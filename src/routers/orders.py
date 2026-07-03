"""Order endpoints: checkout cart into a pending order."""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.database.models import (
    CartItemModel,
    CartModel,
    OrderItemModel,
    OrderModel,
    OrderStatusEnum,
    UserModel,
)
from src.database.session import get_postgresql_db
from src.schemas.orders import OrderResponseSchema
from src.services.auth.dependencies import get_current_user

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "/checkout",
    response_model=OrderResponseSchema,
    summary="Checkout cart into a pending order",
    description=(
        "Convert the authenticated user's cart into a pending order.\n\n"
        "**Action:**\n"
        "1. Reads all items from the user's cart.\n"
        "2. Creates an `Order` with status `pending`.\n"
        "3. Snapshots each movie price into `price_at_order` on `OrderItem` records.\n"
        "4. Calculates `total_amount` from current movie prices.\n"
        "5. Clears the cart after the order is created.\n\n"
        "**Authorization:** Bearer access token required.\n\n"
        "**Validation:** Returns 400 if the cart is empty."
    ),
    responses={
        200: {"description": "Order created with pending status"},
        400: {"description": "Cart is empty"},
        401: {"description": "Missing or invalid Bearer access token"},
    },
)
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
        movie_price = getattr(cart_item.movie, "price", Decimal("9.99"))
        total_running_amount += movie_price

        order_item = OrderItemModel(
            movie_id=cart_item.movie_id, price_at_order=movie_price, order=new_order
        )
        order_items.append(order_item)

    new_order.total_amount = total_running_amount  # type: ignore[assignment]
    new_order.items = order_items

    user_cart.items.clear()

    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)

    return new_order
