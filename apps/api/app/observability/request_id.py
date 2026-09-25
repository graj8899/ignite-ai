"""Request-ID middleware.

Every request gets a request_id: the incoming X-Request-ID header if the
caller supplied one *and* it looks safe, otherwise a generated UUID4. It is
echoed back on the response and stashed in a ContextVar so logging can pick
it up without threading it through every function call.
"""

import re
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"

# Conservative allowlist: alphanumerics, dot, underscore, hyphen, 1-64 chars.
# Rejects anything that could carry control characters (e.g. CRLF), be used
# for header/log injection, or grow unbounded.
_VALID_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Return the current request's ID, for use in logging."""
    return _request_id_ctx.get()


def is_valid_request_id(value: str) -> bool:
    """Whether an incoming X-Request-ID value is safe to trust and echo back."""
    return bool(_VALID_REQUEST_ID_RE.fullmatch(value))


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming = request.headers.get(REQUEST_ID_HEADER)
        request_id = incoming if incoming and is_valid_request_id(incoming) else str(uuid.uuid4())
        token = _request_id_ctx.set(request_id)
        try:
            response = await call_next(request)
        finally:
            _request_id_ctx.reset(token)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
