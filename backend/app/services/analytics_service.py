from datetime import date, datetime
from uuid import UUID
from collections import Counter

from sqlalchemy import case, cast, Date, Float, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval import Approval
from app.models.conversation import Conversation, Message
from app.models.department import Department
from app.models.knowledge import KnowledgeDoc
from app.models.user import User


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_usage_overview(
        self,
        tenant_id: UUID,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> dict:
        base_filter = [Message.tenant_id == tenant_id, Message.role == "user"]
        if date_from:
            base_filter.append(cast(Message.created_at, Date) >= date_from)
        if date_to:
            base_filter.append(cast(Message.created_at, Date) <= date_to)

        total_queries = (
            await self.db.execute(select(func.count()).select_from(Message).where(*base_filter))
        ).scalar_one()

        daily_stmt = (
            select(cast(Message.created_at, Date).label("date"), func.count().label("queries"))
            .where(*base_filter)
            .group_by(cast(Message.created_at, Date))
            .order_by(cast(Message.created_at, Date))
        )
        daily_result = await self.db.execute(daily_stmt)
        queries_per_day = [{"date": str(row.date), "queries": row.queries} for row in daily_result.all()]

        active_users = (
            await self.db.execute(select(func.count(func.distinct(Message.user_id))).where(*base_filter))
        ).scalar_one()

        dept_stmt = (
            select(Department.name, func.count(Message.id).label("queries"))
            .join(Department, Department.id == Message.department_id)
            .where(*base_filter)
            .group_by(Department.name)
        )
        dept_result = await self.db.execute(dept_stmt)
        by_department = [{"department": row.name, "queries": row.queries} for row in dept_result.all()]

        return {
            "total_queries": total_queries,
            "active_users": active_users,
            "queries_per_day": queries_per_day,
            "by_department": by_department,
        }

    async def get_department_stats(
        self, tenant_id: UUID, department_id: UUID,
        date_from: date | None = None, date_to: date | None = None,
    ) -> dict:
        base_filter = [Message.tenant_id == tenant_id, Message.department_id == department_id]
        if date_from:
            base_filter.append(cast(Message.created_at, Date) >= date_from)
        if date_to:
            base_filter.append(cast(Message.created_at, Date) <= date_to)

        ai_filter = [*base_filter, Message.role == "assistant"]

        avg_confidence = (
            await self.db.execute(
                select(func.avg(Message.confidence)).where(*ai_filter, Message.confidence.isnot(None))
            )
        ).scalar_one()

        total = (
            await self.db.execute(select(func.count()).where(*base_filter, Message.role == "user"))
        ).scalar_one()

        # Active users per department
        active_users_dept = (
            await self.db.execute(
                select(func.count(func.distinct(Message.user_id))).where(*base_filter, Message.role == "user")
            )
        ).scalar_one()

        # Approval stats
        approval_filter = [Approval.tenant_id == tenant_id, Approval.department_id == department_id]
        approved = (await self.db.execute(select(func.count()).where(*approval_filter, Approval.status == "approved"))).scalar_one()
        total_approvals = (await self.db.execute(select(func.count()).where(*approval_filter))).scalar_one()
        approval_rate = (approved / total_approvals * 100) if total_approvals > 0 else 0

        # MTTR - Mean Time to Resolution (time from query to approval)
        mttr_result = await self.db.execute(
            select(func.avg(Approval.updated_at - Approval.created_at)).where(
                *approval_filter, Approval.status.in_(["approved", "rejected"])
            )
        )
        mttr = mttr_result.scalar_one()
        mttr_hours = mttr.total_seconds() / 3600 if mttr else 0

        return {
            "total_queries": total,
            "avg_confidence": round(float(avg_confidence or 0), 3),
            "active_users": active_users_dept,
            "approval_rate": round(approval_rate, 1),
            "total_approvals": total_approvals,
            "approved": approved,
            "mttr_hours": round(mttr_hours, 1),
        }

    async def get_ai_performance(
        self, tenant_id: UUID,
        date_from: date | None = None, date_to: date | None = None,
    ) -> dict:
        base_filter = [Message.tenant_id == tenant_id, Message.role == "assistant"]
        if date_from:
            base_filter.append(cast(Message.created_at, Date) >= date_from)
        if date_to:
            base_filter.append(cast(Message.created_at, Date) <= date_to)

        avg_latency = (
            await self.db.execute(
                select(func.avg(Message.latency_ms)).where(*base_filter, Message.latency_ms.isnot(None))
            )
        ).scalar_one()

        trend_stmt = (
            select(
                cast(Message.created_at, Date).label("date"),
                func.avg(Message.confidence).label("avg_confidence"),
                func.avg(Message.latency_ms).label("avg_latency"),
            )
            .where(*base_filter, Message.confidence.isnot(None))
            .group_by(cast(Message.created_at, Date))
            .order_by(cast(Message.created_at, Date))
        )
        trend_result = await self.db.execute(trend_stmt)
        confidence_trend = [
            {
                "date": str(row.date),
                "avg_confidence": round(float(row.avg_confidence or 0), 3),
                "avg_latency": round(float(row.avg_latency or 0), 1),
            }
            for row in trend_result.all()
        ]

        token_stmt = select(
            func.sum(Message.tokens_input).label("total_input"),
            func.sum(Message.tokens_output).label("total_output"),
        ).where(*base_filter)
        token_result = await self.db.execute(token_stmt)
        tokens = token_result.one()

        # Model accuracy trend (based on approval rates over time)
        accuracy_stmt = (
            select(
                cast(Approval.created_at, Date).label("date"),
                func.count(case((Approval.status == "approved", 1))).label("approved"),
                func.count().label("total"),
            )
            .where(Approval.tenant_id == tenant_id)
            .group_by(cast(Approval.created_at, Date))
            .order_by(cast(Approval.created_at, Date))
        )
        accuracy_result = await self.db.execute(accuracy_stmt)
        model_accuracy_trend = [
            {
                "date": str(row.date),
                "accuracy": round(row.approved / row.total * 100, 1) if row.total > 0 else 0,
            }
            for row in accuracy_result.all()
        ]

        # Confidence drift detection
        drift_detected = False
        if len(confidence_trend) >= 7:
            recent = [t["avg_confidence"] for t in confidence_trend[-7:]]
            earlier = [t["avg_confidence"] for t in confidence_trend[-14:-7]] if len(confidence_trend) >= 14 else recent
            if earlier:
                avg_recent = sum(recent) / len(recent)
                avg_earlier = sum(earlier) / len(earlier)
                drift_detected = (avg_earlier - avg_recent) > 0.05

        return {
            "avg_latency_ms": round(float(avg_latency or 0), 1),
            "confidence_trend": confidence_trend,
            "model_accuracy_trend": model_accuracy_trend,
            "drift_detected": drift_detected,
            "total_tokens_input": int(tokens.total_input or 0),
            "total_tokens_output": int(tokens.total_output or 0),
        }

    async def get_top_topics(self, tenant_id: UUID, department_id: UUID | None = None, limit: int = 10) -> list[dict]:
        """Get top queried topics using simple keyword extraction."""
        filters = [Message.tenant_id == tenant_id, Message.role == "user"]
        if department_id:
            filters.append(Message.department_id == department_id)

        result = await self.db.execute(
            select(Message.content).where(*filters).order_by(Message.created_at.desc()).limit(500)
        )
        messages = [row[0] for row in result.all()]

        # Simple keyword frequency analysis
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
                      "have", "has", "had", "do", "does", "did", "will", "would", "could",
                      "should", "may", "might", "shall", "can", "to", "of", "in", "for",
                      "on", "with", "at", "by", "from", "as", "into", "through", "during",
                      "before", "after", "above", "below", "between", "it", "its", "this",
                      "that", "these", "those", "i", "me", "my", "we", "our", "you", "your",
                      "he", "she", "they", "them", "what", "which", "who", "how", "when",
                      "where", "why", "not", "no", "and", "or", "but", "if", "then", "so"}

        word_counts = Counter()
        for msg in messages:
            words = msg.lower().split()
            for word in words:
                clean = word.strip(".,?!:;()[]{}\"'")
                if len(clean) > 2 and clean not in stop_words:
                    word_counts[clean] += 1

        return [{"topic": word, "count": count} for word, count in word_counts.most_common(limit)]

    async def get_team_productivity(self, tenant_id: UUID) -> dict:
        """Team productivity metrics."""
        # Queries per user
        user_stats = await self.db.execute(
            select(User.full_name, func.count(Message.id).label("queries"))
            .join(Message, Message.user_id == User.id)
            .where(Message.tenant_id == tenant_id, Message.role == "user")
            .group_by(User.full_name)
            .order_by(func.count(Message.id).desc())
        )
        queries_per_user = [{"user": row.full_name, "queries": row.queries} for row in user_stats.all()]

        # Self-service rate (auto-approved / total)
        total_queries = (
            await self.db.execute(
                select(func.count()).select_from(Message).where(
                    Message.tenant_id == tenant_id, Message.role == "user"
                )
            )
        ).scalar_one()
        escalated = (
            await self.db.execute(
                select(func.count()).select_from(Approval).where(Approval.tenant_id == tenant_id)
            )
        ).scalar_one()
        self_service_rate = ((total_queries - escalated) / total_queries * 100) if total_queries > 0 else 100

        # Knowledge base growth
        kb_growth = await self.db.execute(
            select(
                cast(KnowledgeDoc.created_at, Date).label("date"),
                func.count().label("docs"),
            )
            .where(KnowledgeDoc.tenant_id == tenant_id)
            .group_by(cast(KnowledgeDoc.created_at, Date))
            .order_by(cast(KnowledgeDoc.created_at, Date))
        )
        kb_growth_data = [{"date": str(r.date), "docs_added": r.docs} for r in kb_growth.all()]

        # Estimated time saved (assume 15 min per auto-resolved query)
        auto_resolved = total_queries - escalated
        time_saved_hours = auto_resolved * 15 / 60

        return {
            "queries_per_user": queries_per_user,
            "self_service_rate": round(self_service_rate, 1),
            "kb_growth": kb_growth_data,
            "time_saved_hours": round(time_saved_hours, 1),
            "total_queries": total_queries,
            "escalated_queries": escalated,
        }

    async def export_analytics(self, tenant_id: UUID, date_from: date | None = None, date_to: date | None = None) -> dict:
        """Export analytics data as JSON (for CSV/JSON download)."""
        usage = await self.get_usage_overview(tenant_id, date_from, date_to)
        ai_perf = await self.get_ai_performance(tenant_id, date_from, date_to)
        productivity = await self.get_team_productivity(tenant_id)
        topics = await self.get_top_topics(tenant_id)

        return {
            "exported_at": datetime.utcnow().isoformat(),
            "usage": usage,
            "ai_performance": ai_perf,
            "team_productivity": productivity,
            "top_topics": topics,
        }
