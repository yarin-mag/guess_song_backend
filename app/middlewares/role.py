from fastapi import Header, HTTPException
import os

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "super-secret-key")

async def require_internal_key(x_internal_key: str = Header(..., alias="x-internal-key")):
    if x_internal_key != INTERNAL_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid internal key")


# async def require_admin(x_user_role: str = Header(None, alias="x-user-role")):
#     if x_user_role != "admin":
#         raise HTTPException(status_code=403, detail="Admin access required")
