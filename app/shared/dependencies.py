from fastapi import Request, HTTPException, Depends

def get_current_user(allow_unauthenticated: bool = False):
    def dependency(request: Request):
        user_id = getattr(request.state, "user_id", None)
        if allow_unauthenticated and not user_id:
            user_id = ''
        elif not user_id:
            raise HTTPException(
                status_code=401, detail="Unauthorized: no user in request"
            )

        return {"user_id": user_id} if user_id else None

    return dependency

def get_internal_service_user():
    def dependency(request: Request):
        auth_type = getattr(request.state, "auth_type", None)
        if auth_type != 'internal':
            raise HTTPException(
                status_code=403, detail="Forbidden: internal service access only"
            )
        
        service_id = getattr(request.state, "service_id", "unknown")
        user_id = getattr(request.state, "user_id", None) # Impersonated user

        return {"service_id": service_id, "user_id": user_id}

    return dependency