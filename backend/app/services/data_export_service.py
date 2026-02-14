"""GDPR data export and right-to-be-forgotten service."""

import json
import csv
import io
import logging
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.knowledge import KnowledgeDoc
from app.models.audit_log import AuditLog
from app.models.approval import Approval

logger = logging.getLogger(__name__)


class DataExportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def export_tenant_data(self, tenant_id: UUID, format: str = "json") -> str:
        """Export all tenant data for data portability (GDPR Article 20)."""
        data = {
            "exported_at": datetime.utcnow().isoformat(),
            "tenant_id": str(tenant_id),
            "users": await self._export_users(tenant_id),
            "conversations": await self._export_conversations(tenant_id),
            "knowledge_docs": await self._export_knowledge(tenant_id),
            "approvals": await self._export_approvals(tenant_id),
        }

        if format == "csv":
            return self._to_csv(data)
        return json.dumps(data, indent=2, default=str)

    async def export_user_data(self, user_id: UUID) -> str:
        """Export all data for a specific user (GDPR data subject request)."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return json.dumps({"error": "User not found"})

        data = {
            "exported_at": datetime.utcnow().isoformat(),
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "created_at": str(user.created_at),
            },
            "conversations": [],
            "audit_trail": [],
        }

        # User conversations
        result = await self.db.execute(
            select(Conversation).where(Conversation.user_id == user_id)
        )
        for conv in result.scalars().all():
            msg_result = await self.db.execute(
                select(Message).where(Message.conversation_id == conv.id).order_by(Message.created_at)
            )
            messages = [
                {"role": m.role, "content": m.content, "created_at": str(m.created_at)}
                for m in msg_result.scalars().all()
            ]
            data["conversations"].append({
                "id": str(conv.id),
                "title": conv.title,
                "messages": messages,
                "created_at": str(conv.created_at),
            })

        # Audit trail
        result = await self.db.execute(
            select(AuditLog).where(AuditLog.user_id == user_id).order_by(AuditLog.created_at.desc()).limit(500)
        )
        data["audit_trail"] = [
            {"action": log.action, "resource_type": log.resource_type, "created_at": str(log.created_at)}
            for log in result.scalars().all()
        ]

        return json.dumps(data, indent=2, default=str)

    async def delete_user_data(self, user_id: UUID, tenant_id: UUID) -> dict:
        """Right to be forgotten - delete all user data (GDPR Article 17)."""
        counts = {}

        # Delete messages in user's conversations
        result = await self.db.execute(
            select(Conversation.id).where(Conversation.user_id == user_id)
        )
        conv_ids = [row[0] for row in result.all()]

        if conv_ids:
            result = await self.db.execute(
                delete(Message).where(Message.conversation_id.in_(conv_ids))
            )
            counts["messages_deleted"] = result.rowcount

            result = await self.db.execute(
                delete(Conversation).where(Conversation.user_id == user_id)
            )
            counts["conversations_deleted"] = result.rowcount

        # Anonymize audit logs (keep structure, remove PII)
        result = await self.db.execute(
            select(AuditLog).where(AuditLog.user_id == user_id)
        )
        audit_logs = result.scalars().all()
        for log in audit_logs:
            log.user_id = None
            log.details = {"anonymized": True, "original_action": log.action}
        counts["audit_logs_anonymized"] = len(audit_logs)

        # Delete the user record
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            await self.db.delete(user)
            counts["user_deleted"] = True

        await self.db.commit()
        logger.info(f"GDPR deletion completed for user {user_id}: {counts}")
        return counts

    async def _export_users(self, tenant_id: UUID) -> list[dict]:
        result = await self.db.execute(select(User).where(User.tenant_id == tenant_id))
        return [
            {"id": str(u.id), "email": u.email, "full_name": u.full_name, "role": u.role, "created_at": str(u.created_at)}
            for u in result.scalars().all()
        ]

    async def _export_conversations(self, tenant_id: UUID) -> list[dict]:
        result = await self.db.execute(select(Conversation).where(Conversation.tenant_id == tenant_id))
        convos = []
        for conv in result.scalars().all():
            msg_result = await self.db.execute(
                select(Message).where(Message.conversation_id == conv.id).order_by(Message.created_at)
            )
            messages = [{"role": m.role, "content": m.content, "created_at": str(m.created_at)} for m in msg_result.scalars().all()]
            convos.append({"id": str(conv.id), "title": conv.title, "messages": messages})
        return convos

    async def _export_knowledge(self, tenant_id: UUID) -> list[dict]:
        result = await self.db.execute(select(KnowledgeDoc).where(KnowledgeDoc.tenant_id == tenant_id))
        return [
            {"id": str(d.id), "title": d.title, "file_type": d.file_type, "status": d.status, "created_at": str(d.created_at)}
            for d in result.scalars().all()
        ]

    async def _export_approvals(self, tenant_id: UUID) -> list[dict]:
        result = await self.db.execute(select(Approval).where(Approval.tenant_id == tenant_id))
        return [
            {"id": str(a.id), "status": a.status, "created_at": str(a.created_at)}
            for a in result.scalars().all()
        ]

    def _to_csv(self, data: dict) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        for section, items in data.items():
            if isinstance(items, list) and items:
                writer.writerow([f"--- {section} ---"])
                writer.writerow(items[0].keys())
                for item in items:
                    writer.writerow(item.values())
                writer.writerow([])
        return output.getvalue()
