from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth import require_role
from app.services.users_store import create_user, list_users, update_user, delete_user

router = APIRouter()


class UserCreate(BaseModel):
    email: str
    role: Literal["marketplace", "logistics"]


class UserUpdate(BaseModel):
    role: Literal["marketplace", "logistics"] | None = None


def _public_view(user: dict) -> dict:
    return {k: v for k, v in user.items() if k != "password"}


# All endpoints here are admin-only.
@router.post("/users", status_code=status.HTTP_201_CREATED)
def register_user(
    req: UserCreate,
    current_user: dict = Depends(require_role("admin")),
):
    if req.email in [u["email"] for u in list_users()]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )
    record = create_user(email=req.email, role=req.role)
    # The temp password is only ever shown here, once, at creation time —
    # the admin needs it to hand off to the user; every other endpoint
    # strips it out via _public_view.
    return record


@router.get("/users")
def get_users(current_user: dict = Depends(require_role("admin"))):
    return [_public_view(u) for u in list_users()]


@router.patch("/users/{email}")
def edit_user(
    email: str,
    req: UserUpdate,
    current_user: dict = Depends(require_role("admin")),
):
    updated = update_user(email, role=req.role)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _public_view(updated)


@router.delete("/users/{email}", status_code=status.HTTP_204_NO_CONTENT)
def remove_user(
    email: str,
    current_user: dict = Depends(require_role("admin")),
):
    if email == current_user.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot delete their own accounts."
        )
    ok = delete_user(email)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")