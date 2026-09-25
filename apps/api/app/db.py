"""Database engine, session factory, and FastAPI session dependency.

The engine is built lazily (only when first requested, via lru_cache) so
that importing this module — or app.main — never reads settings or opens a
connection. Tests override get_db() instead of touching the real database.
"""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},
    )


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session]:
    """FastAPI dependency: yields a Session, closes it after the request."""
    session = get_sessionmaker()()
    try:
        yield session
    finally:
        session.close()
