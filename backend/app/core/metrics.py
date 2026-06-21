"""Prometheus metrics middleware and /metrics endpoint."""

from __future__ import annotations

import time

from fastapi import HTTPException, Request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
HTTP_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    if route is not None and getattr(route, "path", None):
        return route.path
    return request.url.path


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)
        start = time.perf_counter()
        response = await call_next(request)
        path = _route_template(request)
        status = str(response.status_code)
        HTTP_REQUESTS.labels(request.method, path, status).inc()
        HTTP_LATENCY.labels(request.method, path).observe(time.perf_counter() - start)
        return response


def _authorize_metrics(request: Request) -> None:
    token = (settings.METRICS_TOKEN or "").strip()
    if token:
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {token}":
            raise HTTPException(status_code=401, detail="Invalid metrics token")
        return
    if settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=503, detail="Metrics endpoint is not configured")


async def metrics_endpoint(request: Request) -> Response:
    _authorize_metrics(request)
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
