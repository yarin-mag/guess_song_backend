import json
import logging
import os
from fastapi import APIRouter, Request, HTTPException, Header
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from app.shared.http import call_internal_service
import httpx
from datetime import datetime, timedelta
from app.users.model import get_user_by_id, update_user_fields

router = APIRouter()

PAYPAL_WEBHOOK_ID = os.getenv("PAYPAL_WEBHOOK_ID")


async def verify_paypal_signature(request: Request, headers: dict) -> bool:
    """
    Verifies the PayPal webhook signature.
    """
    try:
        transmission_id = headers.get("paypal-transmission-id")
        transmission_time = headers.get("paypal-transmission-time")
        cert_url = headers.get("paypal-cert-url")
        auth_algo = headers.get("paypal-auth-algo")
        transmission_sig = headers.get("paypal-transmission-sig")
        webhook_id = PAYPAL_WEBHOOK_ID

        if not all([transmission_id, transmission_time, cert_url, auth_algo, transmission_sig, webhook_id]):
            logging.error("Missing PayPal headers for verification.")
            return False

        # Fetch the public key certificate from PayPal
        async with httpx.AsyncClient() as client:
            response = await client.get(cert_url)
            response.raise_for_status()

        cert_pem = response.text
        cert = x509.load_pem_x509_certificate(cert_pem.encode("utf-8"))
        public_key = cert.public_key()

        # Construct the expected signature
        body = await request.body()
        expected_signature_base = f"{transmission_id}|{transmission_time}|{webhook_id}|{body.decode('utf-8')}"

        # Verify the signature
        public_key.verify(
            bytes.fromhex(transmission_sig),
            expected_signature_base.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        # Additionally, you might want to check the certificate chain and subject.
        # For this example, we are trusting the certificate from the URL.

        return True
    except Exception as e:
        logging.error(f"Error verifying PayPal signature: {e}")
        return False


@router.post("/paypal-webhook")
async def paypal_webhook(request: Request):
    """
    Handles webhooks from PayPal.
    """
    headers = dict(request.headers)

    # Temporarily disable verification for local testing if needed
    # if os.getenv("IS_RUNNING_LOCAL") == "true":
    #     is_verified = True
    # else:
    is_verified = await verify_paypal_signature(request, headers)

    if not is_verified:
        raise HTTPException(
            status_code=400, detail="Webhook signature verification failed.")

    body = await request.body()
    event = json.loads(body)

    if event["event_type"] == "BILLING.SUBSCRIPTION.CREATED":
        resource = event.get("resource", {})
        subscription_id = resource.get("id")
        user_id = resource.get("custom_id")

        if not user_id:
            logging.error(
                "Received subscription event without custom_id (user_id).")
            raise HTTPException(
                status_code=400, detail="User ID not found in webhook payload.")
        if not subscription_id:
            logging.error(
                "Received subscription event without id (subscription_id).")
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

        logging.info(f"User {user_id} subscribed successfully.")
    elif event["event_type"] == "BILLING.SUBSCRIPTION.CANCELLED":
        resource = event.get("resource", {})
        user_id = resource.get("custom_id")

        if not user_id:
            logging.error("Cancellation event missing user ID")
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

        logging.info(f"User {user_id} subscription cancelled.")

    return {"status": "success"}
