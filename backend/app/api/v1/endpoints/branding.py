from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_role
from app.models.user import User
from app.services.branding_service import BrandingService

router = APIRouter()


class BrandingUpdate(BaseModel):
    logo_url: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    company_name: str | None = None
    custom_css: str | None = None
    favicon_url: str | None = None
    login_background_url: str | None = None


@router.get("")
async def get_branding(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("member")),
):
    service = BrandingService(db)
    return await service.get_branding(user.tenant_id)


@router.put("")
async def update_branding(
    body: BrandingUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("owner")),
):
    service = BrandingService(db)
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    return await service.update_branding(user.tenant_id, update_data)
