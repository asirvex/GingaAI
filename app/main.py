import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.claims import router as claims_router
from app.config import settings
from app.database import Base, engine

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Minimal claims processing and adjudication service",
    lifespan=lifespan,
)

app.include_router(claims_router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
