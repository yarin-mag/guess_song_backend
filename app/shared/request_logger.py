import time
from fastapi import Request
from app.shared.logger import log_info, log_error


class RequestLogger:
    def __init__(self):
        pass  # In the future: integrate Coralogix or some free tier metrics cloud provider.

    async def log_start(self, request: Request):
        request.state._start_time = time.time()
        log_info(f"🔄 Request Start: {request.method} {request.url}")

    async def log_end(self, request: Request):
        duration = round(time.time() - getattr(request.state,
                         "_start_time", time.time()), 3)
        log_info(
            f"✅ Request End: {request.method} {request.url} | Duration: {duration}s")

    async def log_failure(self, request: Request, error: Exception):
        log_error(
            f"❌ Request Failed: {request.method} {request.url} | Error: {repr(error)}")
