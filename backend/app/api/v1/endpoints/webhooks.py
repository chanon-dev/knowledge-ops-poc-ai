from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_role
from app.models.user import User
from app.services.webhook_service import WebhookService

router = APIRouter()


class WebhookCreate(BaseModel):
    url: str
    events: list[str]


@router.post("")
async def create_webhook(
    body: WebhookCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    service = WebhookService(db)
    webhook = await service.create_webhook(user.tenant_id, body.url, body.events)
    return {"id": str(webhook.id), "url": webhook.url, "events": webhook.events, "status": webhook.status}


@router.get("")
async def list_webhooks(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    service = WebhookService(db)
    webhooks = await service.list_webhooks(user.tenant_id)
    return {"data": [{"id": str(w.id), "url": w.url, "events": w.events, "status": w.status} for w in webhooks]}


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    service = WebhookService(db)
    deleted = await service.delete_webhook(webhook_id, user.tenant_id)
    if not deleted:
        return {"error": "Webhook not found"}
    return {"status": "deleted"}
