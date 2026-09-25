import logging
from typing import Literal

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import get_db
from app.observability.request_id import get_request_id

logger = logging.getLogger(__name__)

router = APIRouter()

_VECTOR_EXTENSION_CHECK = text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]


@router.get("/api/readiness", response_model=ReadinessResponse)
def readiness(response: Response, db: Session = Depends(get_db)) -> ReadinessResponse:
    try:
        db.execute(text("SELECT 1"))
        vector_installed = db.execute(_VECTOR_EXTENSION_CHECK).first() is not None
        if not vector_installed:
            raise RuntimeError("pgvector extension is not installed")
    except (SQLAlchemyError, RuntimeError) as exc:
        logger.error(
            "readiness check failed request_id=%s error=%s",
            get_request_id(),
            exc,
        )
        response.status_code = 503
        return ReadinessResponse(status="not_ready")

    return ReadinessResponse(status="ready")
