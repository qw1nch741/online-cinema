"""Shopping cart endpoints: view, add, remove items, and clear cart."""

from sqlalchemy import delete, select
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import CartItemModel, CartModel, UserModel
from src.database.session import get_postgresql_db
from src.schemas.cart import CartItemAdd, CartItemResponse, CartResponse
from src.services.auth.dependencies import get_current_user

router = APIRouter(prefix="/cart", tags=["Shopping Cart"])


@router.get(
    "/",
    response_model=CartResponse,
    summary="Get current user's cart",
    description=(
        "Retrieve the authenticated user's shopping cart.\n\n"
        "**Action:** Returns the cart and its items. If no cart exists yet, one is created automatically.\n\n"
        "**Authorization:** Bearer access token required."
    ),
    responses={
        200: {"description": "Cart with items"},
        401: {"description": "Missing or invalid Bearer access token"},
    },
)
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


@router.post(
    "/items",
    response_model=CartItemResponse,
    summary="Add movie to cart",
    description=(
        "Add a movie to the authenticated user's cart.\n\n"
        "**Action:** Creates a cart item linking the user cart to a movie. "
        "The same movie cannot be added twice to one cart.\n\n"
        "**Authorization:** Bearer access token required.\n\n"
        "**Parameters (body):**\n"
        "- `movie_id` — ID of the movie to add"
    ),
    responses={
        200: {"description": "Item added to cart"},
        401: {"description": "Missing or invalid Bearer access token"},
        404: {"description": "Movie already in cart or already purchased"},
        422: {"description": "Validation error"},
    },
)
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


@router.delete(
    "/items/{item_id}",
    status_code=204,
    summary="Remove item from cart",
    description=(
        "Remove a single item from the authenticated user's cart.\n\n"
        "**Action:** Deletes the cart item by its ID. Only items belonging to the current user's cart can be removed.\n\n"
        "**Authorization:** Bearer access token required.\n\n"
        "**Parameters:**\n"
        "- `item_id` — numeric ID of the cart item (path parameter)"
    ),
    responses={
        204: {"description": "Item removed"},
        401: {"description": "Missing or invalid Bearer access token"},
        404: {"description": "Cart or item not found"},
    },
)
async def delete_item(
    item_id: int = Path(..., description="ID of the cart item to remove", examples=[1]),
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


@router.delete(
    "/",
    status_code=204,
    summary="Clear entire cart",
    description=(
        "Remove all items from the authenticated user's cart.\n\n"
        "**Action:** Deletes every cart item but keeps the empty cart container.\n\n"
        "**Authorization:** Bearer access token required."
    ),
    responses={
        204: {"description": "Cart cleared"},
        401: {"description": "Missing or invalid Bearer access token"},
        404: {"description": "Cart not found"},
    },
)
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

    await db.execute(delete(CartItemModel).where(CartItemModel.cart_id == user_cart.id))
    await db.commit()
