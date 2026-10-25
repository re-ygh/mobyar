"""
Category CRUD.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryOut

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    rows = db.execute(
        text("SELECT category_id, category_name, type FROM category ORDER BY category_id ASC")
    ).mappings().all()
    return [CategoryOut(**dict(r)) for r in rows]


@router.post("", response_model=CategoryOut, dependencies=[Depends(require_roles(["admin", "staff"]))])
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    try:
        row = db.execute(
            text("""
                INSERT INTO category (category_name, type)
                VALUES (:category_name, :type)
                RETURNING category_id, category_name, type
            """),
            payload.model_dump(),
        ).mappings().first()
        db.commit()
        return CategoryOut(**dict(row))
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Category already exists or invalid data") from e


@router.put("/{category_id}", response_model=CategoryOut, dependencies=[Depends(require_roles(["admin", "staff"]))])
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)):
    data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Build dynamic SET clause safely
    set_clause = ", ".join([f"{k} = :{k}" for k in data.keys()])
    data["category_id"] = category_id

    try:
        row = db.execute(
            text(f"""
                UPDATE category
                SET {set_clause}
                WHERE category_id = :category_id
                RETURNING category_id, category_name, type
            """),
            data,
        ).mappings().first()

        if not row:
            db.rollback()
            raise HTTPException(status_code=404, detail="Category not found")

        db.commit()
        return CategoryOut(**dict(row))
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Update violates constraints") from e


@router.delete("/{category_id}", dependencies=[Depends(require_roles(["admin"]))])
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """
    Hard-delete a category (admin only).

    In real systems you'd usually soft-delete, but for this course project a hard delete is ok.
    """
    # Prevent deleting categories that still have products
    has_products = db.execute(
        text("SELECT 1 FROM product WHERE category_id = :category_id LIMIT 1"),
        {"category_id": category_id},
    ).first()

    if has_products:
        raise HTTPException(status_code=400, detail="Cannot delete category with existing products")

    res = db.execute(
        text("DELETE FROM category WHERE category_id = :category_id"),
        {"category_id": category_id},
    )
    if res.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=404, detail="Category not found")
    db.commit()
    return {"ok": True}
