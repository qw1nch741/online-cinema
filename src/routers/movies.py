from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.schemas.movies import MovieCreate, MovieResponse

from src.database.models import MovieModel
from src.database.session import get_postgresql_db

from src.services.auth.dependencies import get_current_user
from src.database.models import UserModel

router = APIRouter(prefix="/movies", tags=["/movies"])


@router.post("/", response_model=MovieResponse)
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


@router.get("/", response_model=list[MovieResponse])
async def get_movies(db: AsyncSession = Depends(get_postgresql_db)):
    movies_result = await db.execute(select(MovieModel))
    movies = movies_result.scalars().all()
    return movies


@router.get("/{movie_id}", response_model=MovieResponse)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_postgresql_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie
