import os
from clerk_backend_api import Clerk
from clerk_backend_api.security import authenticate_request
from clerk_backend_api.security.types import AuthenticateRequestOptions
import httpx
from fastapi import HTTPException

import jwt
from jwt import PyJWKClient

CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY")

async def update_clerk_metadata(user_id: str, metadata: dict):
    """
    Updates the public metadata for a Clerk user.

    Args:
        user_id (str): The Clerk user ID.
        metadata (dict): Dictionary representing the public metadata to update.
                         Example: {"isPremium": True, "plan": "pro"}
    """
    api_key = CLERK_SECRET_KEY
    if not api_key:
        raise EnvironmentError(
            "CLERK_SECRET_KEY not found in environment variables.")

    url = f"https://api.clerk.dev/v1/users/{user_id}/metadata"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "public_metadata": metadata
    }

    async with httpx.AsyncClient() as client:
        response = await client.patch(url, json=data, headers=headers)

    if response.status_code < 200 or response.status_code >= 300:
        raise Exception(
            f"Failed to update metadata: {response.status_code}, {response.text}")

    return response.json()


async def fetch_clerk_user_data(user_id: str):
    """
    Fetch user from Clerk using their management API.
    """
    api_key = CLERK_SECRET_KEY
    if not api_key:
        raise EnvironmentError("CLERK_SECRET_KEY not found in environment.")

    url = f"https://api.clerk.dev/v1/users/{user_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
    if response.status_code < 200 or response.status_code >= 300:
        raise Exception(
            f"Failed to fetch user {user_id}: {response.status_code} {response.text}")

    return response.json()

AUTHORIZED_PARTIES = ["http://localhost:5173", "https://localhost:5173"]  # Or your actual frontend origins
CLERK_JWKS_URL = f"https://direct-reptile-68.clerk.accounts.dev/.well-known/jwks.json"
EXPECTED_ISSUER = f"https://direct-reptile-68.clerk.accounts.dev"
EXPECTED_AUDIENCE = "http://localhost:5173"  # Or your actual azp

async def verify_clerk_token(token: str):
    try:
        jwks_client = PyJWKClient(CLERK_JWKS_URL)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=EXPECTED_ISSUER
        )
        return payload

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid JWT: {str(e)}")