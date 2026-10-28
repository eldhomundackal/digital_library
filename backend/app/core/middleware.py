import logging
import time

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Captures request context (IP, user-agent) into request.state.
    Does NOT write audit logs — service methods call audit_action().
    """

    async def dispatch(self, request: Request, call_next):
        """Store IP address and user agent on request state for audit logging."""
        request.state.ip_address = (
            request.client.host if request.client else "unknown"
        )
        request.state.user_agent = request.headers.get("User-Agent", "")
        response = await call_next(request)
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs method, path, status code, and response time for every request."""

    async def dispatch(self, request: Request, call_next):
        """Log each request with its duration in milliseconds."""
        start = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000
        logger.info(
            "%s %s %s %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catches all unhandled exceptions and formats them as ErrorResponse.
    HTTPException passes through with its own status code; all others return 500.
    """
    from fastapi import HTTPException

    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "message": exc.detail},
        )
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error"},
    )
