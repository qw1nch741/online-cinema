"""Movie catalog endpoints: list, detail, and create."""

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import MovieModel, UserModel
from src.database.session import get_postgresql_db
from src.schemas.movies import MovieCreate, MovieResponse
from src.services.auth.dependencies import get_current_user

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.post(
    "/",
    response_model=MovieResponse,
    summary="Create a movie",
    description=(
        "Add a new movie to the catalog.\n\n"
        "**Action:** Creates a movie record with title, description, duration, and release year.\n\n"
        "**Authorization:** Bearer access token required.\n\n"
        "**Parameters (body):**\n"
        "- `title` — movie title (max 512 chars)\n"
        "- `description` — synopsis (max 1024 chars, must be unique)\n"
        "- `duration_minutes` — runtime in minutes (must be > 0)\n"
        "- `release_year` — year of release (1888–2026)"
    ),
    responses={
        200: {"description": "Movie created successfully"},
        400: {"description": "Movie with this description already exists"},
        401: {"description": "Missing or invalid Bearer access token"},
        422: {"description": "Validation error"},
    },
)
async def create_movie(
    movie: MovieCreate,
    db: AsyncSession = Depends(get_postgresql_db),
    current_user: UserModel = Depends(get_current_user),
):
    result = await db.execute(
        select(MovieModel).where(MovieModel.description == movie.description)
    )
    movie_exists = result.scalar_one_or_none()
    if movie_exists:
        raise HTTPException(status_code=400, detail="Movie already exists")

    new_movie = MovieModel(
        title=movie.title,
        description=movie.description,
        duration_minutes=movie.duration_minutes,
        release_year=movie.release_year,
    )
    db.add(new_movie)
    await db.commit()
    await db.refresh(new_movie)

    return new_movie


@router.get(
    "/",
    response_model=list[MovieResponse],
    summary="List all movies",
    description=(
        "Retrieve the full movie catalog.\n\n"
        "**Action:** Returns all movies currently stored in the database.\n\n"
        "**Authorization:** Not required."
    ),
    responses={
        200: {"description": "List of movies"},
    },
)
async def get_movies(db: AsyncSession = Depends(get_postgresql_db)):
    movies_result = await db.execute(select(MovieModel))
    movies = movies_result.scalars().all()
    return movies


@router.get(
    "/{movie_id}",
    response_model=MovieResponse,
    summary="Get movie details",
    description=(
        "Retrieve detailed information for a single movie.\n\n"
        "**Action:** Returns one movie by its numeric ID.\n\n"
        "**Authorization:** Not required.\n\n"
        "**Parameters:**\n"
        "- `movie_id` — unique movie identifier (path parameter)"
    ),
    responses={
        200: {"description": "Movie found"},
        404: {"description": "Movie not found"},
    },
)
async def get_movie(
    movie_id: int = Path(..., description="Numeric ID of the movie", examples=[1]),
    db: AsyncSession = Depends(get_postgresql_db),
):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie
