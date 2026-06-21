FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Layer 1: PyTorch CPU-only (~200 MB instead of ~2.5 GB CUDA) ──────────────
RUN pip install --no-cache-dir \
    torch torchaudio \
    --extra-index-url https://download.pytorch.org/whl/cpu

# ── Layer 2: Core web/API deps (changes rarely → cached) ─────────────────────
COPY requirements-core.txt .
RUN pip install --no-cache-dir -r requirements-core.txt

# ── Layer 3: ML deps (depends on PyTorch already installed) ───────────────────
COPY requirements-ml.txt .
RUN pip install --no-cache-dir -r requirements-ml.txt

COPY . .

RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

CMD ["gunicorn", "app.main:app", \
     "-w", "4", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--access-logfile", "-"]
