from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.schemas.billing import SubscriptionResponse, UsageSummaryResponse, QuotaStatusResponse, InvoiceResponse
from app.services.billing_service import BillingService

router = APIRouter()


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("member")),
):
    service = BillingService(db)
    sub = await service.get_subscription(user.tenant_id)
    if not sub:
        sub = await service.create_subscription(user.tenant_id)
    return sub


@router.post("/subscription/upgrade", response_model=SubscriptionResponse)
async def upgrade_plan(
    new_plan: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("owner")),
):
    service = BillingService(db)
    return await service.upgrade_plan(user.tenant_id, new_plan)


@router.get("/quota", response_model=QuotaStatusResponse)
async def get_quota(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("member")),
):
    service = BillingService(db)
    sub = await service.get_subscription(user.tenant_id)
    plan = sub.plan_tier if sub else "free"
    return await service.check_quota(user.tenant_id, plan)


@router.get("/usage", response_model=UsageSummaryResponse)
async def get_usage(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    service = BillingService(db)
    return await service.get_usage_summary(user.tenant_id)


@router.get("/invoices", response_model=list[InvoiceResponse])
async def list_invoices(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    service = BillingService(db)
    return await service.list_invoices(user.tenant_id)
