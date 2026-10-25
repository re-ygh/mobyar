"""
Repairs workflow.

DB rules:
- price_at_time is copied from service.current_price at INSERT (trigger)
- phone must belong to the customer (trigger)
- customer/phone/service are immutable after creation (trigger)
- after delivered/cancelled, status cannot change (trigger)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.schemas.repairs import RepairCreate, RepairStatusUpdate, RepairOut

router = APIRouter(prefix="/repairs", tags=["repairs"])


@router.post("", response_model=RepairOut, dependencies=[Depends(require_roles(["admin", "staff"]))])
def create_repair(
    payload: RepairCreate,
    current_user: dict = Depends(require_roles(["admin", "staff"])),
    db: Session = Depends(get_db),
):
    try:
        row = db.execute(
            text("""
                INSERT INTO repair_order (customer_id, phone_id, service_id, created_by_user_id, notes)
                VALUES (:customer_id, :phone_id, :service_id, :created_by_user_id, :notes)
                RETURNING repair_id, customer_id, phone_id, service_id, price_at_time, status, created_by_user_id, notes, created_at, updated_at
            """),
            {
                **payload.model_dump(),
                "created_by_user_id": current_user["user_id"],
            },
        ).mappings().first()
        db.commit()
        return RepairOut(**dict(row))
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid repair data") from e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("", response_model=list[RepairOut], dependencies=[Depends(require_roles(["admin", "staff"]))])
def list_repairs(
    status_filter: str | None = Query(None, description="pending | in_progress | ready | delivered | cancelled"),
    db: Session = Depends(get_db),
):
    where = ""
    params = {}
    if status_filter:
        where = "WHERE status = :status"
        params["status"] = status_filter

    rows = db.execute(
        text(f"""
            SELECT repair_id, customer_id, phone_id, service_id, price_at_time, status,
                   created_by_user_id, notes, created_at, updated_at
            FROM repair_order
            {where}
            ORDER BY repair_id DESC
            LIMIT 100
        """),
        params,
    ).mappings().all()
    return [RepairOut(**dict(r)) for r in rows]


@router.get("/{repair_id}", response_model=RepairOut, dependencies=[Depends(require_roles(["admin", "staff"]))])
def get_repair(repair_id: int, db: Session = Depends(get_db)):
    row = db.execute(
        text("""
            SELECT repair_id, customer_id, phone_id, service_id, price_at_time, status,
                   created_by_user_id, notes, created_at, updated_at
            FROM repair_order
            WHERE repair_id = :repair_id
        """),
        {"repair_id": repair_id},
    ).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Repair order not found")

    return RepairOut(**dict(row))


@router.patch("/{repair_id}/status", response_model=RepairOut, dependencies=[Depends(require_roles(["admin", "staff"]))])
def update_repair_status(
    repair_id: int,
    payload: RepairStatusUpdate,
    db: Session = Depends(get_db),
):
    try:
        row = db.execute(
            text("""
                UPDATE repair_order
                SET status = :status
                WHERE repair_id = :repair_id
                RETURNING repair_id, customer_id, phone_id, service_id, price_at_time, status,
                          created_by_user_id, notes, created_at, updated_at
            """),
            {"status": payload.status, "repair_id": repair_id},
        ).mappings().first()

        if not row:
            db.rollback()
            raise HTTPException(status_code=404, detail="Repair order not found")

        db.commit()
        return RepairOut(**dict(row))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from e
