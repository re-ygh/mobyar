from decimal import Decimal
from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(..., max_length=160)
    description: str | None = None
    image: str | None = None
    current_price: Decimal = Field(..., ge=0)
    stock: int = Field(0, ge=0)
    category_id: int
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = Field(None, max_length=160)
    description: str | None = None
    image: str | None = None
    current_price: Decimal | None = Field(None, ge=0)
    stock: int | None = Field(None, ge=0)
    category_id: int | None = None
    is_active: bool | None = None


class ProductOut(BaseModel):
    product_id: int
    name: str
    description: str | None = None
    image: str | None = None
    current_price: Decimal
    stock: int
    category_id: int
    category_name: str
    is_active: bool
