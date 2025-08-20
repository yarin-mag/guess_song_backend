from starlette.middleware.base import BaseHTTPMiddleware
import time
import structlog

logger = structlog.get_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        actor = self.get_actor(request)

        if request.method != 'OPTIONS':
            logger.info(
                "Request Start",
                method=request.method,
                url=str(request.url),
                actor=actor
            )

        try:
            response = await call_next(request)
            duration = round(time.time() - start, 3)

            if request.method != 'OPTIONS':
                logger.info(
                    "Request End",
                    method=request.method,
                    url=str(request.url),
                    duration=duration,
                    actor=actor
                )
            return response

        except Exception as e:
            if request.method != 'OPTIONS':
                logger.error(
                    "Request Failed",
                    method=request.method,
                    url=str(request.url),
                    error=repr(e),
                    actor=actor
                )
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
