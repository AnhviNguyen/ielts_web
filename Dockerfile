FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Layer 1: PyTorch CPU-only (~200 MB instead of ~2.5 GB CUDA) ──────────────
RUN pip install --no-cache-dir \
    torch torchaudio \
    --extra-index-url https://download.pytorch.org/whl/cpu

# ── Layer 2: Core web/API deps (changes rarely → cached) ─────────────────────
COPY backend/requirements-core.txt ./requirements-core.txt
RUN pip install --no-cache-dir -r requirements-core.txt

# ── Layer 3: ML deps (depends on PyTorch already installed) ───────────────────
COPY backend/requirements-ml.txt ./requirements-ml.txt
RUN pip install --no-cache-dir -r requirements-ml.txt

# ── Layer 4: Application code ────────────────────────────────────────────────
COPY backend/alembic.ini ./alembic.ini
COPY backend/alembic ./alembic
COPY backend/app ./app
COPY backend/ml ./ml
COPY backend/data ./data

RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 7860

CMD ["sh", "-c", "exec gunicorn app.main:app -w ${WEB_CONCURRENCY:-2} -k uvicorn.workers.UvicornWorker --bind [::]:7860 --timeout 300 --access-logfile -"]
