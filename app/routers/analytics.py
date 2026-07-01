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
def get_regional_demand(region: str):
    return {"status": "stub", "region": region}


@router.get("/delay-rate")
def get_delay_rate():
    return {"status": "stub"}


@router.get("/vehicle-usage")
def get_vehicle_usage():
    return {"status": "stub"}


@router.get("/top-routes")
def get_top_routes():
    return {"status": "stub"}