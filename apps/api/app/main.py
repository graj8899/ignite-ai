from fastapi import FastAPI

from app.observability.request_id import RequestIDMiddleware
from app.routes.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(title="Ignite RAG API")

    app.add_middleware(RequestIDMiddleware)

    app.include_router(health_router)

    return app


app = create_app()
