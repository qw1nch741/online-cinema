from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from src.schemas.movies import MovieResponse


class CartItemAdd(BaseModel):
    movie_id: int


class CartItemResponse(BaseModel):
    id: int
    added_at: datetime
    movie: MovieResponse

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    id: int
    user_id: int
    items: list[CartItemResponse]

    model_config = ConfigDict(from_attributes=True)
