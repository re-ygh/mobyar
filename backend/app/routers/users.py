"""
Extra endpoints to help frontend demo (customers & their phones).

Not strictly required by minimum spec, but very useful for UI forms.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.dependencies import require_roles

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/customers", dependencies=[Depends(require_roles(["admin", "staff"]))])
def list_customers(db: Session = Depends(get_db)):
    rows = db.execute(
        text("""
            SELECT u.user_id, u.name, u.phone, u.email, u.status
            FROM users u
            JOIN role r ON r.role_id = u.role_id
            WHERE r.role_name = 'customer'
            ORDER BY u.user_id ASC
        """)
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/customer-phones", dependencies=[Depends(require_roles(["admin", "staff"]))])
def list_customer_phones(
    customer_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    params = {}
    where = ""
    if customer_id:
        where = "WHERE cp.customer_id = :customer_id"
        params["customer_id"] = customer_id

    rows = db.execute(
        text(f"""
            SELECT
              cp.phone_id,
              cp.customer_id,
              cp.imei,
              cp.color,
              pm.model_name,
              b.brand_name
            FROM customer_phone cp
            JOIN phone_model pm ON pm.model_id = cp.model_id
            JOIN brand b ON b.brand_id = pm.brand_id
            {where}
            ORDER BY cp.phone_id ASC
        """),
        params,
    ).mappings().all()
    return [dict(r) for r in rows]
