from pydantic import BaseModel, Field


class MovieCreate(BaseModel):
    """Request body for creating a new movie."""

    title: str = Field(
        ..., max_length=512, description="Movie title", examples=["Inception"]
    )
    description: str = Field(
        ...,
        max_length=1024,
        description="Movie synopsis (must be unique across catalog)",
        examples=[
            "A thief who steals corporate secrets through dream-sharing technology."
        ],
    )
    duration_minutes: int = Field(
        ..., gt=0, description="Runtime in minutes", examples=[148]
    )
    release_year: int = Field(
        ..., ge=1888, le=2026, description="Year of release", examples=[2010]
    )


class MovieResponse(MovieCreate):
    """Movie record returned from the API."""

    id: int = Field(..., description="Unique movie ID")

    class Config:
        from_attributes = True
