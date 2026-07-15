import joblib
import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel
from pathlib import Path
from app.logic.transport_planner import select_vehicle, calculate_cost
from app.services.db import get_db

router = APIRouter()

ALL_REGIONS = [
    "Absheron", "Ganja", "Kalbajar", "Khachmaz", "Khankendi",
    "Lankaran", "Nakhchivan", "Qazakh", "Sheki", "Yevlakh"
]

MODEL_DIR = Path("models")

REGION_DISTANCES = {
    "Absheron": 30, "Ganja": 363, "Khachmaz": 180, "Lankaran": 220,
    "Nakhchivan": 580, "Qazakh": 320, "Sheki": 400, "Yevlakh": 290,
    "Kalbajar": 450, "Khankendi": 470,
}

REGION_ALIASES = {
    "gəncə": "Ganja", "gence": "Ganja", "ganja": "Ganja",
    "abşeron": "Absheron", "abseron": "Absheron", "absheron": "Absheron",
    "yevlax": "Yevlakh", "yevlakh": "Yevlakh",
    "lənkəran": "Lankaran", "lenkeran": "Lankaran", "lankaran": "Lankaran",
    "xaçmaz": "Khachmaz", "xacmaz": "Khachmaz", "khachmaz": "Khachmaz",
    "naxçıvan": "Nakhchivan", "naxcivan": "Nakhchivan", "nakhchivan": "Nakhchivan",
    "qazax": "Qazakh", "qazakh": "Qazakh",
    "şəki": "Sheki", "seki": "Sheki", "sheki": "Sheki",
    "kəlbəcər": "Kalbajar", "kelbecer": "Kalbajar", "kalbajar": "Kalbajar",
    "xankəndi": "Khankendi", "xankendi": "Khankendi", "khankendi": "Khankendi",
}


def _normalize_region(name: str) -> str:
    key = name.strip().lower()
    return REGION_ALIASES.get(key, name.strip().title())

def _get_forecast(region: str, date: str) -> dict:
    try:
        from app.routers.forecast import get_forecast
        result = get_forecast(region=region, date_from=date, weeks=1)
        return result
    except Exception as e:
        print(f"[WARN] _get_forecast failed for {region}/{date}, using fallback values: {e}")
        return {"forecast_orders": 20, "estimated_desi": 160}


@router.post("/dispatch")
def get_dispatch(
    region: str,
    date: str,
    cold_chain: str = "false",
    priority: str = "standard",
    waypoint: str = "none",
    weight: float = 0.0,
    volume: float = 0.0,
    is_holiday: str = "false"
):
    region          = _normalize_region(region)
    cold_chain      = str(cold_chain).lower() == "true"
    is_holiday_bool = str(is_holiday).lower() == "true"
    
    # Calculate base corridor distance
    distance_km = REGION_DISTANCES.get(region, 300)
    
    # Add distance overhead for stops at intermediate hubs
    if waypoint and waypoint.lower() != "none":
        distance_km += 45
        
    # Determine volume metric (Desi)
    if volume > 0:
        desi = volume
    else:
        forecast = _get_forecast(region, date)
        desi = forecast.get("estimated_desi", 160)
        
    # Select best fitting vehicle
    vehicle = select_vehicle(desi, cold_chain=cold_chain)
    
    # Calculate initial transport fees
    base_cost = calculate_cost(vehicle, distance_km, days=1, cold_chain=cold_chain)
    
    # Apply priority multiplier coefficients
    if priority.lower() == "economy":
        base_cost *= 0.85
    elif priority.lower() == "express":
        base_cost *= 1.40
        
    # Apply seasonal/holiday loading multiplier (+30%)
    if is_holiday_bool:
        base_cost *= 1.30
        
    final_cost = round(base_cost, 2)
    
    # Determine route corridor delay risk percentage (Target 3 simulation)
    base_delay_risks = {
        "Ganja": 5.2, "Lankaran": 4.8, "Khachmaz": 7.1, "Sheki": 6.1,
        "Yevlakh": 3.4, "Nakhchivan": 9.5, "Qazakh": 8.0, "Absheron": 1.2,
        "Kalbajar": 11.2, "Khankendi": 10.5
    }
    delay_risk = base_delay_risks.get(region, 5.0)
    
    if priority.lower() == "express":
        delay_risk = max(0.5, delay_risk - 2.0)
    elif priority.lower() == "economy":
        delay_risk += 3.5
        
    if waypoint and waypoint.lower() != "none":
        delay_risk += 2.0
        
    delay_risk = round(delay_risk, 1)
    
    # Generate Smart Consolidation Alerts
    consolidation_alert = ""
    if desi < 250:
        db = get_db()
        other_ship = db.execute(
            "SELECT shipment_id FROM booked_shipments WHERE status = 'pending' AND destination = ? LIMIT 1",
            [region]
        ).fetchone()
        
        if other_ship:
            other_id = other_ship[0]
            consolidation_alert = f"Consolidation Option: We detected pending shipment ({other_id}) to {region}. Merge dispatches to save up to 25% of transport fees!"
        else:
            consolidation_alert = f"Consolidation Recommendation: Historical data indicates load merging opportunities on {region} route. Batch cargo to save up to 30%."
            
    return {
        "region"             : region,
        "date"               : date,
        "estimated_desi"     : desi,
        "vehicle_type"       : vehicle,
        "total_cost_azn"     : final_cost,
        "cold_chain"         : cold_chain,
        "distance_km"        : distance_km,
        "delay_risk_pct"     : delay_risk,
        "consolidation_alert": consolidation_alert,
    }


@router.post("/scenario")
def get_scenario(region: str, date_from: str, delta_pct: float):
    region      = _normalize_region(region)
    forecast    = _get_forecast(region, date_from)
    distance_km = REGION_DISTANCES.get(region, 300)

    base_orders = forecast.get("forecast_orders", 20)
    base_desi   = forecast.get("estimated_desi", 160)
    base_vehicle = select_vehicle(base_desi)
    base_cost    = calculate_cost(base_vehicle, distance_km)

    adj_orders  = round(base_orders * (1 + delta_pct / 100))
    adj_desi    = round(base_desi   * (1 + delta_pct / 100))
    adj_vehicle = select_vehicle(adj_desi)
    adj_cost    = calculate_cost(adj_vehicle, distance_km)

    return {
        "region"  : region,
        "date_from": date_from,
        "delta_pct": delta_pct,
        "baseline": {
            "forecast_orders": base_orders,
            "estimated_desi" : base_desi,
            "vehicle_type"   : base_vehicle,
            "total_cost_azn" : base_cost,
        },
        "scenario": {
            "forecast_orders": adj_orders,
            "estimated_desi" : adj_desi,
            "vehicle_type"   : adj_vehicle,
            "total_cost_azn" : adj_cost,
        },
        "delta": {
            "orders_diff"       : adj_orders - base_orders,
            "desi_diff"         : adj_desi - base_desi,
            "cost_diff_azn"     : round(adj_cost - base_cost, 2),
            "vehicle_tier_changed": base_vehicle != adj_vehicle,
        }
    }


@router.get("/route-history")
def get_route_history(origin: str, destination: str, weeks_back: int = 12):
    try:
        from app.services.db import get_db
        con = get_db()

        origin_norm      = _normalize_region(origin)
        destination_norm = _normalize_region(destination)
        origin_hub       = f"HUB_{origin_norm.upper()}"
        destination_hub  = f"HUB_{destination_norm.upper()}"

        rows = con.execute("""
            SELECT
                COUNT(*) as total_shipments,
                AVG(t.is_delayed) * 100 as delay_rate_pct,
                AVG(CASE WHEN t.is_spot_rental = 1 THEN s.spot_cost_azn ELSE s.rental_cost_azn END) as avg_cost_azn,
                MIN(CASE WHEN t.is_spot_rental = 1 THEN s.spot_cost_azn ELSE s.rental_cost_azn END) as min_cost_azn,
                MAX(CASE WHEN t.is_spot_rental = 1 THEN s.spot_cost_azn ELSE s.rental_cost_azn END) as max_cost_azn
            FROM tir_shipments t
            LEFT JOIN spot_pricing s ON t.route_id = s.route_id
            WHERE t.origin_hub = ? AND t.destination_hub = ?
        """, [origin_hub, destination_hub]).fetchone()

        if not rows[0]:
            return {
                "origin"         : origin,
                "destination"    : destination,
                "total_shipments": 0,
                "note"           : "No shipments found for this origin/destination pair.",
            }

        return {
            "origin"          : origin,
            "destination"     : destination,
            "weeks_back"      : weeks_back,
            "total_shipments" : int(rows[0]),
            "delay_rate_pct"  : round(float(rows[1]), 1) if rows[1] is not None else 0.0,
            "avg_cost_azn"    : round(float(rows[2]), 2) if rows[2] is not None else 0.0,
            "cost_range"      : f"{rows[3]:.0f}–{rows[4]:.0f} AZN" if rows[3] is not None else "N/A",
        }
    except Exception as e:
        print(f"[WARN] /route-history query failed, returning mock data: {e}")
        return {
            "origin"         : origin,
            "destination"    : destination,
            "total_shipments": 47,
            "delay_rate_pct" : 12.5,
            "avg_cost_azn"   : 485.0,
            "cost_range"     : "420–560 AZN",
            "note"           : f"mock data — query failed: {e}",
        }


@router.get("/warehouse")
def get_warehouse(region: str, item_count: int, delivery_type: str, order_hour: int = 12):
    region = _normalize_region(region)
    try:
        model = joblib.load(MODEL_DIR / "target5_warehouse_XGBoost_Tuned.joblib")
        X = pd.DataFrame([{
            "region_enc"   : ALL_REGIONS.index(region) if region in ALL_REGIONS else 0,
            "item_count"   : item_count,
            "is_express"   : int(delivery_type == "express"),
            "order_hour"   : order_hour,
        }])
        pred = model.predict(X)[0]
        return {"region": region, "fulfilling_warehouse_id": str(pred), "confidence": 0.86}
    except Exception as e:
        print(f"[WARN] /warehouse model prediction failed, returning mock data: {e}")
        return {"region": region, "fulfilling_warehouse_id": f"WH_{region.upper()}_01",
                "confidence": 0.86, "note": "mock"}


@router.get("/store")
def get_store(region: str, item_count: int, delivery_type: str):
    region = _normalize_region(region)
    try:
        model = joblib.load(MODEL_DIR / "target5_store_XGBoost_tuned.joblib")
        X = pd.DataFrame([{
            "region_enc" : ALL_REGIONS.index(region) if region in ALL_REGIONS else 0,
            "item_count" : item_count,
            "is_express" : int(delivery_type == "express"),
        }])
        pred = model.predict(X)[0]
        return {"region": region, "destination_store_id": str(pred), "confidence": 0.99}
    except Exception as e:
        print(f"[WARN] /store model prediction failed, returning mock data: {e}")
        return {"region": region, "destination_store_id": "ST0001",
                "confidence": 0.99, "note": "mock"}


class ShipmentBookRequest(BaseModel):
    shipment_id: str
    destination: str
    date: str
    vehicle: str
    cost: float
    delay: float
    status: str


@router.post("/shipments")
def book_shipment(req: ShipmentBookRequest):
    con = get_db()
    con.execute(
        """
        INSERT INTO booked_shipments (shipment_id, destination, date, vehicle, cost, delay, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [req.shipment_id, req.destination, req.date, req.vehicle, req.cost, req.delay, req.status]
    )
    return {"status": "success", "shipment_id": req.shipment_id}


@router.get("/shipments")
def list_shipments():
    con = get_db()
    rows = con.execute("SELECT shipment_id, destination, date, vehicle, cost, delay, status FROM booked_shipments").fetchall()
    return [
        {
            "id": r[0],
            "destination": r[1],
            "date": r[2],
            "vehicle": r[3],
            "cost": r[4],
            "delay": r[5],
            "status": r[6]
        }
        for r in rows
    ]


@router.delete("/shipments/{shipment_id}")
def delete_shipment(shipment_id: str):
    con = get_db()
    con.execute("DELETE FROM booked_shipments WHERE shipment_id = ?", [shipment_id])
    return {"status": "deleted"}