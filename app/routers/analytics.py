from fastapi import APIRouter
from app.services.db import get_db

router = APIRouter()


@router.get("/regions")
def get_regions():
    con = get_db()
    regions = con.execute(
        "SELECT DISTINCT region FROM weekly_orders_by_region ORDER BY 1"
    ).fetchall()
    return {"regions": [r[0] for r in regions]}


@router.get("/regional-demand")
def get_regional_demand(region: str = None):
    con = get_db()
    if region:
        rows = con.execute("""
            SELECT week, region, order_count
            FROM regional_demand_trend
            WHERE region = ?
            ORDER BY week
        """, [region]).fetchall()
    else:
        rows = con.execute("""
            SELECT week, region, order_count
            FROM regional_demand_trend
            ORDER BY week, region
        """).fetchall()
    return {"data": [{"week": str(r[0]), "region": r[1], "order_count": r[2]} for r in rows]}


@router.get("/delay-rate")
def get_delay_rate():
    con = get_db()
    rows = con.execute("""
        SELECT origin_hub, destination_hub, total_shipments,
               delayed_shipments, delay_rate_pct
        FROM delay_rate_by_route
        ORDER BY delay_rate_pct DESC
    """).fetchall()
    return {"data": [{"origin": r[0], "destination": r[1],
                      "total": r[2], "delayed": r[3], "delay_rate_pct": r[4]}
                     for r in rows]}


@router.get("/vehicle-usage")
def get_vehicle_usage():
    con = get_db()
    rows = con.execute("""
        SELECT capacity_ton, shipment_count, avg_utilization_pct
        FROM vehicle_usage_distribution
    """).fetchall()
    return {"data": [{"capacity_ton": r[0], "shipment_count": r[1],
                      "avg_utilization_pct": r[2]} for r in rows]}


@router.get("/top-routes")
def get_top_routes():
    con = get_db()
    rows = con.execute("""
        SELECT origin_hub, destination_hub, avg_cost_azn, shipment_count
        FROM top_routes_by_cost
    """).fetchall()
    return {"data": [{"origin": r[0], "destination": r[1],
                      "avg_cost_azn": r[2], "shipment_count": r[3]}
                     for r in rows]}

