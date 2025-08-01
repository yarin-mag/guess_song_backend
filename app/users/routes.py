from fastapi import APIRouter, Depends
from app.auth.clerk_auth import verify_user
from app.auth.dependencies import get_current_user_id, require_internal_service
from app.users.service import get_or_create_user, update_user_data, cancel_subscription, agree_to_terms_and_conditions
from app.users.repository import UserUpdateRequest, UserResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/cancel-subscription")
async def cancel_subscription_route(user_id: str = Depends(get_current_user_id)):
    return await cancel_subscription(user_id)

@router.post("/agree-to-terms-and-conditions")
async def agree_to_terms_and_conditions_route(user_id: str = Depends(get_current_user_id)):
    return await agree_to_terms_and_conditions(user_id)

@router.get("", response_model=UserResponse)
async def get(user_id: str = Depends(get_current_user_id)):
    return await get_or_create_user(user_id)

@router.put("", response_model=UserResponse)
async def update(update_req: UserUpdateRequest, user_id: str = Depends(get_current_user_id),  _ = Depends(require_internal_service)):
    return await update_user_data(user_id, update_req)