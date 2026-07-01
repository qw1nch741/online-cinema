from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from src.config.settings import get_settings

settings = get_settings()


# 1. Base class for declarative relational mapping models
class Base(DeclarativeBase):
    pass


# 2. Asynchronous Engine using our Pydantic computed field URL
postgresql_engine = create_async_engine(settings.ASYNC_DATABASE_URL, echo=False)

# 3. Dedicated Async Session Factory (Clean SQLAlchemy 2.0 structure - no type-ignores needed!)
AsyncPostgresqlSessionLocal = async_sessionmaker(
    bind=postgresql_engine,
    autoflush=False,
    expire_on_commit=False,
)


# 4. FastAPI Request Dependency
async def get_postgresql_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncPostgresqlSessionLocal() as session:
        yield session


# 5. Background Task Context Manager (For Celery/Scripts)
@asynccontextmanager
async def get_postgresql_db_contextmanager() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncPostgresqlSessionLocal() as session:
        yield session
