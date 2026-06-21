FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements-core.txt requirements-ml.txt ./
RUN pip install --no-cache-dir -r requirements-core.txt -r requirements-ml.txt gunicorn

COPY . .

RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "exec gunicorn app.main:app -w ${WEB_CONCURRENCY:-2} -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout ${GUNICORN_TIMEOUT:-300} --access-logfile -"]
