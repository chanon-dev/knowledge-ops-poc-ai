import hashlib
import hmac
import json
import secrets
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook import Webhook, WebhookDelivery


class WebhookService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_webhook(self, tenant_id: UUID, url: str, events: list[str]) -> Webhook:
        webhook = Webhook(
            tenant_id=tenant_id,
            url=url,
            secret=secrets.token_hex(32),
            events=events,
            status="active",
        )
        self.db.add(webhook)
        await self.db.commit()
        await self.db.refresh(webhook)
        return webhook

    async def list_webhooks(self, tenant_id: UUID) -> list[Webhook]:
        result = await self.db.execute(
            select(Webhook).where(Webhook.tenant_id == tenant_id).order_by(Webhook.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_webhook(self, webhook_id: UUID, tenant_id: UUID) -> bool:
        result = await self.db.execute(
            select(Webhook).where(Webhook.id == webhook_id, Webhook.tenant_id == tenant_id)
        )
        webhook = result.scalar_one_or_none()
        if not webhook:
            return False
        await self.db.delete(webhook)
        await self.db.commit()
        return True

    async def dispatch(self, tenant_id: UUID, event_type: str, payload: dict):
        result = await self.db.execute(
            select(Webhook).where(
                Webhook.tenant_id == tenant_id,
                Webhook.status == "active",
            )
        )
        webhooks = result.scalars().all()

        for webhook in webhooks:
            if event_type not in webhook.events and "*" not in webhook.events:
                continue
            await self._deliver(webhook, event_type, payload)

    async def _deliver(self, webhook: Webhook, event_type: str, payload: dict):
        body = json.dumps({"event": event_type, "data": payload})
        signature = hmac.new(webhook.secret.encode(), body.encode(), hashlib.sha256).hexdigest()

        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event_type=event_type,
            payload=payload,
            status="pending",
        )
        self.db.add(delivery)

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    webhook.url,
                    content=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Signature": signature,
                        "X-Event-Type": event_type,
                    },
                )
            delivery.response_status = resp.status_code
            delivery.response_body = resp.text[:2000]
            delivery.status = "delivered" if resp.status_code < 400 else "failed"
        except Exception as e:
            delivery.status = "failed"
            delivery.response_body = str(e)[:2000]
        delivery.attempts = 1
        await self.db.commit()
