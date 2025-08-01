from fastapi import APIRouter
from app.webhooks.paypal import router as paypal_router

router = APIRouter(prefix="/webhooks")

router.include_router(paypal_router)
