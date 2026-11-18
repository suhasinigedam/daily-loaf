"""Turn every known error into {"error": {"code", "message", "field"}}."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.errors import HTTP_STATUS, DomainError, ErrorCode


def _error(status: int, code: ErrorCode, message: str, field: str | None) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "field": field}},
    )


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return _error(HTTP_STATUS[exc.code], exc.code, exc.message, exc.field)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = exc.errors()
        first = errors[0] if errors else {}
        parts = [str(p) for p in first.get("loc", ()) if p not in ("body", "query", "path")]
        message = str(first.get("msg", "Invalid input"))
        return _error(422, ErrorCode.VALIDATION_ERROR, message, ".".join(parts) or None)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code in (404, 405):
            return _error(404, ErrorCode.NOT_FOUND, "Not found", None)
        return _error(exc.status_code, ErrorCode.INTERNAL_ERROR, "Request failed", None)
