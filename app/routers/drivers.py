from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth import verify_token, require_role
from app.services.drivers_store import create_driver, get_driver, list_drivers

router = APIRouter()


class DriverCreate(BaseModel):
    name: str
    phone: str
    vehicle_type: str
    vehicle_number: str
    password: str


def _public_view(driver: dict) -> dict:
    """Strips the password out before sending the record back — the
    admin doesn't need to see it in the list/response after creation,
    and the driver already knows the password they registered with."""
    return {k: v for k, v in driver.items() if k != "password"}


# Only a logged-in logistics admin can register or list drivers.
@router.post("/drivers", status_code=status.HTTP_201_CREATED)
def register_driver(
    req: DriverCreate,
    current_user: dict = Depends(require_role("logistics")),
):
    if len(req.password) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 4 characters",
        )
    record = create_driver(
        name=req.name,
        phone=req.phone,
        vehicle_type=req.vehicle_type,
        vehicle_number=req.vehicle_number,
        password=req.password,
    )
    return _public_view(record)


@router.get("/drivers")
def get_drivers(
    current_user: dict = Depends(require_role("logistics")),
):
    return [_public_view(d) for d in list_drivers()]


# A driver reading their own profile — any logged-in driver, not admin-only.
@router.get("/drivers/me")
def get_my_profile(current_user: dict = Depends(verify_token)):
    if current_user["role"] != "driver":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only drivers can access this endpoint",
        )
    driver = get_driver(current_user["email"])
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return _public_view(driver)
