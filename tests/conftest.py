import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.database import Base, engine
from app.main import app

API_KEY = settings.api_key
AUTH_HEADERS = {"X-API-Key": API_KEY}


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(loop_scope="session")
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
