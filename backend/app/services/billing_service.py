from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.billing import Subscription, UsageRecord, Invoice


PLAN_LIMITS = {
    "free": {"queries_per_day": 50, "departments": 1, "users": 5},
    "professional": {"queries_per_day": 500, "departments": 5, "users": 25},
    "enterprise": {"queries_per_day": -1, "departments": -1, "users": -1},
}


class BillingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_subscription(self, tenant_id: UUID) -> Subscription | None:
        result = await self.db.execute(
            select(Subscription).where(Subscription.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def create_subscription(self, tenant_id: UUID, plan_tier: str = "free") -> Subscription:
        sub = Subscription(tenant_id=tenant_id, plan_tier=plan_tier, status="active")
        self.db.add(sub)
        await self.db.commit()
        await self.db.refresh(sub)
        return sub

    async def upgrade_plan(self, tenant_id: UUID, new_plan: str) -> Subscription:
        sub = await self.get_subscription(tenant_id)
        if not sub:
            sub = await self.create_subscription(tenant_id, new_plan)
        else:
            sub.plan_tier = new_plan
            sub.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(sub)
        return sub

    async def check_quota(self, tenant_id: UUID, plan_tier: str) -> dict:
        today = date.today()
        result = await self.db.execute(
            select(func.coalesce(func.sum(UsageRecord.query_count), 0)).where(
                UsageRecord.tenant_id == tenant_id,
                UsageRecord.record_date == today,
            )
        )
        count_today = result.scalar()
        limit = PLAN_LIMITS.get(plan_tier, PLAN_LIMITS["free"])["queries_per_day"]
        return {
            "allowed": limit == -1 or count_today < limit,
            "plan_tier": plan_tier,
            "query_count_today": count_today,
            "query_limit": limit,
            "remaining": max(0, limit - count_today) if limit != -1 else -1,
        }

    async def record_usage(self, tenant_id: UUID, user_id: UUID | None = None, queries: int = 1, tokens: int = 0):
        today = date.today()
        result = await self.db.execute(
            select(UsageRecord).where(
                UsageRecord.tenant_id == tenant_id,
                UsageRecord.user_id == user_id,
                UsageRecord.record_date == today,
            )
        )
        record = result.scalar_one_or_none()
        if record:
            record.query_count += queries
            record.tokens_used += tokens
        else:
            record = UsageRecord(
                tenant_id=tenant_id, user_id=user_id, record_date=today,
                query_count=queries, tokens_used=tokens,
            )
            self.db.add(record)
        await self.db.commit()

    async def get_usage_summary(self, tenant_id: UUID, date_from: date | None = None, date_to: date | None = None) -> dict:
        if not date_to:
            date_to = date.today()
        if not date_from:
            date_from = date_to - timedelta(days=30)

        result = await self.db.execute(
            select(
                UsageRecord.record_date,
                func.sum(UsageRecord.query_count).label("queries"),
                func.sum(UsageRecord.image_query_count).label("image_queries"),
                func.sum(UsageRecord.tokens_used).label("tokens"),
            )
            .where(
                UsageRecord.tenant_id == tenant_id,
                UsageRecord.record_date >= date_from,
                UsageRecord.record_date <= date_to,
            )
            .group_by(UsageRecord.record_date)
            .order_by(UsageRecord.record_date)
        )
        rows = result.all()
        return {
            "tenant_id": tenant_id,
            "date_from": date_from,
            "date_to": date_to,
            "total_queries": sum(r.queries for r in rows),
            "total_image_queries": sum(r.image_queries for r in rows),
            "total_tokens_used": sum(r.tokens for r in rows),
            "daily_breakdown": [
                {"date": str(r.record_date), "queries": r.queries, "tokens": r.tokens}
                for r in rows
            ],
        }

    async def list_invoices(self, tenant_id: UUID) -> list[Invoice]:
        result = await self.db.execute(
            select(Invoice).where(Invoice.tenant_id == tenant_id).order_by(Invoice.created_at.desc())
        )
        return list(result.scalars().all())
