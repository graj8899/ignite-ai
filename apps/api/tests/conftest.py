"""Shared test fixtures.

Tests must not depend on the repo's real .env: `client` builds the app and
overrides get_settings with fixed, explicit values (which take priority over
any env var or .env file in pydantic-settings), so the whole suite passes
even on a machine with no .env present.
"""

import pytest
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
def client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_settings] = _test_settings
    return TestClient(app)
