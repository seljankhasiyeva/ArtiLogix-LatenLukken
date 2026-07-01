from fastapi import APIRouter

router = APIRouter()


@router.get("/dispatch")
def get_dispatch(region: str, date: str = None):
    return {"status": "stub", "region": region, "date": date}


@router.get("/load")
def get_load(region: str, date: str = None):
    return {"status": "stub", "region": region, "date": date}


@router.get("/cost")
def get_cost(vehicle_type: str, distance_km: float, days: int = 1):
    return {"status": "stub", "vehicle_type": vehicle_type, "distance_km": distance_km}