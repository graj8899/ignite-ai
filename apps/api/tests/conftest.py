"""Shared test fixtures.

Tests must not depend on the repo's real .env: `client` builds the app and
overrides get_settings with fixed, explicit values (which take priority over
any env var or .env file in pydantic-settings), so the whole suite passes
even on a machine with no .env present.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import create_app


def _test_settings() -> Settings:
    return Settings(
        openai_api_key="test-openai-key",
        auth_secret="test-auth-secret",
        database_url="postgresql://test:test@localhost/test",
        openai_model="test-model",
        embedding_model="test-embedding-model",
    )


@pytest.fixture
def app() -> FastAPI:
    """A fresh app with settings overridden. Tests may add further
    dependency_overrides (e.g. get_db) before building a client from it."""
    fastapi_app = create_app()
    fastapi_app.dependency_overrides[get_settings] = _test_settings
    return fastapi_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)
