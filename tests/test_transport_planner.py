import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.logic.transport_planner import (
    select_vehicle, calculate_cost, consolidate,
    process_dispatch_request, RegionLoad, VEHICLES
)


class TestSelectVehicle(unittest.TestCase):

    def test_tier1_below_500(self):
        self.assertEqual(select_vehicle(0),     "Ford Transit 2t")
        self.assertEqual(select_vehicle(499.9), "Ford Transit 2t")

    def test_tier2_500_to_1500(self):
        self.assertEqual(select_vehicle(500),    "Gazelle 3t")
        self.assertEqual(select_vehicle(1499.9), "Gazelle 3t")

    def test_tier3_1500_to_4000(self):
        self.assertEqual(select_vehicle(1500),   "Mercedes Atego 10t")
        self.assertEqual(select_vehicle(3999.9), "Mercedes Atego 10t")

    def test_tier4_above_4000(self):
        self.assertEqual(select_vehicle(4000),   "TIR 20t")
        self.assertEqual(select_vehicle(99999),  "TIR 20t")

    def test_cold_chain_tier1(self):
        self.assertEqual(
            select_vehicle(200, cold_chain=True),
            "Ford Transit 2t (refrigerated)"
        )

    def test_cold_chain_tier4(self):
        self.assertEqual(
            select_vehicle(5000, cold_chain=True),
            "TIR 20t (refrigerated)"
        )

    def test_negative_desi_raises(self):
        with self.assertRaises(ValueError):
            select_vehicle(-1)


class TestCalculateCost(unittest.TestCase):

    def test_transit_basic(self):
        self.assertEqual(calculate_cost("Ford Transit 2t", 100), 70.00)

    def test_transit_multi_day(self):
        self.assertEqual(calculate_cost("Ford Transit 2t", 100, days=2), 110.00)

    def test_tir_basic(self):
        self.assertEqual(calculate_cost("TIR 20t", 363), 514.85)

    def test_tir_cold_chain(self):
        self.assertEqual(calculate_cost("TIR 20t", 363, cold_chain=True), 643.56)

    def test_atego_basic(self):
        self.assertEqual(calculate_cost("Mercedes Atego 10t", 200), 260.00)

    def test_cold_chain_via_name(self):
        cost_normal = calculate_cost("Gazelle 3t", 100)
        cost_cold   = calculate_cost("Gazelle 3t (refrigerated)", 100)
        self.assertAlmostEqual(cost_cold, cost_normal * 1.25, places=2)

    def test_invalid_vehicle_raises(self):
        with self.assertRaises(ValueError):
            calculate_cost("unknown_truck", 100)

    def test_negative_distance_raises(self):
        with self.assertRaises(ValueError):
            calculate_cost("Ford Transit 2t", -10)

    def test_zero_days_raises(self):
        with self.assertRaises(ValueError):
            calculate_cost("Ford Transit 2t", 100, days=0)


class TestConsolidate(unittest.TestCase):

    def _make_loads(self, desi_list, cold=False):
        return [
            RegionLoad(region=f"R{i+1}", desi=d, distance_km=100, cold_chain=cold)
            for i, d in enumerate(desi_list)
        ]

    def test_consolidation_triggers_at_3(self):
        loads   = self._make_loads([100, 150, 180])
        results = consolidate(loads, hub="Absheron")
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].consolidated)
        self.assertEqual(results[0].total_desi, 430)
        self.assertEqual(set(results[0].regions_merged), {"R1", "R2", "R3"})

    def test_consolidation_skips_at_2(self):
        loads   = self._make_loads([100, 150])
        results = consolidate(loads, hub="Ganja")
        self.assertEqual(len(results), 2)
        self.assertFalse(any(r.consolidated for r in results))

    def test_consolidation_excludes_large_loads(self):
        loads = [
            RegionLoad("R1", 100,  100),
            RegionLoad("R2", 150,  100),
            RegionLoad("R3", 250,  100),
            RegionLoad("R4", 180,  100),
        ]
        results = consolidate(loads, hub="Yevlakh")
        self.assertEqual(len(results), 2)
        merged = next(r for r in results if r.consolidated)
        self.assertAlmostEqual(merged.total_desi, 430, places=1)
        separate = next(r for r in results if not r.consolidated)
        self.assertEqual(separate.regions_merged, ["R3"])

    def test_cold_chain_propagates_in_consolidation(self):
        loads = [
            RegionLoad("R1", 100, 100, cold_chain=True),
            RegionLoad("R2", 150, 100, cold_chain=False),
            RegionLoad("R3", 120, 100, cold_chain=False),
        ]
        results = consolidate(loads, hub="Lankaran")
        self.assertTrue(results[0].consolidated)
        self.assertIn("refrigerated", results[0].vehicle)


class TestProcessDispatch(unittest.TestCase):

    def test_dispatch_returns_correct_keys(self):
        res = process_dispatch_request(300, 150)
        self.assertIn("selected_vehicle", res)
        self.assertIn("total_cost_azn", res)
        self.assertIn("status", res)
        self.assertEqual(res["status"], "success")

    def test_dispatch_tier1_no_cold(self):
        res = process_dispatch_request(200, 100)
        self.assertEqual(res["selected_vehicle"], "Ford Transit 2t")
        self.assertEqual(res["total_cost_azn"], 70.00)

    def test_dispatch_cold_chain_flag(self):
        res_normal = process_dispatch_request(200, 100, cold_chain=False)
        res_cold   = process_dispatch_request(200, 100, cold_chain=True)
        self.assertAlmostEqual(
            res_cold["total_cost_azn"],
            res_normal["total_cost_azn"] * 1.25,
            places=2
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)