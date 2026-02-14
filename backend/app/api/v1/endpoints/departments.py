from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams, build_paginated_response
from app.schemas.department import (
    DepartmentCreate,
    DepartmentMemberCreate,
    DepartmentMemberResponse,
    DepartmentResponse,
    DepartmentUpdate,
)
from app.services.department_service import DepartmentService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[DepartmentResponse])
async def list_departments(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = DepartmentService(db)
    items, total = await service.list_departments(
        user.tenant_id, pagination.page, pagination.per_page
    )
    return build_paginated_response(items, total, pagination, DepartmentResponse)


@router.post("", response_model=DepartmentResponse, status_code=201)
async def create_department(
    body: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    service = DepartmentService(db)
    return await service.create_department(user.tenant_id, body)


@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = DepartmentService(db)
    return await service.get_department(department_id)


@router.put("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: UUID,
    body: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    service = DepartmentService(db)
    return await service.update_department(department_id, body)


@router.delete("/{department_id}", status_code=204)
async def delete_department(
    department_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    service = DepartmentService(db)
    await service.soft_delete_department(department_id)


@router.get("/{department_id}/members", response_model=list[DepartmentMemberResponse])
async def list_members(
    department_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = DepartmentService(db)
    return await service.list_members(department_id)


@router.post(
    "/{department_id}/members",
    response_model=DepartmentMemberResponse,
    status_code=201,
)
async def add_member(
    department_id: UUID,
    body: DepartmentMemberCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    service = DepartmentService(db)
    return await service.add_member(department_id, user.tenant_id, body)


@router.delete("/{department_id}/members/{user_id}", status_code=204)
async def remove_member(
    department_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    service = DepartmentService(db)
    await service.remove_member(department_id, user_id)
