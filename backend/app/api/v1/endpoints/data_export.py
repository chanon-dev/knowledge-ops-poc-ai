"""GDPR data export and deletion endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.services.data_export_service import DataExportService

router = APIRouter()


@router.get("/export/tenant")
async def export_tenant_data(
    format: str = "json",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("owner")),
):
    """Export all tenant data (GDPR data portability)."""
    service = DataExportService(db)
    data = await service.export_tenant_data(user.tenant_id, format=format)
    content_type = "text/csv" if format == "csv" else "application/json"
    return PlainTextResponse(content=data, media_type=content_type)


@router.get("/export/user/{user_id}")
async def export_user_data(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """Export all data for a specific user."""
    service = DataExportService(db)
    data = await service.export_user_data(user_id)
    return PlainTextResponse(content=data, media_type="application/json")


@router.get("/export/me")
async def export_my_data(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Export my own data (GDPR data subject access request)."""
    service = DataExportService(db)
    data = await service.export_user_data(user.id)
    return PlainTextResponse(content=data, media_type="application/json")


@router.delete("/forget/{user_id}")
async def forget_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("owner")),
):
    """Right to be forgotten - delete all user data (GDPR Article 17)."""
    service = DataExportService(db)
    result = await service.delete_user_data(user_id, user.tenant_id)
    return {"status": "deleted", "details": result}
