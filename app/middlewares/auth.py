from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.shared.clerk import verify_clerk_token
from app.shared.logger import log_error
from app.shared.http import verify_internal_jwt
from .consts import UNPROTECTED_PATHS
import os

INTERNAL_KEY_HEADER = "x-internal-key"
INTERNAL_JWT_HEADER = "x-internal-jwt"
AUTHORIZATION_HEADER = "authorization"
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            if request.method == "OPTIONS":
                return await call_next(request)
            print("🧩 Request ID: ", id(request))
            print("request.url: ", request.url)
            # === 0. Bypass authentication for unprotected paths ===
            if any(request.url.path.startswith(p) for p in UNPROTECTED_PATHS):
                # Log user if present, but continue even if not
                auth_header = request.headers.get(AUTHORIZATION_HEADER)
                if auth_header and auth_header.lower().startswith("bearer "):
                    try:
                        token = auth_header.split(" ", 1)[1]
                        clerk_user = await verify_clerk_token(token)
                        request.state.auth_type = "user"
                        request.state.user_id = clerk_user.get("sub")
                        # request.state.user_role = clerk_user.get("public_metadata", {}).get("role", "user")
                    except Exception:
                        pass  # Ignore errors for optional auth
                return await call_next(request)

            # === 1. Internal Microservice via JWT ===
            internal_jwt = request.headers.get(INTERNAL_JWT_HEADER)
            if internal_jwt:
                payload = verify_internal_jwt(internal_jwt)
                request.state.auth_type = "internal"
                request.state.service_id = payload.get("service", "unknown")
                request.state.user_id = payload.get("impersonated_user_id", None) or payload.get("user_id", None)
                return await call_next(request)

            # === 2. Internal via static key ===
            if DEBUG_MODE:
                internal_key = request.headers.get(INTERNAL_KEY_HEADER)
                if internal_key == os.getenv("INTERNAL_API_KEY"):
                    request.state.auth_type = "internal"
                    request.state.service_id = "static-key"
                    request.state.user_id = request.headers.get("x-user-id")
                    return await call_next(request)

            # === 3. Clerk User JWT ===
            auth_header = request.headers.get(AUTHORIZATION_HEADER)
            if auth_header and auth_header.lower().startswith("bearer "):
                token = auth_header.split(" ", 1)[1]
                clerk_user = await verify_clerk_token(token)
                request.state.auth_type = "user"
                request.state.user_id = clerk_user.get("sub")
                request.state.clerk_user = clerk_user
                # request.state.user_role = clerk_user.get("public_metadata", {}).get("role", "user")
                return await call_next(request)

            raise HTTPException(status_code=401, detail="Unauthorized: missing valid credentials")

        except HTTPException as e:
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        except Exception as e:
            log_error(f"[AuthMiddleware] Unexpected error: {e}")
            return JSONResponse(status_code=500, content={"detail": "Internal server error"})
