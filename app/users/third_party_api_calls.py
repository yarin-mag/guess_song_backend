from fastapi import HTTPException
import httpx
import os
from app.shared.clerk import fetch_clerk_user_data

from dotenv import load_dotenv
load_dotenv()

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_API_BASE = "https://api-m.sandbox.paypal.com" if os.getenv(
    "ENV") != "prod" else "https://api-m.paypal.com"


async def get_paypal_access_token():
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{PAYPAL_API_BASE}/v1/oauth2/token",
            data={"grant_type": "client_credentials"},
            auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
            headers={"Accept": "application/json"}
        )
        res.raise_for_status()
        return res.json()["access_token"]


async def cancel_paypal_subscription(subscription_id: str, access_token: str):
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{PAYPAL_API_BASE}/v1/billing/subscriptions/{subscription_id}/cancel",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json={"reason": "User cancelled via app"}
        )
        if res.status_code not in (204, 202):
            try:
                error = res.json()
            except Exception:
                error = res.text
            raise HTTPException(
                status_code=500, detail=f"Failed to cancel subscription: {error}")

    return {"status": "cancelled"}


async def fetch_clerk_user(user_id: str):
    return await fetch_clerk_user_data(user_id)