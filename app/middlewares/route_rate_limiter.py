from fastapi import Request, HTTPException
from functools import wraps
import time

# In-memory tracking per-user per-endpoint
_request_store = {}

def rate_limited(limit: int = 10, window: int = 60):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            user_id = getattr(request.state, "user_id", request.client.host)

            key = f"{user_id}:{request.url.path}"
            now = time.time()
            timestamps = _request_store.get(key, [])
            timestamps = [ts for ts in timestamps if now - ts < window]

            if len(timestamps) >= limit:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")

            timestamps.append(now)
            _request_store[key] = timestamps

            return await func(*args, **kwargs)
        return wrapper
    return decorator
