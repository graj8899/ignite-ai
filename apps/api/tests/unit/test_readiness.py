from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db import get_db


def _failing_db():
    session = MagicMock()
    session.execute.side_effect = OperationalError(
        "connect failed", None, Exception("no route to host")
    )
    yield session


def test_readiness_returns_503_when_db_unreachable(app: FastAPI):
    app.dependency_overrides[get_db] = _failing_db
    client = TestClient(app)

    response = client.get("/api/readiness")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}
