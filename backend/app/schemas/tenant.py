from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TenantCreate(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    plan_tier: Literal["free", "professional", "enterprise", "onpremise"] = "free"
    settings: dict = {}


class TenantUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    plan_tier: Literal["free", "professional", "enterprise", "onpremise"] | None = None
    status: Literal["active", "trial", "suspended", "cancelled"] | None = None
    settings: dict | None = None


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    plan_tier: str
    status: str
    settings: dict
    created_at: datetime
    updated_at: datetime
