from app.users.model import get_user_by_id, create_user, update_user_fields
from app.users.repository import UserUpdateRequest, UserResponse
from google.cloud import firestore
from datetime import datetime
from .third_party_api_calls import get_paypal_access_token, cancel_paypal_subscription, fetch_clerk_user

async def get_or_create_user(user_id: str) -> UserResponse:
    user_doc = await get_user_by_id(user_id)
    if not user_doc:
        clerk_user_data = await fetch_clerk_user(user_id)
        email = None
        linked_to = None
        try:
            email = clerk_user_data.get("email_addresses", [])[0].get("email_address")
            linked_to = clerk_user_data.get("email_addresses", [])[0].get("verification", {}).get("strategy", "")
        except (IndexError, AttributeError):
            email = None
            linked_to = None
        user_data = {
            "email": email,
            "linked_to": linked_to,
            "first_name": clerk_user_data.get("first_name", ""),
            "last_name": clerk_user_data.get("last_name", ""),
        }
        return await create_user(user_id, user_data)
    return user_doc

async def update_user_data(user_id: str, update_req: UserUpdateRequest) -> UserResponse:
    user_doc = await get_user_by_id(user_id)
    if not user_doc:
        raise Exception("User not found!")
    await update_user_fields(user_id, update_req.dict(exclude_unset=True))
    return await get_user_by_id(user_id)

async def cancel_subscription(user_id: str):
    user_doc = await get_user_by_id(user_id)
    
    if not user_doc:
        raise Exception("User not found!")
    
    if user_doc.get('subscription_id') is None:
        raise Exception("User has no subscription_id on the document!")
    
    paypal_access_token = await get_paypal_access_token()
    return await cancel_paypal_subscription(access_token=paypal_access_token, subscription_id=user_doc.get('subscription_id'))
    
async def agree_to_terms_and_conditions(user_id: str):
    update_req = UserUpdateRequest(agree_to_conditions_and_terms=datetime.utcnow())
    return await update_user_data(user_id, update_req)
    