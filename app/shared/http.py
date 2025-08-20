import httpx
import os
from typing import Optional, Dict, Any
import jwt
import uuid
import time
from dotenv import load_dotenv
from app.shared.exceptions import InternalJWTExpiredException, InvalidInternalJWTException
from fastapi import HTTPException

load_dotenv()

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8000")
INTERNAL_KEY = os.getenv("INTERNAL_API_KEY", "super-secret-key")
MICRO_JWT_SECRET = os.getenv("MICRO_JWT_SECRET", "micro-jwt-secret")
MICRO_JWT_ALGORITHM = "HS256"
IS_RUNNING_LOCAL = os.getenv("IS_RUNNING_LOCAL") == "true"


def sign_internal_jwt(payload: Optional[Dict[str, Any]] = None, expires_in: int = 300) -> str:
    """
    Sign a JWT for internal microservice communication.
    :param payload: Custom payload to include in the JWT.
    :param expires_in: Expiration time in seconds.
    :return: JWT as string.
    """
    now = int(time.time())
    data = {
        "iat": now,
        "exp": now + expires_in,
        **(payload or {})
    }
    token = jwt.encode(data, MICRO_JWT_SECRET, algorithm=MICRO_JWT_ALGORITHM)
    # PyJWT >= 2.0 returns str, <2.0 returns bytes
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def verify_internal_jwt(token: str) -> Dict[str, Any]:
    """
    Verify a JWT for internal microservice communication.
    :param token: JWT as string.
    :return: Decoded payload if valid, raises jwt exceptions if invalid.
    """
    try:
        payload = jwt.decode(token, MICRO_JWT_SECRET, algorithms=[MICRO_JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise InternalJWTExpiredException()
    except jwt.InvalidTokenError:
        raise InvalidInternalJWTException()


async def call_internal_service(
    service_url: str,
    method: str = "GET",
    body: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
) -> Any:
    full_url = f"{USER_SERVICE_URL}{service_url}"
    trace_id = str(uuid.uuid4())
    internal_jwt = sign_internal_jwt({ **(body or {}), **(params or {}) })
    request_headers = {
        "x-trace-id": trace_id,
        "x-internal-key": INTERNAL_KEY,
        "x-internal-jwt": internal_jwt,
        **(headers or {})
    }

    timeout = httpx.Timeout(300.0 if IS_RUNNING_LOCAL else 20.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.request(
            method=method.upper(),
            url=full_url,
            headers=request_headers,
            json=body if method.upper() in {"POST", "PUT", "PATCH"} else None,
            params=params
        )

        if response.status_code >= 400:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to call {method.upper()} {service_url}: {response.text}"
            )

        return response.json()
