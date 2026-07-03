from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from src.schemas.orders import OrderResponseSchema, OrderItemResponseSchema
from src.database.session import get_postgresql_db
from src.services.auth.dependencies import get_current_user
from src.database.models import (
    UserModel,
    CartModel,
    CartItemModel,
    OrderModel,
    OrderStatusEnum,
    OrderItemModel,
)

router = APIRouter(prefix="/orders", tags=["/orders"])


@router.post("/checkout", response_model="OrderResponseSchema")
async def checkout(
    db: AsyncSession = Depends(get_postgresql_db),
    current_user: UserModel = Depends(get_current_user),
):
    user_cart_result = await db.execute(
        select(CartModel)
        .options(joinedload(CartModel.items).joinedload(CartItemModel.movie))
        .where(CartModel.user_id == current_user.id)
    )
    user_cart = user_cart_result.scalar_one_or_none()
    if not user_cart or user_cart.count() == 0:
        raise HTTPException(status_code=400, detail="Cart is empty")

    new_order = OrderModel(
        user_id=current_user.id,
        status=OrderStatusEnum.PENDING,
        total_amount=Decimal("0.00"),
    )

    order_items = []
    total_running_amount = Decimal("0.00")

    for cart_item in user_cart.items:
        movie_price = cart_item.movie.price
        total_running_amount += movie_price

        order_item = OrderItemModel(
            movie_id=cart_item.movie_id, price_at_order=movie_price, order=new_order
        )
        order_items.append(order_item)

    new_order.total_amount = total_running_amount
    new_order.items = order_items

    user_cart.items.clear()

    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)

    return new_order
