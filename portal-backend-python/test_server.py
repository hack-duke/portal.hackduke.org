from fastapi.testclient import TestClient
from server import app

client = TestClient(app)


class TestServer:
    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"message": "OK"}

    def test_legacy_application_and_admin_routes_remain_available(self):
        paths = app.openapi()["paths"]
        for prefix in ("/application", "/check_in", "/admin", "/roles"):
            assert any(path.startswith(prefix) for path in paths)

    def test_archived_event_endpoints_are_not_served(self):
        assert not any(path.startswith("/events") for path in app.openapi()["paths"])
        assert client.get("/events/duquantum-2026").status_code == 404
