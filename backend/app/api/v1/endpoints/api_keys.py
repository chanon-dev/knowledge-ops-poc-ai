from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_role
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams, build_paginated_response
from app.services.api_key_service import ApiKeyService

router = APIRouter()


class ApiKeyCreate(BaseModel):
    name: str = Field(..., max_length=255)
    permissions: dict = {}
    rate_limit: int = 100


class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    key_prefix: str
    permissions: dict
    rate_limit: int
    status: str
    last_used_at: datetime | None
    expires_at: datetime | None
    created_at: datetime


class ApiKeyCreateResponse(ApiKeyResponse):
    raw_key: str  # Only returned on creation


@router.post("", response_model=ApiKeyCreateResponse, status_code=201)
async def generate_api_key(
    body: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    service = ApiKeyService(db)
    api_key, raw_key = await service.generate_key(
        tenant_id=user.tenant_id,
        user_id=user.id,
        name=body.name,
        permissions=body.permissions,
        rate_limit=body.rate_limit,
    )
    response = ApiKeyResponse.model_validate(api_key).model_dump()
    response["raw_key"] = raw_key
    return response


@router.get("", response_model=PaginatedResponse[ApiKeyResponse])
async def list_api_keys(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    service = ApiKeyService(db)
    items, total = await service.list_keys(
        user.tenant_id, pagination.page, pagination.per_page
    )
    return build_paginated_response(items, total, pagination, ApiKeyResponse)


@router.delete("/{key_id}", status_code=204)
async def revoke_api_key(
    key_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    service = ApiKeyService(db)
    await service.revoke_key(key_id, user.tenant_id)
