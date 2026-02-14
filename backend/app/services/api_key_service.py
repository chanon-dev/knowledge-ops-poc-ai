import secrets
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.security import hash_api_key, verify_api_key
from app.models.api_key import ApiKey


class ApiKeyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_key(
        self,
        tenant_id: UUID,
        user_id: UUID,
        name: str,
        permissions: dict | None = None,
        rate_limit: int = 100,
    ) -> tuple[ApiKey, str]:
        raw_key = "exp_" + secrets.token_urlsafe(32)
        prefix = raw_key[:12]
        key_hash = hash_api_key(raw_key)

        api_key = ApiKey(
            tenant_id=tenant_id,
            created_by=user_id,
            name=name,
            key_prefix=prefix,
            key_hash=key_hash,
            permissions=permissions or {},
            rate_limit=rate_limit,
            status="active",
        )
        self.db.add(api_key)
        await self.db.flush()
        await self.db.refresh(api_key)
        return api_key, raw_key

    async def validate_key(self, raw_key: str) -> ApiKey | None:
        prefix = raw_key[:12]
        stmt = select(ApiKey).where(
            ApiKey.key_prefix == prefix,
            ApiKey.status == "active",
        )
        result = await self.db.execute(stmt)
        api_key = result.scalar_one_or_none()

        if not api_key:
            return None

        if not verify_api_key(raw_key, api_key.key_hash):
            return None

        # Check expiry
        if api_key.expires_at:
            from datetime import datetime, timezone
            if datetime.now(timezone.utc) > api_key.expires_at:
                return None

        # Update last used
        api_key.last_used_at = func.now()
        await self.db.flush()

        return api_key

    async def list_keys(
        self,
        tenant_id: UUID,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[ApiKey], int]:
        base = select(ApiKey).where(ApiKey.tenant_id == tenant_id)
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = (
            base.order_by(ApiKey.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def revoke_key(self, key_id: UUID, tenant_id: UUID) -> None:
        stmt = select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.tenant_id == tenant_id,
        )
        result = await self.db.execute(stmt)
        api_key = result.scalar_one_or_none()
        if not api_key:
            raise NotFoundError("API key not found")

        api_key.status = "revoked"
        await self.db.flush()
