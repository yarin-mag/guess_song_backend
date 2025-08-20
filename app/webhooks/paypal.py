import json
import structlog
import os

logger = structlog.get_logger()
from fastapi import APIRouter, Request, HTTPException, Header
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from app.shared.http import call_internal_service
import base64, zlib, httpx
from datetime import datetime, timedelta
from app.users.model import get_user_by_id, update_user_fields

router = APIRouter()

PAYPAL_WEBHOOK_ID = os.getenv("PAYPAL_WEBHOOK_ID")


async def verify_paypal_signature(raw_body: bytes, headers: dict, webhook_id: str) -> bool:
    """
    Self-verifies a PayPal webhook using RSA/SHA256 over:
    transmissionId|timeStamp|webhookId|crc32(raw_body in decimal)
    """
    try:
        # Normalize header keys to lowercase once
        h = {k.lower(): v for k, v in headers.items()}

        transmission_id = h.get("paypal-transmission-id")
        transmission_time = h.get("paypal-transmission-time")
        cert_url        = h.get("paypal-cert-url")
        auth_algo       = h.get("paypal-auth-algo")     # e.g., "SHA256withRSA"
        transmission_sig_b64 = h.get("paypal-transmission-sig")

        if not all([transmission_id, transmission_time, cert_url, auth_algo, transmission_sig_b64, webhook_id]):
            logger.error("Missing PayPal headers/webhook_id for verification")
            return False

        # Safety: only accept PayPal cert hosts
        if not (cert_url.startswith("https://api.paypal.com/") or cert_url.startswith("https://api.sandbox.paypal.com/")):
            logger.error("Bad cert_url host", cert_url=cert_url)
            return False

        # Compute CRC32 over the *raw* body bytes → decimal
        crc32_decimal = zlib.crc32(raw_body) & 0xFFFFFFFF
        message = f"{transmission_id}|{transmission_time}|{webhook_id}|{crc32_decimal}"

        # Fetch and parse the X.509 cert, extract public key
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(cert_url)
            resp.raise_for_status()
            cert_pem = resp.text
        cert = x509.load_pem_x509_certificate(cert_pem.encode("utf-8"))
        public_key = cert.public_key()

        # Base64-decode the signature from the header
        signature = base64.b64decode(transmission_sig_b64)

        # Use the algo from header. Today it's "SHA256withRSA".
        if "SHA256" in auth_algo.upper():
            digest = hashes.SHA256()
        else:
            logger.error("Unsupported auth_algo", auth_algo=auth_algo)
            return False

        public_key.verify(
            signature,
            message.encode("utf-8"),
            padding.PKCS1v15(),
            digest
        )
        return True

    except Exception as e:
        logger.exception("PayPal signature verification failed")
        return False


@router.post("/paypal-webhook")
async def paypal_webhook(request: Request):
    """
    Handles webhooks from PayPal.
    """
    headers = dict(request.headers)
    raw_body = await request.body()

    webhook_id = PAYPAL_WEBHOOK_ID
    is_verified = await verify_paypal_signature(raw_body, headers, webhook_id)

    if not is_verified:
        raise HTTPException(
            status_code=400, detail="Webhook signature verification failed.")

    body = await request.body()
    event = json.loads(raw_body.decode("utf-8"))

    if event["event_type"] == "BILLING.SUBSCRIPTION.CREATED":
        resource = event.get("resource", {})
        subscription_id = resource.get("id")
        user_id = resource.get("custom_id")

        if not user_id:
            logger.error("Received subscription event without custom_id (user_id).")
            raise HTTPException(
                status_code=400, detail="User ID not found in webhook payload.")
        if not subscription_id:
            logger.error("Received subscription event without id (subscription_id).")
            raise HTTPException(
                status_code=400, detail="Subscription ID not found in webhook payload.")
            
        user = await call_internal_service("/users", "GET", None, {"user_id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        billing_info = resource.get("billing_info", {})
        last_payment = billing_info.get("last_payment", {})

        if not hasattr(user, 'payment_history') or user.payment_history is None:
            user.payment_history = []

        user.payment_history.append({
            "payment_id": event.get("id"),
            "create_time": event.get("create_time"),
            "amount": float(last_payment.get("amount", 0.0)),
            "currency": last_payment.get("currency_code")
        })

        await call_internal_service(
            "/users",
            "PUT",
            {
                **user,
                "is_subscribed": True,
                "subscription_start_date": event.get("create_time"),
                "subscription_end_date_net": None,
                "subscription_end_date_gross": None,
                "subscription_id": subscription_id,
                "monthly_payment": float(last_payment.get("amount", 0.0)),
                "payment_history": user.payment_history
            },
            {"user_id": user_id}
        )

        logger.info("User subscribed successfully", user_id=user_id)
    elif event["event_type"] == "BILLING.SUBSCRIPTION.CANCELLED":
        resource = event.get("resource", {})
        user_id = resource.get("custom_id")

        if not user_id:
            logger.error("Cancellation event missing user ID")
            raise HTTPException(status_code=400, detail="Missing user ID")
        
        today = datetime.utcnow().date()
        subscription_end_gross = (today + timedelta(days=30)).isoformat()
        today_iso = today.isoformat()
        
        await call_internal_service(
            "/users",
            "PUT",
            {
                "is_subscribed": False,
                "subscription_end_date_net": today_iso,
                "subscription_end_date_gross": subscription_end_gross,
                "subscription_id": None
            },
            {"user_id": user_id}
        )

        logger.info("User subscription cancelled", user_id=user_id)

    return {"status": "success"}
