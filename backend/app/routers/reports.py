"""
Reporting endpoints (read-only).

We mainly rely on SQL views (03_views.sql) for simplicity and performance.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.schemas.reports import DailySalesRow, LowStockRow, OpenRepairRow

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/daily-sales", response_model=list[DailySalesRow], dependencies=[Depends(require_roles(["admin", "staff"]))])
def daily_sales(
    date_from: str | None = Query(None, description="YYYY-MM-DD"),
    date_to: str | None = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    Daily sales report, based on v_daily_sales.
    Optional filter: date range.
    """
    where = []
    params = {}

    if date_from:
        where.append("sale_day >= :date_from")
        params["date_from"] = date_from
    if date_to:
        where.append("sale_day <= :date_to")
        params["date_to"] = date_to

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    rows = db.execute(
        text(f"""
            SELECT sale_day, sales_count, revenue
            FROM v_daily_sales
            {where_sql}
            ORDER BY sale_day DESC
        """),
        params,
    ).mappings().all()

    return [DailySalesRow(**dict(r)) for r in rows]


@router.get("/low-stock", response_model=list[LowStockRow], dependencies=[Depends(require_roles(["admin", "staff"]))])
def low_stock(
    threshold: int = Query(5, ge=0, description="Show products with stock <= threshold"),
    db: Session = Depends(get_db),
):
    """
    Low stock report.
    Note: we can either use the view with fixed threshold (=5) or filter directly.
    Here we filter directly to support a dynamic threshold.
    """
    rows = db.execute(
        text("""
            SELECT
              p.product_id,
              p.name,
              p.stock,
              p.current_price,
              c.category_name
            FROM product p
            JOIN category c ON c.category_id = p.category_id
            WHERE p.is_active = TRUE
              AND p.stock <= :threshold
            ORDER BY p.stock ASC, p.product_id ASC
        """),
        {"threshold": threshold},
    ).mappings().all()

    return [LowStockRow(**dict(r)) for r in rows]


@router.get("/open-repairs", response_model=list[OpenRepairRow], dependencies=[Depends(require_roles(["admin", "staff"]))])
def open_repairs(db: Session = Depends(get_db)):
    """
    Open repairs report based on v_open_repairs.
    """
    rows = db.execute(
        text("""
            SELECT
              repair_id,
              created_at,
              updated_at,
              status,
              price_at_time,
              customer_name,
              customer_phone,
              service_name,
              imei
            FROM v_open_repairs
            ORDER BY created_at DESC
        """)
    ).mappings().all()

    return [OpenRepairRow(**dict(r)) for r in rows]


@router.get("/top-products-30d", dependencies=[Depends(require_roles(["admin", "staff"]))])
def top_products_30d(db: Session = Depends(get_db)):
    """
    Top 10 products in last 30 days.
    """
    rows = db.execute(
        text("""
            SELECT product_id, name, total_qty, total_amount
            FROM v_top_products_30d
        """)
    ).mappings().all()
    return [dict(r) for r in rows]


@router.get("/service-revenue-30d", dependencies=[Depends(require_roles(["admin", "staff"]))])
def service_revenue_30d(db: Session = Depends(get_db)):
    """
    Service revenue in last 30 days (delivered repairs).
    """
    rows = db.execute(
        text("""
            SELECT service_id, service_name, orders_count, revenue
            FROM v_service_revenue_30d
        """)
    ).mappings().all()
    return [dict(r) for r in rows]
