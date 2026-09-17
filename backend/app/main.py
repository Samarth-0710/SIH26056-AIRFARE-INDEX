import os
import sys
from contextlib import asynccontextmanager

# Ensure sibling repository source directories are always in sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
for src_path in [
    os.path.join(repo_root, "backend"),
    os.path.join(repo_root, "data-collection", "src"),
    os.path.join(repo_root, "data-quality"),
    os.path.join(repo_root, "data-quality", "src"),
    os.path.join(repo_root, "statistical-engine", "src"),
    os.path.join(repo_root, "intelligence", "src"),
]:
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

from dotenv import load_dotenv
for env_candidate in [
    os.path.join(repo_root, "backend", ".env"),
    os.path.join(repo_root, ".env"),
]:
    if os.path.exists(env_candidate):
        load_dotenv(dotenv_path=env_candidate)
        break

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from fastapi.responses import JSONResponse
from app.api.routes import (
    booking_windows,
    index,
    ingestion,
    intelligence,
    pipeline,
    quality,
    routes,
    simulation,
    validation,
)
from app.core.config import get_settings
from app.db.database import Base, SessionLocal, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema is created on startup
    Base.metadata.create_all(bind=engine)
    if not app.dependency_overrides:
        try:
            from app.services.pipeline_service import load_mospi_reference_dataset

            with SessionLocal() as db:
                load_mospi_reference_dataset(db)
        except Exception as exc:
            import logging

            logging.getLogger("uvicorn.error").warning(
                "MoSPI reference auto-load error on startup: %s", exc
            )
    yield


settings = get_settings()
app = FastAPI(
    title=settings.api_title,
    version="1.0.0",
    description="Persistence and retrieval API for official SIH26056 statistical-engine outputs.",
    lifespan=lifespan,
)

# Enable CORS for frontend dashboard (Next.js)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(OperationalError)
async def database_unavailable(_, __):
    return JSONResponse(
        status_code=503,
        content={"detail": "database is unavailable or migrations have not been applied"},
    )


@app.get("/", tags=["System"])
def root():
    return {"message": "SIH26056 Airfare Price Index API", "status": "running"}


@app.get("/health", tags=["System"])
def health():
    return {"status": "healthy"}


for router in (
    index.router,
    routes.router,
    booking_windows.router,
    quality.router,
    intelligence.router,
    simulation.router,
    validation.router,
    ingestion.router,
    pipeline.router,
):
    app.include_router(router, prefix="/api/v1")
