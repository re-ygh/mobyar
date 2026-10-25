from decimal import Decimal
from pydantic import BaseModel, Field


class ServiceCreate(BaseModel):
    service_name: str = Field(..., max_length=160)
    description: str | None = None
    current_price: Decimal = Field(..., ge=0)
    is_active: bool = True


class ServiceUpdate(BaseModel):
    service_name: str | None = Field(None, max_length=160)
    description: str | None = None
    current_price: Decimal | None = Field(None, ge=0)
    is_active: bool | None = None


class ServiceOut(BaseModel):
    service_id: int
    service_name: str
    description: str | None = None
    current_price: Decimal
    is_active: bool
