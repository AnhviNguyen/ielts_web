import pytest
from fastapi import status

pytestmark = pytest.mark.integration


async def test_health_check_success(client):
    """Test health check route returns OK or degraded status."""
    response = await client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert data["status"] in ("ok", "degraded")


async def test_security_headers_present(client):
    """Test response contains mandatory security headers."""
    response = await client.get("/health")
    headers = response.headers
    
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
