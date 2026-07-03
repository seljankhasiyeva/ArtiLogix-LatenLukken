from fastapi import APIRouter

router = APIRouter()


@router.get("/forecast")
def get_forecast(region: str, date_from: str = None):
    return {"status": "stub", "region": region, "date_from": date_from}