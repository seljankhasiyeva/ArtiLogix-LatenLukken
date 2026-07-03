from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class VehicleSpec:
    name       : str
    capacity_t : float
    fixed_fee  : float
    var_cost   : float
    toll_fee   : float

VEHICLES: dict[str, VehicleSpec] = {
    "Ford Transit 2t"    : VehicleSpec("Ford Transit 2t",     2.0,  40.0, 0.30, 0.0),
    "Gazelle 3t"         : VehicleSpec("Gazelle 3t",          3.0,  50.0, 0.38, 0.0),
    "Isuzu NPR 5t"       : VehicleSpec("Isuzu NPR 5t",        5.0,  70.0, 0.50, 5.0),
    "Mercedes Atego 10t" : VehicleSpec("Mercedes Atego 10t", 10.0, 110.0, 0.70, 10.0),
    "TIR 20t"            : VehicleSpec("TIR 20t",            20.0, 150.0, 0.95, 20.0),
}

COLD_CHAIN_SURCHARGE = 0.25

DESI_TIERS: list[tuple[float, str]] = [
    (500,  "Ford Transit 2t"),
    (1500, "Gazelle 3t"),
    (4000, "Mercedes Atego 10t"),
    (float("inf"), "TIR 20t"),
]

def select_vehicle(desi: float, cold_chain: bool = False) -> str:
    if desi < 0:
        raise ValueError(f"desi cannot be negative, got {desi}")

    vehicle = next(
        name for threshold, name in DESI_TIERS if desi < threshold
    )

    if cold_chain:
        return f"{vehicle} (refrigerated)"

    return vehicle

@dataclass
class RegionLoad:
    region     : str
    desi       : float
    distance_km: float
    cold_chain : bool = False

@dataclass
class ConsolidationResult:
    consolidated      : bool
    vehicle           : str
    total_desi        : float
    regions_merged    : list[str]
    consolidation_note: str

def consolidate(loads: list[RegionLoad], hub: str) -> list[ConsolidationResult]:
    eligible = [l for l in loads if l.desi < 200]
    other    = [l for l in loads if l.desi >= 200]

    results: list[ConsolidationResult] = []

    if len(eligible) >= 3:
        total_desi   = sum(l.desi for l in eligible)
        merged_regions = [l.region for l in eligible]
        vehicle      = select_vehicle(
            total_desi,
            cold_chain=any(l.cold_chain for l in eligible)
        )
        results.append(ConsolidationResult(
            consolidated=True,
            vehicle=vehicle,
            total_desi=total_desi,
            regions_merged=merged_regions,
            consolidation_note=(
                f"{len(eligible)} regions merged at hub {hub}: "
                f"{', '.join(merged_regions)} "
                f"(each < 200 desi, total = {total_desi:.1f} desi)"
            )
        ))
    else:
        for load in eligible:
            results.append(ConsolidationResult(
                consolidated=False,
                vehicle=select_vehicle(load.desi, cold_chain=load.cold_chain),
                total_desi=load.desi,
                regions_merged=[load.region],
                consolidation_note="No consolidation — fewer than 3 eligible regions."
            ))

    for load in other:
        results.append(ConsolidationResult(
            consolidated=False,
            vehicle=select_vehicle(load.desi, cold_chain=load.cold_chain),
            total_desi=load.desi,
            regions_merged=[load.region],
            consolidation_note=f"{load.region}: {load.desi:.1f} desi >= 200, not eligible for consolidation."
        ))

    return results

def calculate_cost(
    vehicle     : str,
    distance_km : float,
    days        : int   = 1,
    cold_chain  : bool  = False,
) -> float:
    base_name   = vehicle.replace(" (refrigerated)", "").strip()
    is_cold     = cold_chain or "(refrigerated)" in vehicle

    spec = VEHICLES.get(base_name)
    if spec is None:
        raise ValueError(
            f"Unknown vehicle '{vehicle}'. "
            f"Valid options: {list(VEHICLES.keys())}"
        )

    if distance_km < 0:
        raise ValueError(f"distance_km cannot be negative, got {distance_km}")
    if days < 1:
        raise ValueError(f"days must be >= 1, got {days}")

    cost = (spec.fixed_fee * days) + (distance_km * spec.var_cost) + spec.toll_fee

    if is_cold:
        cost *= (1 + COLD_CHAIN_SURCHARGE)

    return round(cost, 2)

def process_dispatch_request(
    desi        : float,
    distance_km : float,
    days        : int  = 1,
    cold_chain  : bool = False,
) -> dict:
    vehicle = select_vehicle(desi, cold_chain=cold_chain)
    cost    = calculate_cost(vehicle, distance_km, days=days, cold_chain=cold_chain)

    return {
        "selected_vehicle" : vehicle,
        "total_cost_azn"   : cost,
        "cold_chain"       : cold_chain,
        "desi"             : desi,
        "distance_km"      : distance_km,
        "days"             : days,
        "status"           : "success",
    }