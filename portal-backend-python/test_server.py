from fastapi.testclient import TestClient
from server import app

client = TestClient(app)


class TestServer:
    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"message": "OK"}
