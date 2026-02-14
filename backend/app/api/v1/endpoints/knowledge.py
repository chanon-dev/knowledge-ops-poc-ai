from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse, PaginationParams, build_paginated_response
from app.services.knowledge_service import KnowledgeService

router = APIRouter()


class KnowledgeDocResponse:
    """Inline response model."""
    pass


from pydantic import BaseModel, ConfigDict
from datetime import datetime


class KnowledgeDocResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    department_id: UUID
    title: str
    source_type: str
    mime_type: str | None = None
    file_size: int | None = None
    status: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime


@router.post("/{dept_id}/upload", response_model=KnowledgeDocResponse, status_code=201)
async def upload_document(
    dept_id: UUID,
    title: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    content = await file.read()
    service = KnowledgeService(db)
    doc = await service.upload_document(
        tenant_id=user.tenant_id,
        department_id=dept_id,
        user_id=user.id,
        file_content=content,
        filename=file.filename or "unknown",
        title=title,
        mime_type=file.content_type or "application/octet-stream",
    )
    return doc


@router.get("/{dept_id}", response_model=PaginatedResponse[KnowledgeDocResponse])
async def list_documents(
    dept_id: UUID,
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = KnowledgeService(db)
    items, total = await service.list_documents(
        user.tenant_id, dept_id, pagination.page, pagination.per_page
    )
    return build_paginated_response(items, total, pagination, KnowledgeDocResponse)


@router.get("/{dept_id}/{doc_id}", response_model=KnowledgeDocResponse)
async def get_document(
    dept_id: UUID,
    doc_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = KnowledgeService(db)
    return await service.get_document(doc_id)


@router.delete("/{dept_id}/{doc_id}", status_code=204)
async def delete_document(
    dept_id: UUID,
    doc_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = KnowledgeService(db)
    await service.delete_document(doc_id)
