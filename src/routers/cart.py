import datetime
from sqlalchemy import delete
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.schemas.cart import CartItemAdd, CartItemResponse, CartResponse

from src.database.models import MovieModel, CartModel, CartItemModel
from src.database.session import get_postgresql_db

from src.services.auth.dependencies import get_current_user
from src.database.models import UserModel

router = APIRouter(prefix="/cart", tags=["/cart"])


@router.get("/", response_model=CartResponse)
async def get_cart(
    db: AsyncSession = Depends(get_postgresql_db),
    current_user: UserModel = Depends(get_current_user),
):
    result = await db.execute(
        select(CartModel).where(CartModel.user_id == current_user.id)
    )
    user_cart = result.scalar_one_or_none()

    # If no cart container exists for this user yet, build one on the fly
    if not user_cart:
        user_cart = CartModel(user_id=current_user.id)
        db.add(user_cart)
        await db.commit()
        await db.refresh(user_cart)

    return user_cart


@router.post("/items", response_model=CartItemResponse)
async def add_movie_to_the_cart(
    item: CartItemAdd,
    db: AsyncSession = Depends(get_postgresql_db),
    current_user: UserModel = Depends(get_current_user),
):

    user_cart_result = await db.execute(
        select(CartModel).where(CartModel.user_id == current_user.id)
    )
    user_cart = user_cart_result.scalar_one_or_none()
    if not user_cart:
        user_cart = CartModel(user_id=current_user.id)
        db.add(user_cart)
        await db.flush()

    result = await db.execute(
        select(CartItemModel).where(
            CartItemModel.cart_id == user_cart.id,
            CartItemModel.movie_id == item.movie_id,
        )
    )
    item_in_cart = result.scalar_one_or_none()
    if item_in_cart:
        raise HTTPException(
            status_code=404, detail="Movie is already purchased or a is duplicate"
        )

    new_item = CartItemModel(
        cart_id=user_cart.id,
        movie_id=item.movie_id,
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item


@router.delete("/items/{item_id}", status_code=204)
async def delete_item(
    item_id: int,
    db: AsyncSession = Depends(get_postgresql_db),
    current_user: UserModel = Depends(get_current_user),
):
    result = await db.execute(
        select(CartModel).where(CartModel.user_id == current_user.id)
    )
    user_cart = result.scalar_one_or_none()
    if not user_cart:
        raise HTTPException(status_code=404, detail="The cart is absent")

    items = await db.execute(
        select(CartItemModel).where(
            CartItemModel.id == item_id, CartItemModel.cart_id == user_cart.id
        )
    )
    item = items.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found in your cart")

    db.delete(item)
    await db.commit()


@router.delete("/", status_code=204)
async def delete_cart(
    db: AsyncSession = Depends(get_postgresql_db),
    current_user: UserModel = Depends(get_current_user),
):
    result = await db.execute(
        select(CartModel).where(CartModel.user_id == current_user.id)
    )
    user_cart = result.scalar_one_or_none()
    if not user_cart:
        raise HTTPException(status_code=404, detail="The cart is absent")

    await db.execute(
        delete(CartItemModel).where(CartItemModel.cart_id == user_cart.id)
    )
    await db.commit()
