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
