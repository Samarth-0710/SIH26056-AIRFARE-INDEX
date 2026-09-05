from fastapi import FastAPI
from sqlalchemy.exc import OperationalError
from fastapi.responses import JSONResponse
from app.api.routes import booking_windows, index, ingestion, intelligence, quality, routes, simulation
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.api_title, version="1.0.0", description="Persistence and retrieval API for official SIH26056 statistical-engine outputs.")

@app.exception_handler(OperationalError)
async def database_unavailable(_, __):
    return JSONResponse(status_code=503, content={"detail": "database is unavailable or migrations have not been applied"})

@app.get("/", tags=["System"])
def root():
    return {"message": "SIH26056 Airfare Price Index API", "status": "running"}

@app.get("/health", tags=["System"])
def health():
    return {"status": "healthy"}

for router in (index.router, routes.router, booking_windows.router, quality.router, intelligence.router, simulation.router, ingestion.router):
    app.include_router(router, prefix="/api/v1")
