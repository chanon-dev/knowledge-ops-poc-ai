from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SubscribeRequest(BaseModel):
    plan_tier: Literal["free", "professional", "enterprise"] = "free"
    stripe_payment_method_id: str | None = None


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    plan_tier: str
    status: str
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    created_at: datetime
    updated_at: datetime


class UsageSummaryResponse(BaseModel):
    tenant_id: UUID
    date_from: date
    date_to: date
    total_queries: int
    total_image_queries: int
    total_tokens_used: int
    daily_breakdown: list[dict] = []


class QuotaStatusResponse(BaseModel):
    allowed: bool
    plan_tier: str
    query_count_today: int
    query_limit: int
    remaining: int


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    tenant_id: UUID
    amount_cents: int
    currency: str
    status: str
    period_start: datetime | None = None
    period_end: datetime | None = None
    pdf_url: str | None = None
    created_at: datetime
