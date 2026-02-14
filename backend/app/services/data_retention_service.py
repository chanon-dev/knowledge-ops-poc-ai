from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message
from app.models.audit_log import AuditLog


DEFAULT_RETENTION_DAYS = {
    "conversations": 365,
    "audit_logs": 730,
    "usage_records": 365,
}


class DataRetentionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def cleanup_old_conversations(self, tenant_id: UUID, retention_days: int | None = None):
        days = retention_days or DEFAULT_RETENTION_DAYS["conversations"]
        cutoff = datetime.utcnow() - timedelta(days=days)

        old_convos = await self.db.execute(
            select(Conversation.id).where(
                Conversation.tenant_id == tenant_id,
                Conversation.updated_at < cutoff,
            )
        )
        convo_ids = [row[0] for row in old_convos.all()]
        if not convo_ids:
            return 0

        await self.db.execute(
            delete(Message).where(Message.conversation_id.in_(convo_ids))
        )
        result = await self.db.execute(
            delete(Conversation).where(Conversation.id.in_(convo_ids))
        )
        await self.db.commit()
        return result.rowcount

    async def cleanup_old_audit_logs(self, tenant_id: UUID, retention_days: int | None = None):
        days = retention_days or DEFAULT_RETENTION_DAYS["audit_logs"]
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            delete(AuditLog).where(
                AuditLog.tenant_id == tenant_id,
                AuditLog.created_at < cutoff,
            )
        )
        await self.db.commit()
        return result.rowcount

    async def get_retention_stats(self, tenant_id: UUID) -> dict:
        from app.models.billing import UsageRecord

        convo_count = await self.db.execute(
            select(Conversation.id).where(Conversation.tenant_id == tenant_id)
        )
        audit_count = await self.db.execute(
            select(AuditLog.id).where(AuditLog.tenant_id == tenant_id)
        )
        return {
            "conversations": len(convo_count.all()),
            "audit_logs": len(audit_count.all()),
            "retention_policy": DEFAULT_RETENTION_DAYS,
        }
