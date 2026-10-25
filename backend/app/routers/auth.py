"""
Auth endpoints.

We implement a simple login:
- Input: phone + password
- Output: JWT access_token + user info (including role_name)

This is intentionally minimal for a DB course project.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.schemas.auth import LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with phone & password.
    """
    row = db.execute(
        text("""
            SELECT u.user_id, u.name, u.phone, u.email, u.status, u.password_hash, r.role_name
            FROM users u
            JOIN role r ON r.role_id = u.role_id
            WHERE u.phone = :phone
        """),
        {"phone": payload.phone},
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid phone or password")

    if row["status"] != "active":
        raise HTTPException(status_code=403, detail="User is inactive")

    if not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid phone or password")

    token = create_access_token(subject=str(row["user_id"]))

    user_out = UserOut(
        user_id=row["user_id"],
        name=row["name"],
        phone=row["phone"],
        email=row["email"],
        status=row["status"],
        role_name=row["role_name"],
    )

    return TokenResponse(access_token=token, user=user_out)


@router.get("/me", response_model=UserOut)
def me(current_user: dict = Depends(get_current_user)):
    """
    Return current user info (decoded from JWT + DB check).
    """
    return UserOut(**current_user)
