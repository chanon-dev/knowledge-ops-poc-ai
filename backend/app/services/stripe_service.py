"""Stripe integration service for billing."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import Subscription, Invoice

logger = logging.getLogger(__name__)


class StripeService:
    """Handles Stripe customer, subscription, and webhook operations."""

    def __init__(self, db: AsyncSession, api_key: str | None = None):
        self.db = db
        self._api_key = api_key

    def _get_stripe(self):
        import stripe
        if self._api_key:
            stripe.api_key = self._api_key
        return stripe

    async def create_customer(self, tenant_id: UUID, email: str, name: str) -> str:
        stripe = self._get_stripe()
        customer = stripe.Customer.create(email=email, name=name, metadata={"tenant_id": str(tenant_id)})

        result = await self.db.execute(select(Subscription).where(Subscription.tenant_id == tenant_id))
        sub = result.scalar_one_or_none()
        if sub:
            sub.stripe_customer_id = customer.id
            await self.db.commit()

        return customer.id

    async def create_subscription(self, tenant_id: UUID, price_id: str, payment_method_id: str | None = None) -> dict:
        stripe = self._get_stripe()

        result = await self.db.execute(select(Subscription).where(Subscription.tenant_id == tenant_id))
        sub = result.scalar_one_or_none()
        if not sub or not sub.stripe_customer_id:
            raise ValueError("Customer not found. Create customer first.")

        if payment_method_id:
            stripe.PaymentMethod.attach(payment_method_id, customer=sub.stripe_customer_id)
            stripe.Customer.modify(
                sub.stripe_customer_id,
                invoice_settings={"default_payment_method": payment_method_id},
            )

        stripe_sub = stripe.Subscription.create(
            customer=sub.stripe_customer_id,
            items=[{"price": price_id}],
            metadata={"tenant_id": str(tenant_id)},
        )

        sub.stripe_subscription_id = stripe_sub.id
        sub.status = "active"
        await self.db.commit()

        return {"subscription_id": stripe_sub.id, "status": stripe_sub.status}

    async def cancel_subscription(self, tenant_id: UUID) -> bool:
        stripe = self._get_stripe()
        result = await self.db.execute(select(Subscription).where(Subscription.tenant_id == tenant_id))
        sub = result.scalar_one_or_none()
        if not sub or not sub.stripe_subscription_id:
            return False

        stripe.Subscription.modify(sub.stripe_subscription_id, cancel_at_period_end=True)
        sub.status = "cancelled"
        await self.db.commit()
        return True

    async def handle_webhook_event(self, event_type: str, event_data: dict):
        handlers = {
            "invoice.paid": self._handle_invoice_paid,
            "invoice.payment_failed": self._handle_payment_failed,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "customer.subscription.updated": self._handle_subscription_updated,
        }
        handler = handlers.get(event_type)
        if handler:
            await handler(event_data)
        else:
            logger.info(f"Unhandled Stripe event: {event_type}")

    async def _handle_invoice_paid(self, data: dict):
        stripe_invoice = data.get("object", {})
        customer_id = stripe_invoice.get("customer")
        result = await self.db.execute(
            select(Subscription).where(Subscription.stripe_customer_id == customer_id)
        )
        sub = result.scalar_one_or_none()
        if not sub:
            return

        invoice = Invoice(
            tenant_id=sub.tenant_id,
            stripe_invoice_id=stripe_invoice.get("id"),
            amount_cents=stripe_invoice.get("amount_paid", 0),
            currency=stripe_invoice.get("currency", "usd"),
            status="paid",
            pdf_url=stripe_invoice.get("invoice_pdf"),
        )
        self.db.add(invoice)
        await self.db.commit()
        logger.info(f"Invoice recorded for tenant {sub.tenant_id}")

    async def _handle_payment_failed(self, data: dict):
        customer_id = data.get("object", {}).get("customer")
        result = await self.db.execute(
            select(Subscription).where(Subscription.stripe_customer_id == customer_id)
        )
        sub = result.scalar_one_or_none()
        if sub:
            sub.status = "past_due"
            await self.db.commit()
            logger.warning(f"Payment failed for tenant {sub.tenant_id}")

    async def _handle_subscription_deleted(self, data: dict):
        stripe_sub_id = data.get("object", {}).get("id")
        result = await self.db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
        )
        sub = result.scalar_one_or_none()
        if sub:
            sub.status = "cancelled"
            sub.plan_tier = "free"
            await self.db.commit()
            logger.info(f"Subscription cancelled for tenant {sub.tenant_id}")

    async def _handle_subscription_updated(self, data: dict):
        stripe_sub = data.get("object", {})
        stripe_sub_id = stripe_sub.get("id")
        result = await self.db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
        )
        sub = result.scalar_one_or_none()
        if sub:
            sub.status = stripe_sub.get("status", sub.status)
            await self.db.commit()

    async def report_usage(self, tenant_id: UUID, quantity: int):
        """Report metered usage to Stripe."""
        stripe = self._get_stripe()
        result = await self.db.execute(select(Subscription).where(Subscription.tenant_id == tenant_id))
        sub = result.scalar_one_or_none()
        if not sub or not sub.stripe_subscription_id:
            return

        stripe_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)
        if stripe_sub.get("items", {}).get("data"):
            si_id = stripe_sub["items"]["data"][0]["id"]
            stripe.SubscriptionItem.create_usage_record(si_id, quantity=quantity, action="increment")
