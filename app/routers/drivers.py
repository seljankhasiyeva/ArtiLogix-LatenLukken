from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth import verify_token, require_role
from app.services.drivers_store import create_driver, get_driver, list_drivers, update_driver, delete_driver

router = APIRouter()


class DriverCreate(BaseModel):
    name: str
    phone: str
    vehicle_type: str
    vehicle_number: str
    password: str


class DriverUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    vehicle_type: str | None = None
    vehicle_number: str | None = None
    status: str | None = None


class DriverProfileUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    vehicle_type: str | None = None
    vehicle_number: str | None = None


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
    
    from app.services.db import get_db
    con = get_db()
    
    # Find active shipment assigned to this driver
    shipment_row = con.execute(
        "SELECT shipment_id, destination, date, vehicle, cost, delay, status FROM booked_shipments WHERE driver_id = ? AND status != 'delivered'",
        [driver["driver_id"]]
    ).fetchone()
    
    # If no shipment is assigned, grab the first pending shipment and assign it
    if not shipment_row:
        pending_shipment = con.execute(
            "SELECT shipment_id, destination, date, vehicle, cost, delay, status FROM booked_shipments WHERE driver_id IS NULL AND status = 'pending' ORDER BY date ASC"
        ).fetchone()
        if pending_shipment:
            con.execute(
                "UPDATE booked_shipments SET driver_id = ? WHERE shipment_id = ?",
                [driver["driver_id"], pending_shipment[0]]
            )
            shipment_row = pending_shipment
            
    shipment_data = None
    if shipment_row:
        shipment_data = {
            "shipment_id": shipment_row[0],
            "destination": shipment_row[1],
            "date": shipment_row[2],
            "vehicle": shipment_row[3],
            "cost": shipment_row[4],
            "delay": shipment_row[5],
            "status": shipment_row[6]
        }
        
    resp = _public_view(driver)
    resp["active_shipment"] = shipment_data
    return resp


@router.patch("/drivers/me")
def update_my_profile(
    req: DriverProfileUpdate,
    current_user: dict = Depends(verify_token),
):
    if current_user["role"] != "driver":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only drivers can update their profile information",
        )
    driver_id = current_user["email"]
    
    payload = {}
    if req.name is not None:
        payload["name"] = req.name
    if req.phone is not None:
        payload["phone"] = req.phone
    if req.vehicle_type is not None:
        payload["vehicle_type"] = req.vehicle_type
    if req.vehicle_number is not None:
        payload["vehicle_number"] = req.vehicle_number
        
    updated = update_driver(driver_id, **payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return _public_view(updated)


# Admin-only: edit or remove a driver.
@router.patch("/drivers/{driver_id}")
def edit_driver(
    driver_id: str,
    req: DriverUpdate,
    current_user: dict = Depends(require_role("logistics")),
):
    updated = update_driver(
        driver_id,
        name=req.name,
        phone=req.phone,
        vehicle_type=req.vehicle_type,
        vehicle_number=req.vehicle_number,
        status=req.status,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return _public_view(updated)


@router.delete("/drivers/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_driver(
    driver_id: str,
    current_user: dict = Depends(require_role("logistics")),
):
    ok = delete_driver(driver_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")


class DriverProgressUpdate(BaseModel):
    status: str | None = None
    current_checkpoint: str | None = None
    last_checkpoint_time: str | None = None


@router.patch("/drivers/me/progress")
def update_my_progress(
    req: DriverProgressUpdate,
    current_user: dict = Depends(verify_token),
):
    if current_user["role"] != "driver":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only drivers can update progress",
        )
    driver_id = current_user["email"]
    updated = update_driver(
        driver_id,
        status=req.status,
        current_checkpoint=req.current_checkpoint,
        last_checkpoint_time=req.last_checkpoint_time,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
        
    # Also update the active shipment's status in DuckDB!
    from app.services.db import get_db
    con = get_db()
    if req.status == "In-Transit":
        con.execute(
            "UPDATE booked_shipments SET status = 'in-transit' WHERE driver_id = ? AND status != 'delivered'",
            [driver_id]
        )
    elif req.status == "Completed":
        con.execute(
            "UPDATE booked_shipments SET status = 'delivered' WHERE driver_id = ? AND status != 'delivered'",
            [driver_id]
        )
        
    return _public_view(updated)