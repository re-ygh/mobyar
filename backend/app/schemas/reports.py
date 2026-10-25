from decimal import Decimal
from datetime import date, datetime
from pydantic import BaseModel


class DailySalesRow(BaseModel):
    sale_day: date
    sales_count: int
    revenue: Decimal


class LowStockRow(BaseModel):
    product_id: int
    name: str
    stock: int
    current_price: Decimal
    category_name: str


class OpenRepairRow(BaseModel):
    repair_id: int
    created_at: datetime
    updated_at: datetime
    status: str
    price_at_time: Decimal
    customer_name: str
    customer_phone: str
    service_name: str
    imei: str
