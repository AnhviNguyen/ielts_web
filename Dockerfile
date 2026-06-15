FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY backend/alembic.ini ./alembic.ini
COPY backend/alembic ./alembic
COPY backend/app ./app
COPY backend/ml ./ml
COPY backend/model ./model
COPY backend/data ./data

RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 7860

CMD ["sh", "-c", "exec gunicorn app.main:app -w ${WEB_CONCURRENCY:-2} -k uvicorn.workers.UvicornWorker --bind [::]:7860 --timeout 300 --access-logfile -"]
