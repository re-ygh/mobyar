"""
Service CRUD + price updates.

DB rules (enforced by triggers):
- When service.current_price changes => row inserted into service_price_history
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceOut

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=list[ServiceOut])
def list_services(
    include_inactive: bool = Query(False, description="Include is_active=false services"),
    db: Session = Depends(get_db),
):
    where = "" if include_inactive else "WHERE is_active = TRUE"
    rows = db.execute(
        text(f"""
            SELECT service_id, service_name, description, current_price, is_active
            FROM service
            {where}
            ORDER BY service_id ASC
        """)
    ).mappings().all()
    return [ServiceOut(**dict(r)) for r in rows]


@router.post("", response_model=ServiceOut, dependencies=[Depends(require_roles(["admin", "staff"]))])
def create_service(
    payload: ServiceCreate,
    current_user: dict = Depends(require_roles(["admin", "staff"])),
    db: Session = Depends(get_db),
):
    try:
        row = db.execute(
            text("""
                INSERT INTO service (service_name, description, current_price, is_active, updated_by_user_id)
                VALUES (:service_name, :description, :current_price, :is_active, :updated_by_user_id)
                RETURNING service_id, service_name, description, current_price, is_active
            """),
            {**payload.model_dump(), "updated_by_user_id": current_user["user_id"]},
        ).mappings().first()
        db.commit()
        return ServiceOut(**dict(row))
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid service data") from e


@router.put("/{service_id}", response_model=ServiceOut, dependencies=[Depends(require_roles(["admin", "staff"]))])
def update_service(
    service_id: int,
    payload: ServiceUpdate,
    current_user: dict = Depends(require_roles(["admin", "staff"])),
    db: Session = Depends(get_db),
):
    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")

    data["updated_by_user_id"] = current_user["user_id"]
    data["service_id"] = service_id

    set_clause = ", ".join([f"{k} = :{k}" for k in data.keys() if k != "service_id"])

    try:
        row = db.execute(
            text(f"""
                UPDATE service
                SET {set_clause}
                WHERE service_id = :service_id
                RETURNING service_id, service_name, description, current_price, is_active
            """),
            data,
        ).mappings().first()

        if not row:
            db.rollback()
            raise HTTPException(status_code=404, detail="Service not found")

        db.commit()
        return ServiceOut(**dict(row))
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Update violates constraints") from e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/{service_id}", dependencies=[Depends(require_roles(["admin", "staff"]))])
def deactivate_service(
    service_id: int,
    current_user: dict = Depends(require_roles(["admin", "staff"])),
    db: Session = Depends(get_db),
):
    res = db.execute(
        text("""
            UPDATE service
               SET is_active = FALSE,
                   updated_by_user_id = :uid
             WHERE service_id = :service_id
        """),
        {"uid": current_user["user_id"], "service_id": service_id},
    )
    if res.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=404, detail="Service not found")
    db.commit()
    return {"ok": True}
