"""Request IDs and the safety net for unexpected errors."""

import logging
import uuid
from contextvars import ContextVar

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.errors import ErrorCode

logger = logging.getLogger("app.request")

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def _valid_uuid(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return str(uuid.UUID(value))
    except ValueError:
        return None


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        rid = _valid_uuid(request.headers.get("X-Request-ID")) or str(uuid.uuid4())
        token = request_id_var.set(rid)
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("unhandled_error", extra={"path": request.url.path})
            response = JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": ErrorCode.INTERNAL_ERROR,
                        "message": "Internal error",
                        "field": None,
                    }
                },
            )
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = rid
        return response
