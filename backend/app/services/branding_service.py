from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant


DEFAULT_BRANDING = {
    "logo_url": None,
    "primary_color": "#2563eb",
    "secondary_color": "#1e40af",
    "company_name": None,
    "custom_css": None,
    "favicon_url": None,
    "login_background_url": None,
}


class BrandingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_branding(self, tenant_id: UUID) -> dict:
        result = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            return DEFAULT_BRANDING
        branding = tenant.settings.get("branding", {})
        return {**DEFAULT_BRANDING, **branding}

    async def update_branding(self, tenant_id: UUID, branding: dict) -> dict:
        result = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise ValueError("Tenant not found")
        settings = dict(tenant.settings or {})
        settings["branding"] = {**settings.get("branding", {}), **branding}
        tenant.settings = settings
        await self.db.commit()
        return {**DEFAULT_BRANDING, **settings["branding"]}
