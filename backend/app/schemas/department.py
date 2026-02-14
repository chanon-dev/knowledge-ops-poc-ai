from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DepartmentCreate(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    icon: str = Field("📁", max_length=10)
    description: str | None = None
    config: dict = {}


class DepartmentUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    icon: str | None = Field(None, max_length=10)
    config: dict | None = None
    status: Literal["active", "archived", "setup"] | None = None
    sort_order: int | None = None


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    slug: str
    icon: str
    description: str | None
    config: dict
    status: str
    sort_order: int
    created_at: datetime
    updated_at: datetime


class DepartmentMemberCreate(BaseModel):
    user_id: UUID
    role: Literal["lead", "approver", "member", "viewer"] = "member"


class DepartmentMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    department_id: UUID
    user_id: UUID
    tenant_id: UUID
    role: str
    created_at: datetime
