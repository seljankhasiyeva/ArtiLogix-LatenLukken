from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends
from pydantic import BaseModel
from app.auth import create_access_token, DEMO_USERS, verify_token
from app.services.drivers_store import get_driver, check_password as check_driver_password
from app.services.users_store import (
    get_user as get_dynamic_user,
    check_password as check_dynamic_password,
    set_password as set_dynamic_password,
)

router = APIRouter()


@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Normalize and clean username
    username_cleaned = form_data.username.strip()
    if username_cleaned.upper().startswith("DRV"):
        username_cleaned = username_cleaned.replace(" ", "").upper()

    # 1. Fixed demo accounts (marketplace/logistics/admin).
    user = DEMO_USERS.get(username_cleaned)
    if user and user["password"] == form_data.password:
        token = create_access_token(
            data={"sub": username_cleaned, "role": user["role"]}
        )
        return {
            "access_token": token, "token_type": "bearer",
            "role": user["role"], "must_change_password": False,
        }

    # 2. Admin-created marketplace/logistics users (temp password until
    # they set their own — see must_change_password).
    dyn_user = get_dynamic_user(username_cleaned)
    if dyn_user and check_dynamic_password(username_cleaned, form_data.password):
        token = create_access_token(
            data={"sub": username_cleaned, "role": dyn_user["role"]}
        )
        return {
            "access_token": token, "token_type": "bearer",
            "role": dyn_user["role"],
            "must_change_password": dyn_user["must_change_password"],
        }

    # 3. Drivers: registered by a logistics admin (POST /api/drivers) with
    # a generated driver_id and a password chosen at registration time.
    driver = get_driver(username_cleaned)
    if driver and check_driver_password(username_cleaned, form_data.password):
        token = create_access_token(
            data={"sub": driver["driver_id"], "role": "driver"}
        )
        return {
            "access_token": token, "token_type": "bearer",
            "role": "driver", "must_change_password": False,
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password"
    )


class ChangePasswordRequest(BaseModel):
    new_password: str


@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    current_user: dict = Depends(verify_token),
):
    """Allows dynamic users and drivers to set their own password."""
    if len(req.new_password) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 4 characters",
        )
        
    if current_user["role"] == "driver":
        from app.services.drivers_store import update_driver_password
        ok = update_driver_password(current_user["email"], req.new_password)
    else:
        ok = set_dynamic_password(current_user["email"], req.new_password)
        
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This account doesn't support self-service password changes",
        )
    return {"status": "password updated"}