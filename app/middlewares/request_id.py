"""
Middleware for adding request IDs to logs.
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import structlog

class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware for adding request IDs to logs."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = structlog.contextvars.get_contextvars().get("request_id")
        return response
