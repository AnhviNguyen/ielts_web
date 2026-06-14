"""
app/main.py
────────────
FastAPI application entry point.
Registers routers, CORS middleware, and handles table creation on startup.
"""

import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

import sentry_sdk
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
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
from app.routers import auth, history, placement, practice, users
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
from app.routers.conversation import router as conversation_router
from app.routers.forecast import router as forecast_router

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

_CONTENT_TIMING_PATHS = (
    "/mock-tests",
    "/quizzes",
    "/writing/topics",
    "/mock-exams/sets",
)

# Suppress noisy third-party loggers
for _noisy in ("filelock", "httpx", "httpcore", "urllib3", "huggingface_hub",
               "python_multipart", "multipart"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)


# ── Lifespan (startup / shutdown) ────────────────────────────────────────────

async def _log_startup_task(name: str, coro) -> None:
    try:
        await coro
    except Exception as exc:
        logger.warning("%s skipped: %s", name, exc)


async def warmup_mock_data() -> None:
    """Build mock/quiz file index in a worker thread (does not block startup)."""
    import asyncio

    from app.services.mock_data_service import MockDataService

    loop = asyncio.get_running_loop()
    count = await loop.run_in_executor(None, MockDataService.default().warmup_index)
    logger.info("Mock data index warmed up (%d mock tests).", count)


async def preload_ml_models() -> None:
    """Load heavy ML models in a worker thread when ML_PRELOAD_ON_STARTUP is enabled."""
    import asyncio

    from ml.model_registry import preload_all

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, preload_all)
    logger.info("ML model preload complete.")


async def seed_translation_data() -> None:
    from app.db.database import AsyncSessionLocal
    from app.services.translation_service import TranslationService

    async with AsyncSessionLocal() as seed_db:
        try:
            svc = TranslationService(seed_db)
            seeded = await svc.seed_if_empty()
            if seeded:
                logger.info("Translation practice seed data loaded.")
            sync_stats = await svc.sync_seed_content()
            if any(sync_stats.values()):
                logger.info("Translation practice synced: %s", sync_stats)
            await seed_db.commit()
        except Exception:
            await seed_db.rollback()
            raise


async def seed_conversation_data() -> None:
    from app.db.database import AsyncSessionLocal
    from app.services.conversation_service import ConversationService

    async with AsyncSessionLocal() as seed_db:
        try:
            conv_svc = ConversationService(seed_db)
            if await conv_svc.seed_if_empty():
                logger.info("Conversation practice seed data loaded.")
            await conv_svc.sync_seed()
            await seed_db.commit()
        except Exception:
            await seed_db.rollback()
            raise


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

    asyncio.create_task(_log_startup_task("Mock data index warmup", warmup_mock_data()))

    if settings.ml_preload_on_startup:
        asyncio.create_task(_log_startup_task("ML model preload", preload_ml_models()))
    else:
        logger.info("ML preload disabled (ML_PRELOAD_ON_STARTUP / production / Celery).")

    asyncio.create_task(_log_startup_task("Translation seed", seed_translation_data()))
    asyncio.create_task(_log_startup_task("Conversation seed", seed_conversation_data()))

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


@app.middleware("http")
async def content_timing_middleware(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    path = request.url.path
    if request.method == "GET" and any(path == p or path.startswith(f"{p}/") for p in _CONTENT_TIMING_PATHS):
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["Server-Timing"] = f"app;dur={elapsed_ms:.1f}"
        response.headers["X-App-Time-ms"] = f"{elapsed_ms:.1f}"
        logger.info(
            "content_endpoint_timing method=%s path=%s status=%s duration_ms=%.1f",
            request.method,
            path,
            response.status_code,
            elapsed_ms,
        )
    return response


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
if settings.STORAGE_BACKEND.lower() not in ("s3", "cloudinary"):
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Serve locally-stored quiz images (UUID-named PNGs from data/assets/images)
_data_images_dir = Path("data/assets/images")
if _data_images_dir.exists():
    app.mount("/data-assets/images", StaticFiles(directory=str(_data_images_dir)), name="data_images")

# ── Routers (mounted under /api to match frontend baseURL and Railway proxy) ──
api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(history.router)
api_router.include_router(mock_tests.router)
api_router.include_router(writing.router)
api_router.include_router(users.router)
api_router.include_router(placement.router)
api_router.include_router(practice.router)
api_router.include_router(speaking_router.router)
api_router.include_router(vocabulary_router)
api_router.include_router(annotations_router)
api_router.include_router(leaderboard_router)
api_router.include_router(shadowing_router)
api_router.include_router(admin.router)
api_router.include_router(mock_exams_router)
api_router.include_router(translation_router)
api_router.include_router(pronunciation_router)
api_router.include_router(conversation_router)
api_router.include_router(forecast_router)
app.include_router(api_router)

if settings.METRICS_ENABLED:
    from app.core.metrics import metrics_endpoint

    app.add_api_route("/metrics", metrics_endpoint, methods=["GET"], tags=["Metrics"])


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """Liveness probe with DB and Redis checks."""
    checks = {"status": "ok", "app": settings.APP_NAME, "db": "ok", "redis": "skipped"}
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        checks["db"] = "error"
        checks["status"] = "degraded"

    if settings.redis_required or settings.CELERY_ENABLED:
        checks["redis"] = "ok"
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
    if asset.public_url and asset.source in ("s3", "cloudinary"):
        return RedirectResponse(asset.public_url, status_code=302)
    return FileResponse(
        str(asset.local_path),
        media_type=asset.content_type,
        headers={"Accept-Ranges": "bytes"},
    )


_IMAGE_PLACEHOLDER_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="180" viewBox="0 0 320 180">'
    '<rect width="320" height="180" fill="#1f1f1f"/>'
    '<rect x="1" y="1" width="318" height="178" fill="none" stroke="#4d4d4d"/>'
    '<text x="160" y="92" text-anchor="middle" fill="#b3b3b3" font-family="sans-serif" font-size="13">'
    'No image</text></svg>'
)


@app.get("/images/{file_id}", tags=["Images"])
async def serve_image(file_id: str):
    """Serve quiz thumbnail — redirect to S3/CDN or local file."""
    from app.core.media_assets import resolve_image

    asset = resolve_image(file_id)
    if not asset:
        return Response(
            content=_IMAGE_PLACEHOLDER_SVG,
            media_type="image/svg+xml",
            headers={"Cache-Control": "public, max-age=300"},
        )
    if asset.public_url and asset.source in ("s3", "cloudinary"):
        return RedirectResponse(asset.public_url, status_code=302)
    return FileResponse(
        str(asset.local_path),
        media_type=asset.content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )


# Same handlers under /api/* for frontend nginx proxy (VITE_AUDIO_CDN_BASE=/api/audio).
app.add_api_route("/api/audio/{file_id}", serve_audio, methods=["GET"], tags=["Audio"])
app.add_api_route("/api/images/{file_id}", serve_image, methods=["GET"], tags=["Images"])
