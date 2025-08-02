from datetime import datetime
from firebase.firebase import get_firestore_client
from google.cloud import firestore
from app.users.repository import UserResponse
from app.users.consts import NEW_USER_DATA

db = get_firestore_client()
users_ref = db.collection("users")

async def get_user_by_id(user_id: str) -> UserResponse | None:
    doc = await users_ref.document(user_id).get()
    if not doc.exists:
        return None
    return UserResponse(**doc.to_dict())

async def create_user(user_id: str, user_data: dict) -> UserResponse:
    data = NEW_USER_DATA.copy()
    data.update(user_data)
    data["id"] = user_id
    data["guesses"] = { datetime.utcnow().date().isoformat(): 0 }
    await users_ref.document(user_id).set(data)
    return UserResponse(**data)

async def update_user_fields(user_id: str, update_data: dict):
    await users_ref.document(user_id).update(update_data)