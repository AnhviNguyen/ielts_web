"""
app/main.py
────────────
FastAPI application entry point.
Registers routers, CORS middleware, and handles table creation on startup.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.db.database import engine
from app.db.models import Base  # noqa: F401 – imported so Base.metadata is populated
from app.routers import auth, history, practice, profile, progress, users
from app.routers import mock_tests, writing, speaking as speaking_router

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# Suppress noisy third-party loggers
for _noisy in ("filelock", "httpx", "httpcore", "urllib3", "huggingface_hub",
               "python_multipart", "multipart"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)


# ── Lifespan (startup / shutdown) ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all tables on startup (idempotent). Close engine on shutdown."""
    import asyncio
    logger.info("Starting up — creating database tables if needed …")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database ready.")
    # Warm up ML models in background (non-blocking)
    try:
        from ml.model_registry import preload_all
        asyncio.get_event_loop().run_in_executor(None, preload_all)
        logger.info("ML model preload scheduled in background thread.")
    except Exception as exc:
        logger.warning("ML preload skipped: %s", exc)
    yield
    logger.info("Shutting down — disposing engine …")
    await engine.dispose()


# ── App factory ──────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description="IELTS Learning Platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

uploads_dir = Path("uploads")
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(progress.router)
app.include_router(history.router)
app.include_router(mock_tests.router)
app.include_router(writing.router)
app.include_router(users.router)
app.include_router(practice.router)
app.include_router(speaking_router.router)


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """Simple liveness probe."""
    return {"status": "ok", "app": settings.APP_NAME}


# ── Audio files ───────────────────────────────────────────────────────────────
_AUDIO_DIR = Path(__file__).resolve().parents[1] / "data" / "assets" / "audio"
_IMAGE_DIR = Path(__file__).resolve().parents[1] / "data" / "assets" / "images"

@app.get("/audio/{file_id}", tags=["Audio"])
async def serve_audio(file_id: str):
    """Serve local IELTS audio file by UUID."""
    # strip any extension the caller may include
    stem = file_id.split(".")[0]
    for ext in (".mp3", ".m4a", ".ogg", ".wav"):
        candidate = _AUDIO_DIR / f"{stem}{ext}"
        if candidate.exists():
            media_type = "audio/mpeg" if ext == ".mp3" else "audio/mp4" if ext == ".m4a" else "audio/ogg" if ext == ".ogg" else "audio/wav"
            return FileResponse(str(candidate), media_type=media_type, headers={"Accept-Ranges": "bytes"})
    raise HTTPException(status_code=404, detail=f"Audio file not found: {stem}")


@app.get("/images/{file_id}", tags=["Images"])
async def serve_image(file_id: str):
    """Serve local thumbnail image by UUID."""
    stem = file_id.split(".")[0]
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        candidate = _IMAGE_DIR / f"{stem}{ext}"
        if candidate.exists():
            media_type = "image/png" if ext == ".png" else "image/jpeg" if ext in (".jpg", ".jpeg") else "image/webp"
            return FileResponse(str(candidate), media_type=media_type, headers={"Cache-Control": "public, max-age=86400"})
    raise HTTPException(status_code=404, detail=f"Image not found: {stem}")
