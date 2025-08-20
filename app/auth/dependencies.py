from fastapi import Request, Header, Depends, HTTPException
from app.auth.clerk_auth import verify_user
import structlog

logger = structlog.get_logger()

async def get_current_user_id(
    request: Request,
    authorization: str = Header(None)
) -> str:
    logger.debug("Inside get_current_user_id")
    # Step 1: If the middleware already set user_id (e.g. M2M), use it
    if hasattr(request.state, "user_id") and request.state.user_id:
        return request.state.user_id

    # Step 2: Otherwise, use standard Clerk verification
    if authorization is None:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    return await verify_user(authorization=authorization)

async def require_internal_service(request: Request):
    if getattr(request.state, "auth_type", None) != "internal":
        raise HTTPException(status_code=403, detail="Only internal services may access this route")
    return request.state.service_id