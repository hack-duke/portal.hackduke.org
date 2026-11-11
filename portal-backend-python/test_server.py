import pytest
from httpx2 import ASGITransport, AsyncClient

from server import app

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"message": "OK"}

def test_legacy_application_and_admin_routes_remain_available():
    paths = app.openapi()["paths"]
    for prefix in ("/application", "/check_in", "/admin", "/roles"):
        assert any(path.startswith(prefix) for path in paths)

@pytest.mark.asyncio
async def test_archived_event_endpoints_are_not_served():
    assert not any(path.startswith("/events") for path in app.openapi()["paths"])
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/events/duquantum-2026")
        assert response.status_code == 404
