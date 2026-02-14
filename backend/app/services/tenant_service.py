from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate, TenantUpdate


class TenantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_tenants(
        self, page: int = 1, per_page: int = 20
    ) -> tuple[list[Tenant], int]:
        count_stmt = select(func.count()).select_from(Tenant).where(Tenant.deleted_at.is_(None))
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = (
            select(Tenant)
            .where(Tenant.deleted_at.is_(None))
            .order_by(Tenant.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def get_tenant(self, tenant_id: UUID) -> Tenant:
        stmt = select(Tenant).where(Tenant.id == tenant_id, Tenant.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise NotFoundError(f"Tenant {tenant_id} not found")
        return tenant

    async def get_tenant_by_slug(self, slug: str) -> Tenant:
        stmt = select(Tenant).where(Tenant.slug == slug, Tenant.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise NotFoundError(f"Tenant with slug '{slug}' not found")
        return tenant

    async def create_tenant(self, data: TenantCreate) -> Tenant:
        # Check slug uniqueness
        existing = await self.db.execute(
            select(Tenant).where(Tenant.slug == data.slug)
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Tenant with slug '{data.slug}' already exists")

        tenant = Tenant(**data.model_dump())
        self.db.add(tenant)
        await self.db.flush()
        await self.db.refresh(tenant)
        return tenant

    async def update_tenant(self, tenant_id: UUID, data: TenantUpdate) -> Tenant:
        tenant = await self.get_tenant(tenant_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tenant, field, value)
        await self.db.flush()
        await self.db.refresh(tenant)
        return tenant

    async def soft_delete_tenant(self, tenant_id: UUID) -> None:
        tenant = await self.get_tenant(tenant_id)
        tenant.status = "cancelled"
        tenant.deleted_at = func.now()
        await self.db.flush()
