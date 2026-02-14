from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import check_role_permission, decode_jwt
from app.db.session import SessionLocal
from app.models.user import User


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise UnauthorizedError("Missing Authorization header")

    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError("Invalid Authorization header format")

    payload = decode_jwt(parts[1])
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Invalid token: missing subject")

    from sqlalchemy import select
    stmt = select(User).where(User.id == UUID(user_id), User.deleted_at.is_(None))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedError("User not found")

    return user


def require_role(min_role: str):
    async def _check(user: User = Depends(get_current_user)) -> User:
        if not check_role_permission(user.role, min_role):
            raise ForbiddenError(f"Requires '{min_role}' role or higher")
        return user
    return _check


async def set_tenant_rls(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AsyncSession:
    await db.execute(
        text("SET LOCAL app.current_tenant = :tid"),
        {"tid": str(user.tenant_id)},
    )
    return db
