from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field


class SaleCreate(BaseModel):
    customer_id: int | None = Field(None, description="Nullable: walk-in customer")


class SaleOut(BaseModel):
    sale_id: int
    customer_id: int | None
    created_by_user_id: int
    sale_date: datetime
    status: str
    total_price: Decimal
    finalized_at: datetime | None


class SaleItemAdd(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)


class SaleItemOut(BaseModel):
    sale_item_id: int
    product_id: int
    product_name: str
    quantity: int
    price_at_time: Decimal
    line_total: Decimal


class SaleDetailOut(BaseModel):
    sale: SaleOut
    items: list[SaleItemOut]
