from contextlib import asynccontextmanager
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.core.logging import configure_logging
from app.routers import auth, grievances, notifications, officer, reference
from app.seed import seed_database

settings = get_settings()
configure_logging()

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    if settings.APP_ENV != "test":
        # Ensure schema exists for quick local dev and seed initial demo data
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            seed_database(db)
        finally:
            db.close()

        if settings.JOB_RUNNER == "apscheduler" and not scheduler.running:
            scheduler.start()
    try:
        yield
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

upload_path = Path(settings.UPLOAD_DIR)
upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(grievances.router, prefix=settings.API_V1_PREFIX)
app.include_router(officer.router, prefix=settings.API_V1_PREFIX)
app.include_router(notifications.router, prefix=settings.API_V1_PREFIX)
app.include_router(reference.router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "env": settings.APP_ENV,
        "db_dialect": "sqlite" if settings.is_sqlite else "postgresql",
        "job_runner": settings.JOB_RUNNER,
        "ai_provider": settings.AI_PROVIDER,
    }
