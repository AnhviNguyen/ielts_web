"""
app/main.py
────────────
FastAPI application entry point.
Registers routers, CORS middleware, and handles table creation on startup.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

import sentry_sdk
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.db.database import engine, get_db
from app.db.models import Base  # noqa: F401 – imported so Base.metadata is populated
from app.routers import auth, history, practice, users
from app.routers import admin

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        environment=settings.ENVIRONMENT,
    )

setup_logging(debug=settings.DEBUG)
from app.routers import mock_tests, writing, speaking as speaking_router
from app.routers.vocabulary import router as vocabulary_router, annotations_router
from app.routers.leaderboard import router as leaderboard_router
from app.routers.shadowing import router as shadowing_router
from app.routers.mock_exams import router as mock_exams_router
from app.routers.translation import router as translation_router
from app.routers.pronunciation import router as pronunciation_router

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
    if settings.AUTO_CREATE_TABLES and settings.ENVIRONMENT != "production":
        logger.info("Starting up — creating database tables if needed (dev/SQLite) …")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified.")
    else:
        logger.info(
            "Skipping create_all — run: alembic upgrade head (ENVIRONMENT=%s, AUTO_CREATE_TABLES=%s)",
            settings.ENVIRONMENT,
            settings.AUTO_CREATE_TABLES,
        )
    if settings.redis_required:
        from app.core.cache import cache

        if not cache.ping():
            raise RuntimeError(
                "Redis is required (ENVIRONMENT=production or REDIS_REQUIRED=true) but unreachable"
            )
        logger.info("Redis connection verified.")
    # Migrations managed by Alembic — run: alembic upgrade head
    logger.info("Database ready.")
    if settings.ml_preload_on_startup:
        try:
            from ml.model_registry import preload_all
            asyncio.get_event_loop().run_in_executor(None, preload_all)
            logger.info("ML model preload scheduled in background thread.")
        except Exception as exc:
            logger.warning("ML preload skipped: %s", exc)
    else:
        logger.info("ML preload disabled (ML_PRELOAD_ON_STARTUP / production / Celery).")
    try:
        from app.services.mock_data_service import MockDataService

        count = MockDataService.default().warmup_index()
        logger.info("Mock data index warmed up (%d mock tests).", count)
    except Exception as exc:
        logger.warning("Mock data index warmup skipped: %s", exc)

    # Seed translation practice data if tables are empty
    try:
        from app.db.database import AsyncSessionLocal
        from app.services.translation_service import TranslationService

        async with AsyncSessionLocal() as seed_db:
            seeded = await TranslationService(seed_db).seed_if_empty()
            if seeded:
                logger.info("Translation practice seed data loaded.")
    except Exception as exc:
        logger.warning("Translation seed skipped: %s", exc)

    yield
    logger.info("Shutting down — disposing engine …")
    await engine.dispose()


# ── App factory ──────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description="IELTS Learning Platform API",
    version="1.0.0",
    docs_url=None if settings.ENVIRONMENT == "production" else "/docs",
    redoc_url=None if settings.ENVIRONMENT == "production" else "/redoc",
    openapi_url=None if settings.ENVIRONMENT == "production" else "/openapi.json",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


class CsrfMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        from app.core.auth_cookies import validate_csrf

        validate_csrf(request)
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.ENVIRONMENT == "production":
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        if scheme == "https" or settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


class ProxyHeadersMiddleware(BaseHTTPMiddleware):
    """Trust X-Forwarded-* from reverse proxy for scheme/client IP."""

    async def dispatch(self, request, call_next):
        forwarded_proto = request.headers.get("x-forwarded-proto")
        if forwarded_proto:
            request.scope["scheme"] = forwarded_proto.split(",", 1)[0].strip()
        forwarded_host = request.headers.get("x-forwarded-host")
        if forwarded_host:
            request.scope["server"] = (forwarded_host.split(",", 1)[0].strip(), 443)
        return await call_next(request)


app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(ProxyHeadersMiddleware)
app.add_middleware(CsrfMiddleware)

if settings.METRICS_ENABLED:
    from app.core.metrics import PrometheusMiddleware, metrics_endpoint

    app.add_middleware(PrometheusMiddleware)

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
if settings.STORAGE_BACKEND.lower() != "s3":
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Serve locally-stored quiz images (UUID-named PNGs from data/assets/images)
_data_images_dir = Path("data/assets/images")
if _data_images_dir.exists():
    app.mount("/data-assets/images", StaticFiles(directory=str(_data_images_dir)), name="data_images")

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(history.router)
app.include_router(mock_tests.router)
app.include_router(writing.router)
app.include_router(users.router)
app.include_router(practice.router)
app.include_router(speaking_router.router)
app.include_router(vocabulary_router)
app.include_router(annotations_router)
app.include_router(leaderboard_router)
app.include_router(shadowing_router)
app.include_router(admin.router)
app.include_router(mock_exams_router)
app.include_router(translation_router)
app.include_router(pronunciation_router)

if settings.METRICS_ENABLED:
    from app.core.metrics import metrics_endpoint

    app.add_api_route("/metrics", metrics_endpoint, methods=["GET"], tags=["Metrics"])


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """Liveness probe with DB and Redis checks."""
    checks = {"status": "ok", "app": settings.APP_NAME, "db": "ok", "redis": "ok"}
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        checks["db"] = "error"
        checks["status"] = "degraded"
    try:
        from app.core.cache import cache

        if not cache.ping():
            checks["redis"] = "error"
            if checks["status"] == "ok":
                checks["status"] = "degraded"
    except Exception:
        checks["redis"] = "error"
        if checks["status"] == "ok":
            checks["status"] = "degraded"

    if settings.CELERY_ENABLED:
        checks["celery"] = "ok"
        try:
            from app.core.celery_app import celery_app

            ping_result = celery_app.control.ping(timeout=2)
            if not ping_result:
                raise RuntimeError("No Celery workers responded")
        except Exception:
            checks["celery"] = "error"
            checks["status"] = "degraded"

    if settings.redis_required and checks.get("redis") == "error":
        checks["status"] = "unhealthy"
        return JSONResponse(status_code=503, content=checks)

    return checks


# ── Audio / image quiz assets ────────────────────────────────────────────────
@app.get("/audio/{file_id}", tags=["Audio"])
async def serve_audio(file_id: str):
    """Serve IELTS audio — redirect to S3/CDN or local file."""
    from app.core.media_assets import resolve_audio

    asset = resolve_audio(file_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Audio file not found: {file_id.split('.')[0]}")
    if asset.source == "s3" and asset.public_url:
        return RedirectResponse(asset.public_url, status_code=302)
    return FileResponse(
        str(asset.local_path),
        media_type=asset.content_type,
        headers={"Accept-Ranges": "bytes"},
    )


@app.get("/images/{file_id}", tags=["Images"])
async def serve_image(file_id: str):
    """Serve quiz thumbnail — redirect to S3/CDN or local file."""
    from app.core.media_assets import resolve_image

    asset = resolve_image(file_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Image not found: {file_id.split('.')[0]}")
    if asset.source == "s3" and asset.public_url:
        return RedirectResponse(asset.public_url, status_code=302)
    return FileResponse(
        str(asset.local_path),
        media_type=asset.content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )
