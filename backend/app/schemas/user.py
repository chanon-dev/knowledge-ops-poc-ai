from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., max_length=255)
    role: Literal["owner", "admin", "member", "viewer"] = "member"
    password: str | None = Field(None, min_length=8, description="Password for dev auth")


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=255)
    role: Literal["owner", "admin", "member", "viewer"] | None = None
    avatar_url: str | None = Field(None, max_length=500)
    preferences: dict | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    email: str
    full_name: str
    role: str
    avatar_url: str | None
    preferences: dict = {}
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @field_validator("preferences", mode="before")
    @classmethod
    def strip_password_hash(cls, v):
        if isinstance(v, dict):
            v = {k: val for k, val in v.items() if not k.startswith("_")}
        return v or {}


class UserMeResponse(UserResponse):
    pass
