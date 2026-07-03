import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Import your FastAPI app and database dependencies
from src.main import app
from src.database.session import Base, get_postgresql_db

# 1. Setup the Async Test Engine
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 2. Database Fixture: Creates and drops tables for every single test
@pytest_asyncio.fixture(scope="function")
async def test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # The test runs here!

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# 3. Session Fixture: Yields the actual database session
@pytest_asyncio.fixture(scope="function")
async def db_session(test_db):
    async with TestingSessionLocal() as session:
        yield session


# 4. Client Fixture: Overrides the dependency and fakes HTTP requests
@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_postgresql_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as test_client:
        yield test_client
