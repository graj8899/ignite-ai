import uuid

from fastapi.testclient import TestClient

from app.observability.request_id import REQUEST_ID_HEADER


def test_health_returns_200_and_json(client: TestClient):
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "env" in body


def test_request_id_generated_when_absent(client: TestClient):
    response = client.get("/api/health")

    request_id = response.headers.get(REQUEST_ID_HEADER)
    assert request_id is not None
    # Must be a valid UUID4 string.
    assert uuid.UUID(request_id).version == 4


def test_request_id_echoed_when_provided(client: TestClient):
    supplied = "test-request-id-123"

    response = client.get("/api/health", headers={REQUEST_ID_HEADER: supplied})

    assert response.headers.get(REQUEST_ID_HEADER) == supplied
