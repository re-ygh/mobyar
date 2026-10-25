"""
FastAPI dependencies:
- current user resolution from JWT
- role-based access control
"""

from typing import Callable, List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.security import decode_token
from app.core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> dict:
    """
    Resolve the current user from JWT.

    Returns a dict like:
    {
      "user_id": 1,
      "name": "...",
      "phone": "...",
      "email": "...",
      "status": "active",
      "role_name": "admin"
    }
    """
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload["sub"]
    result = db.execute(
        text("""
            SELECT u.user_id, u.name, u.phone, u.email, u.status, r.role_name
            FROM users u
            JOIN role r ON r.role_id = u.role_id
            WHERE u.user_id = :user_id
        """),
        {"user_id": int(user_id)},
    ).mappings().first()

    if not result:
        raise HTTPException(status_code=401, detail="User not found")

    if result["status"] != "active":
        raise HTTPException(status_code=403, detail="User is inactive")

    return dict(result)


def require_roles(allowed_roles: List[str]) -> Callable:
    """
    Dependency factory for role-based access.

    Example:
      @router.post(..., dependencies=[Depends(require_roles(["admin", "staff"]))])
    """
    def _checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role_name"] not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return current_user

    return _checker
