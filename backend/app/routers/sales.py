"""
Sales workflow endpoints.

Key design:
- A sale starts as 'draft'
- Items can be added/updated only while draft (enforced by DB triggers)
- When finalizing, DB trigger deducts stock and prevents negative stock

Why DB-level rules? So even if someone bypasses the API, the database remains consistent.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.schemas.sales import (
    SaleCreate, SaleOut, SaleItemAdd, SaleDetailOut, SaleItemOut
)

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("", response_model=SaleOut, dependencies=[Depends(require_roles(["admin", "staff"]))])
def create_sale(
    payload: SaleCreate,
    current_user: dict = Depends(require_roles(["admin", "staff"])),
    db: Session = Depends(get_db),
):
    row = db.execute(
        text("""
            INSERT INTO sale (customer_id, created_by_user_id, status)
            VALUES (:customer_id, :created_by_user_id, 'draft')
            RETURNING sale_id, customer_id, created_by_user_id, sale_date, status, total_price, finalized_at
        """),
        {"customer_id": payload.customer_id, "created_by_user_id": current_user["user_id"]},
    ).mappings().first()
    db.commit()
    return SaleOut(**dict(row))


@router.get("", response_model=list[SaleOut], dependencies=[Depends(require_roles(["admin", "staff"]))])
def list_sales(
    status_filter: str | None = Query(None, description="draft | finalized | void"),
    db: Session = Depends(get_db),
):
    where = ""
    params = {}
    if status_filter:
        where = "WHERE status = :status"
        params["status"] = status_filter

    rows = db.execute(
        text(f"""
            SELECT sale_id, customer_id, created_by_user_id, sale_date, status, total_price, finalized_at
            FROM sale
            {where}
            ORDER BY sale_id DESC
            LIMIT 100
        """),
        params,
    ).mappings().all()
    return [SaleOut(**dict(r)) for r in rows]


@router.get("/{sale_id}", response_model=SaleDetailOut, dependencies=[Depends(require_roles(["admin", "staff"]))])
def get_sale_detail(sale_id: int, db: Session = Depends(get_db)):
    sale_row = db.execute(
        text("""
            SELECT sale_id, customer_id, created_by_user_id, sale_date, status, total_price, finalized_at
            FROM sale
            WHERE sale_id = :sale_id
        """),
        {"sale_id": sale_id},
    ).mappings().first()

    if not sale_row:
        raise HTTPException(status_code=404, detail="Sale not found")

    item_rows = db.execute(
        text("""
            SELECT
              si.sale_item_id,
              si.product_id,
              p.name AS product_name,
              si.quantity,
              si.price_at_time,
              (si.quantity * si.price_at_time) AS line_total
            FROM sale_item si
            JOIN product p ON p.product_id = si.product_id
            WHERE si.sale_id = :sale_id
            ORDER BY si.sale_item_id ASC
        """),
        {"sale_id": sale_id},
    ).mappings().all()

    return SaleDetailOut(
        sale=SaleOut(**dict(sale_row)),
        items=[SaleItemOut(**dict(r)) for r in item_rows],
    )


@router.post("/{sale_id}/items", response_model=SaleDetailOut, dependencies=[Depends(require_roles(["admin", "staff"]))])
def add_item(
    sale_id: int,
    payload: SaleItemAdd,
    db: Session = Depends(get_db),
):
    """
    Add an item to a sale (UPSERT).
    - If the product already exists in this sale, we increase quantity.
    - price_at_time is set by DB trigger (snapshot).
    """
    try:
        db.execute(
            text("""
                INSERT INTO sale_item (sale_id, product_id, quantity, price_at_time)
                VALUES (:sale_id, :product_id, :quantity, 0)
                ON CONFLICT (sale_id, product_id)
                DO UPDATE SET quantity = sale_item.quantity + EXCLUDED.quantity
            """),
            {"sale_id": sale_id, "product_id": payload.product_id, "quantity": payload.quantity},
        )
        db.commit()
        return get_sale_detail(sale_id, db)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid sale/item data") from e
    except Exception as e:
        db.rollback()
        # Trigger exceptions (insufficient stock, not draft, ...)
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/{sale_id}/items/{product_id}", response_model=SaleDetailOut, dependencies=[Depends(require_roles(["admin", "staff"]))])
def remove_item(
    sale_id: int,
    product_id: int,
    db: Session = Depends(get_db),
):
    try:
        res = db.execute(
            text("""
                DELETE FROM sale_item
                WHERE sale_id = :sale_id AND product_id = :product_id
            """),
            {"sale_id": sale_id, "product_id": product_id},
        )
        if res.rowcount == 0:
            db.rollback()
            raise HTTPException(status_code=404, detail="Sale item not found")
        db.commit()
        return get_sale_detail(sale_id, db)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/{sale_id}/finalize", response_model=SaleOut, dependencies=[Depends(require_roles(["admin", "staff"]))])
def finalize_sale(sale_id: int, db: Session = Depends(get_db)):
    """
    Finalize a sale:
    - Triggers will check stock, deduct inventory, and set finalized_at.
    """
    try:
        row = db.execute(
            text("""
                UPDATE sale
                SET status = 'finalized'
                WHERE sale_id = :sale_id
                RETURNING sale_id, customer_id, created_by_user_id, sale_date, status, total_price, finalized_at
            """),
            {"sale_id": sale_id},
        ).mappings().first()

        if not row:
            db.rollback()
            raise HTTPException(status_code=404, detail="Sale not found")

        db.commit()
        return SaleOut(**dict(row))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e)) from e
