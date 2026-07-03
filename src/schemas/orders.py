from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from src.database.models import OrderStatusEnum, OrderItemModel


class OrderItemResponseSchema(BaseModel):
    id: int
    movie_id: int
    price_at_order: Decimal

    model_config = {"from_attributes": True}


class OrderResponseSchema(BaseModel):
    id: int
    status: OrderStatusEnum
    total_amount: Decimal
    created_at: datetime
    order_items: list[OrderItemResponseSchema]

    model_config = {"from_attributes": True}
