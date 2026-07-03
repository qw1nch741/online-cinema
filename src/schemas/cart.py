from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.movies import MovieResponse


class CartItemAdd(BaseModel):
    """Request body for adding a movie to the cart."""

    movie_id: int = Field(..., description="ID of the movie to add to the cart", examples=[1])


class CartItemResponse(BaseModel):
    """Single item in a shopping cart."""

    id: int = Field(..., description="Unique cart item ID")
    added_at: datetime = Field(..., description="Timestamp when the movie was added")
    movie: MovieResponse = Field(..., description="Movie details for this cart item")

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    """Authenticated user's shopping cart."""

    id: int = Field(..., description="Unique cart ID")
    user_id: int = Field(..., description="Owner user ID")
    items: list[CartItemResponse] = Field(..., description="Movies currently in the cart")

    model_config = ConfigDict(from_attributes=True)
