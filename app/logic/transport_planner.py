import pandas as pd
import numpy as np
from pathlib import Path

def select_vehicle(weight: float, volume: float, delivery_type: str) -> str:
    delivery_type = delivery_type.lower().strip()
    
    if delivery_type in ["middle_mile", "all_mile"] or weight > 500.0 or volume > 8.0:
        return "TIR"
        
    if delivery_type == "last_mile":
        if weight <= 5.0 and volume <= 0.05:
            return "velosiped"
        elif weight <= 20.0 and volume <= 0.2:
            return "moped"
        else:
            return "avtomobil"
            
    return "avtomobil"

def calculate_cost(vehicle_type: str, distance_km: float, weight: float, is_holiday: int) -> float:
    vehicle_type = vehicle_type.lower().strip()
    
    base_rates = {
        "velosiped": {"base": 2.0, "per_km": 0.5, "per_kg": 0.1},
        "moped": {"base": 3.5, "per_km": 0.8, "per_kg": 0.15},
        "avtomobil": {"base": 7.0, "per_km": 1.5, "per_kg": 0.25},
        "tir": {"base": 50.0, "per_km": 4.5, "per_kg": 0.05}
    }
    
    rates = base_rates.get(vehicle_type, base_rates["avtomobil"])
    cost = rates["base"] + (distance_km * rates["per_km"]) + (weight * rates["per_kg"])
    
    if is_holiday == 1:
        cost *= 1.3
        
    return round(cost, 2)

def process_dispatch_request(weight: float, volume: float, delivery_type: str, distance_km: float, is_holiday: int) -> dict:
    vehicle = select_vehicle(weight, volume, delivery_type)
    cost = calculate_cost(vehicle, distance_km, weight, is_holiday)
    
    return {
        "selected_vehicle": vehicle,
        "estimated_cost_azn": cost,
        "status": "success"
    }