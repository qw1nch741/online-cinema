from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.database.models import OrderStatusEnum


class OrderItemResponseSchema(BaseModel):
    """Single line item within an order."""

    id: int = Field(..., description="Unique order item ID")
    movie_id: int = Field(..., description="ID of the purchased movie")
    price_at_order: Decimal = Field(
        ..., description="Movie price at the time of checkout"
    )

    model_config = {"from_attributes": True}


class OrderResponseSchema(BaseModel):
    """Order created from cart checkout."""

    id: int = Field(..., description="Unique order ID")
    status: OrderStatusEnum = Field(
        ..., description="Order status: pending, paid, or canceled"
    )
    total_amount: Decimal = Field(
        ..., description="Total order amount at checkout time"
    )
    created_at: datetime = Field(..., description="Order creation timestamp")
    order_items: list[OrderItemResponseSchema] = Field(
        ..., description="Movies included in the order"
    )

    model_config = {"from_attributes": True}
