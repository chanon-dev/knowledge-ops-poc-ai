"""Notification service for in-app and email notifications."""

import logging
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# We store notifications in a simple table. For email, we use SMTP or an external service.
class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def notify_approval_needed(self, tenant_id: UUID, department_id: UUID, approval_id: UUID, question: str):
        """Send notification when a new approval is needed."""
        from app.models.user import User
        from app.models.department import DepartmentMember

        # Find department admins/owners
        result = await self.db.execute(
            select(User).join(DepartmentMember, DepartmentMember.user_id == User.id).where(
                DepartmentMember.department_id == department_id,
                DepartmentMember.role.in_(["admin", "owner"]),
            )
        )
        reviewers = result.scalars().all()

        for reviewer in reviewers:
            await self._create_in_app_notification(
                user_id=reviewer.id,
                tenant_id=tenant_id,
                title="New approval request",
                message=f"A low-confidence answer needs review: {question[:100]}...",
                link=f"/approvals/{approval_id}",
                notification_type="approval_needed",
            )
            # Optional: send email
            await self._send_email_notification(
                to_email=reviewer.email,
                subject="[The Expert] New answer requires approval",
                body=f"Question: {question}\n\nPlease review at: /approvals/{approval_id}",
            )

        logger.info(f"Notified {len(reviewers)} reviewers for approval {approval_id}")

    async def notify_approval_resolved(self, tenant_id: UUID, user_id: UUID, approval_id: UUID, status: str):
        """Notify the original querier that their question was resolved."""
        await self._create_in_app_notification(
            user_id=user_id,
            tenant_id=tenant_id,
            title=f"Answer {status}",
            message=f"Your question has been reviewed and the answer was {status}.",
            link=f"/approvals/{approval_id}",
            notification_type="approval_resolved",
        )

    async def _create_in_app_notification(
        self, user_id: UUID, tenant_id: UUID, title: str, message: str,
        link: str | None = None, notification_type: str = "info"
    ):
        """Store in-app notification. Uses audit_logs table for simplicity."""
        from app.models.audit_log import AuditLog
        notification = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=f"notification:{notification_type}",
            resource_type="notification",
            details={"title": title, "message": message, "link": link, "read": False},
        )
        self.db.add(notification)
        await self.db.commit()

    async def _send_email_notification(self, to_email: str, subject: str, body: str):
        """Send email notification via SMTP. Placeholder for actual email sending."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from app.core.config import settings

            smtp_host = getattr(settings, "SMTP_HOST", None)
            if not smtp_host:
                logger.debug(f"Email skipped (no SMTP config): {subject} -> {to_email}")
                return

            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = getattr(settings, "SMTP_FROM", "noreply@theexpert.ai")
            msg["To"] = to_email

            with smtplib.SMTP(smtp_host, getattr(settings, "SMTP_PORT", 587)) as server:
                server.starttls()
                smtp_user = getattr(settings, "SMTP_USER", "")
                smtp_pass = getattr(settings, "SMTP_PASS", "")
                if smtp_user:
                    server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            logger.info(f"Email sent to {to_email}: {subject}")
        except Exception as e:
            logger.warning(f"Failed to send email to {to_email}: {e}")

    async def get_unread_notifications(self, user_id: UUID, limit: int = 20) -> list[dict]:
        """Get unread in-app notifications for a user."""
        from app.models.audit_log import AuditLog

        result = await self.db.execute(
            select(AuditLog).where(
                AuditLog.user_id == user_id,
                AuditLog.action.like("notification:%"),
            ).order_by(AuditLog.created_at.desc()).limit(limit)
        )
        notifications = result.scalars().all()
        return [
            {
                "id": str(n.id),
                "title": n.details.get("title", ""),
                "message": n.details.get("message", ""),
                "link": n.details.get("link"),
                "read": n.details.get("read", False),
                "created_at": str(n.created_at),
            }
            for n in notifications
        ]
