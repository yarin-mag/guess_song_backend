from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from starlette.responses import JSONResponse
import time
from app.shared.logger import log_info, log_error

# In-memory store {key: [timestamps]}
_rate_limit_store = {}

class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 10, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        try:
            # Skip for internal service calls
            if request.headers.get("x-internal-jwt"):
                return await call_next(request)

            identifier = (
                getattr(request.state, "user_id", None)
                or request.client.host
                or "unknown"
            )

            now = time.time()
            request_times = _rate_limit_store.get(identifier, [])

            request_times = [ts for ts in request_times if now - ts < self.window_seconds]

            if len(request_times) >= self.max_requests:
                log_info(f"⛔ Rate limit hit for: {identifier}")
                return JSONResponse(
                    status_code=429,
                    content={"detail": f"Rate limit exceeded. Try again later."},
                )

            request_times.append(now)
            _rate_limit_store[identifier] = request_times

            return await call_next(request)

        except Exception as e:
            log_error(f"[RateLimiterMiddleware] Error: {repr(e)}")
            return JSONResponse(status_code=500, content={"detail": "Internal error"})
