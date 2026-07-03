import unittest
import sys
from pathlib import Path

current_dir = Path.cwd()
sys.path.append(str(current_dir))

from app.logic.transport_planner import select_vehicle, calculate_cost, process_dispatch_request

class TestTransportPlanner(unittest.TestCase):

    def test_vehicle_bicycle_limits(self):
        self.assertEqual(select_vehicle(2.0, 0.02, "last_mile"), "velosiped")
        self.assertEqual(select_vehicle(5.0, 0.05, "last_mile"), "velosiped")

    def test_vehicle_moped_limits(self):
        self.assertEqual(select_vehicle(6.0, 0.04, "last_mile"), "moped")
        self.assertEqual(select_vehicle(15.0, 0.15, "last_mile"), "moped")
        self.assertEqual(select_vehicle(20.0, 0.20, "last_mile"), "moped")

    def test_vehicle_car_limits(self):
        self.assertEqual(select_vehicle(25.0, 0.3, "last_mile"), "avtomobil")
        self.assertEqual(select_vehicle(200.0, 2.5, "last_mile"), "avtomobil")

    def test_vehicle_tir_by_weight_volume(self):
        self.assertEqual(select_vehicle(550.0, 2.0, "last_mile"), "TIR")
        self.assertEqual(select_vehicle(100.0, 9.0, "last_mile"), "TIR")

    def test_vehicle_tir_by_delivery_type(self):
        self.assertEqual(select_vehicle(10.0, 0.1, "middle_mile"), "TIR")
        self.assertEqual(select_vehicle(5.0, 0.02, "all_mile"), "TIR")

    def test_cost_bicycle_normal(self):
        self.assertEqual(calculate_cost("velosiped", 10.0, 2.0, 0), 7.2)

    def test_cost_bicycle_holiday(self):
        self.assertEqual(calculate_cost("velosiped", 10.0, 2.0, 1), 9.36)

    def test_cost_moped_normal(self):
        self.assertEqual(calculate_cost("moped", 5.0, 10.0, 0), 9.0)

    def test_cost_moped_holiday(self):
        self.assertEqual(calculate_cost("moped", 5.0, 10.0, 1), 11.7)

    def test_cost_car_normal(self):
        self.assertEqual(calculate_cost("avtomobil", 20.0, 50.0, 0), 49.5)

    def test_cost_car_holiday(self):
        self.assertEqual(calculate_cost("avtomobil", 20.0, 50.0, 1), 64.35)

    def test_cost_tir_normal(self):
        self.assertEqual(calculate_cost("tir", 150.0, 600.0, 0), 755.0)

    def test_cost_tir_holiday(self):
        self.assertEqual(calculate_cost("tir", 150.0, 600.0, 1), 981.5)

    def test_cost_invalid_vehicle_fallback(self):
        self.assertEqual(calculate_cost("unregistered_vehicle", 10.0, 10.0, 0), 24.5)

    def test_dispatch_bicycle_flow(self):
        res = process_dispatch_request(2.0, 0.01, "last_mile", 5.0, 0)
        self.assertEqual(res["selected_vehicle"], "velosiped")
        self.assertEqual(res["estimated_cost_azn"], 4.7)

    def test_dispatch_moped_flow(self):
        res = process_dispatch_request(10.0, 0.1, "last_mile", 10.0, 0)
        self.assertEqual(res["selected_vehicle"], "moped")
        self.assertEqual(res["estimated_cost_azn"], 13.0)

    def test_dispatch_car_flow(self):
        res = process_dispatch_request(40.0, 0.5, "last_mile", 15.0, 0)
        self.assertEqual(res["selected_vehicle"], "avtomobil")
        self.assertEqual(res["estimated_cost_azn"], 39.5)

    def test_dispatch_tir_middle_mile_flow(self):
        res = process_dispatch_request(50.0, 0.4, "middle_mile", 100.0, 0)
        self.assertEqual(res["selected_vehicle"], "TIR")
        self.assertEqual(res["estimated_cost_azn"], 502.5)

    def test_dispatch_holiday_handling(self):
        res = process_dispatch_request(5.0, 0.02, "last_mile", 4.0, 1)
        self.assertEqual(res["selected_vehicle"], "velosiped")
        self.assertEqual(res["estimated_cost_azn"], 5.85)

    def test_dispatch_case_insensitive_inputs(self):
        res = process_dispatch_request(10.0, 0.1, "  LAST_MILE  ", 5.0, 0)
        self.assertEqual(res["selected_vehicle"], "moped")

if __name__ == "__main__":
    unittest.main()