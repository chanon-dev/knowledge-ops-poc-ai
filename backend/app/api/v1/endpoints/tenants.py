from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_role
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams, build_paginated_response
from app.schemas.tenant import TenantCreate, TenantResponse, TenantUpdate
from app.services.tenant_service import TenantService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[TenantResponse])
async def list_tenants(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    service = TenantService(db)
    items, total = await service.list_tenants(pagination.page, pagination.per_page)
    return build_paginated_response(items, total, pagination, TenantResponse)


@router.post("", response_model=TenantResponse, status_code=201)
async def create_tenant(
    body: TenantCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    service = TenantService(db)
    return await service.create_tenant(body)


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("member")),
):
    service = TenantService(db)
    return await service.get_tenant(tenant_id)


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    body: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("owner")),
):
    service = TenantService(db)
    return await service.update_tenant(tenant_id, body)
