import httpx
from fastapi import HTTPException, Header
from dotenv import load_dotenv
import os

load_dotenv()
CLERK_API_KEY = os.getenv("CLERK_SECRET_KEY")

async def verify_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")

    token = authorization.split(" ")[1]

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.clerk.dev/v1/me",
            headers={
                "Authorization": f"Bearer {token}",
                "Clerk-Secret-Key": CLERK_API_KEY,
            }
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Authentication failed")

        user_data = resp.json()
        return user_data["id"]
