"""Integration test: readiness against a real Postgres.

Unlike the unit tests, this test intentionally does NOT override settings or
get_db — it exercises app.main + app.db + app.config exactly as they run in
production, against the database from the real .env (e.g. the local
docker-compose Postgres). It is skipped automatically when that database is
unreachable, so `pytest` still passes on a machine with no DB running; run
it explicitly with `pytest -m integration` when Postgres is up.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import get_engine
from app.main import create_app

pytestmark = pytest.mark.integration


@pytest.fixture
def real_client() -> TestClient:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        pytest.skip(f"database unreachable, skipping integration test: {exc}")

    return TestClient(create_app())


def test_readiness_is_ready_against_real_postgres(real_client: TestClient):
    response = real_client.get("/api/readiness")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
