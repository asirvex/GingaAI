import logging

from fastapi import FastAPI

from app.api.claims import router as claims_router
from app.config import settings
from app.database import Base, engine

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Minimal claims processing and adjudication service",
)

app.include_router(claims_router)


@app.get("/health")
def health():
    return {"status": "ok"}
