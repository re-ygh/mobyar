from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field


class RepairCreate(BaseModel):
    customer_id: int
    phone_id: int
    service_id: int
    notes: str | None = None


class RepairStatusUpdate(BaseModel):
    status: str = Field(..., description="pending | in_progress | ready | delivered | cancelled")


class RepairOut(BaseModel):
    repair_id: int
    customer_id: int
    phone_id: int
    service_id: int
    price_at_time: Decimal
    status: str
    created_by_user_id: int | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
