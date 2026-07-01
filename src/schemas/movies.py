from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class MovieCreate(BaseModel):
    title: str = Field(max_length=512)
    description: str = Field(max_length=1024)
    duration_minutes: int = Field(gt=0)
    release_year: int = Field(ge=1888, le=2026)


class MovieResponse(MovieCreate):
    id: int

    class Config:
        from_attributes = True
