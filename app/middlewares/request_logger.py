from starlette.middleware.base import BaseHTTPMiddleware
from app.shared.logger import log_info, log_error
import time


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        actor = self.get_actor(request)

        if request.method != 'OPTIONS':
            log_info(
                f"🔄 Request Start: {request.method} {request.url} | By: {actor}")

        try:
            response = await call_next(request)
            duration = round(time.time() - start, 3)

            if request.method != 'OPTIONS':
                log_info(
                    f"✅ Request End: {request.method} {request.url} | Duration: {duration}s | By: {actor}")
            return response

        except Exception as e:
            if request.method != 'OPTIONS':
                log_error(
                    f"❌ Request Failed: {request.method} {request.url} | Error: {repr(e)} | By: {actor}")
            raise

    def get_actor(self, request) -> str:
        # Try identifying the request initiator
        user_id = getattr(request.state, "user_id", None)
        service_id = getattr(request.state, "service_id", None)
        trace_id = getattr(request.state, "trace_id", None)

        if user_id:
            return f"user:{user_id}"
        elif service_id:
            return f"service:{service_id}"
        elif trace_id:
            return f"trace:{trace_id}"
        else:
            return "unknown"
