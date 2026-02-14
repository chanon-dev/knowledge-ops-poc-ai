"""Stripe webhook handler endpoint."""

import logging

from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.api.deps import get_db
from app.core.config import settings
from app.services.stripe_service import StripeService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle incoming Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    try:
        import stripe
        webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Signature verification failed: {e}")

    service = StripeService(db, api_key=getattr(settings, "STRIPE_SECRET_KEY", None))
    await service.handle_webhook_event(event["type"], event["data"])

    return {"status": "ok"}
