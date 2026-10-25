"""
Product CRUD + stock/price updates.

Important DB rules (enforced by triggers):
- When product.current_price changes => row inserted into product_price_history
- When product.stock changes => row inserted into inventory_history
- Stock cannot become negative (DB-level)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.schemas.product import ProductCreate, ProductUpdate, ProductOut

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
def list_products(
    include_inactive: bool = Query(False, description="Include is_active=false products"),
    db: Session = Depends(get_db),
):
    where = "" if include_inactive else "WHERE p.is_active = TRUE"
    rows = db.execute(
        text(f"""
            SELECT
              p.product_id, p.name, p.description, p.image,
              p.current_price, p.stock, p.category_id, p.is_active,
              c.category_name
            FROM product p
            JOIN category c ON c.category_id = p.category_id
            {where}
            ORDER BY p.product_id ASC
        """)
    ).mappings().all()
    return [ProductOut(**dict(r)) for r in rows]


@router.post("", response_model=ProductOut, dependencies=[Depends(require_roles(["admin", "staff"]))])
def create_product(
    payload: ProductCreate,
    current_user: dict = Depends(require_roles(["admin", "staff"])),
    db: Session = Depends(get_db),
):
    try:
        row = db.execute(
            text("""
                INSERT INTO product (name, description, image, current_price, stock, category_id, is_active, updated_by_user_id)
                VALUES (:name, :description, :image, :current_price, :stock, :category_id, :is_active, :updated_by_user_id)
                RETURNING product_id
            """),
            {**payload.model_dump(), "updated_by_user_id": current_user["user_id"]},
        ).mappings().first()
        product_id = row["product_id"]

        # Return enriched view (with category_name)
        out = db.execute(
            text("""
                SELECT
                  p.product_id, p.name, p.description, p.image,
                  p.current_price, p.stock, p.category_id, p.is_active,
                  c.category_name
                FROM product p
                JOIN category c ON c.category_id = p.category_id
                WHERE p.product_id = :product_id
            """),
            {"product_id": product_id},
        ).mappings().first()

        db.commit()
        return ProductOut(**dict(out))
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid product data") from e


@router.put("/{product_id}", response_model=ProductOut, dependencies=[Depends(require_roles(["admin", "staff"]))])
def update_product(
    product_id: int,
    payload: ProductUpdate,
    current_user: dict = Depends(require_roles(["admin", "staff"])),
    db: Session = Depends(get_db),
):
    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Always set updated_by_user_id to support audit triggers
    data["updated_by_user_id"] = current_user["user_id"]
    data["product_id"] = product_id

    set_clause = ", ".join([f"{k} = :{k}" for k in data.keys() if k != "product_id"])

    try:
        row = db.execute(
            text(f"""
                UPDATE product
                SET {set_clause}
                WHERE product_id = :product_id
                RETURNING product_id
            """),
            data,
        ).mappings().first()

        if not row:
            db.rollback()
            raise HTTPException(status_code=404, detail="Product not found")

        out = db.execute(
            text("""
                SELECT
                  p.product_id, p.name, p.description, p.image,
                  p.current_price, p.stock, p.category_id, p.is_active,
                  c.category_name
                FROM product p
                JOIN category c ON c.category_id = p.category_id
                WHERE p.product_id = :product_id
            """),
            {"product_id": product_id},
        ).mappings().first()

        db.commit()
        return ProductOut(**dict(out))
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Update violates constraints") from e
    except Exception as e:
        db.rollback()
        # Trigger errors (e.g., negative stock) also come here
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/{product_id}", dependencies=[Depends(require_roles(["admin", "staff"]))])
def deactivate_product(
    product_id: int,
    current_user: dict = Depends(require_roles(["admin", "staff"])),
    db: Session = Depends(get_db),
):
    """
    Soft-delete (deactivate) product.
    """
    res = db.execute(
        text("""
            UPDATE product
               SET is_active = FALSE,
                   updated_by_user_id = :uid
             WHERE product_id = :product_id
        """),
        {"uid": current_user["user_id"], "product_id": product_id},
    )
    if res.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=404, detail="Product not found")
    db.commit()
    return {"ok": True}
