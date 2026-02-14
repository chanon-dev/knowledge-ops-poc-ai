from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_users(
        self, tenant_id: UUID, page: int = 1, per_page: int = 20
    ) -> tuple[list[User], int]:
        base = select(User).where(
            User.tenant_id == tenant_id, User.deleted_at.is_(None)
        )
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = base.order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def get_user(self, user_id: UUID) -> User:
        stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email, User.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, tenant_id: UUID, data: UserCreate) -> User:
        existing = await self.get_user_by_email(data.email)
        if existing:
            raise ConflictError(f"User with email '{data.email}' already exists")

        user_data = data.model_dump(exclude={"password"})
        user = User(tenant_id=tenant_id, **user_data)

        # Store hashed password in preferences for dev auth (not for production)
        if data.password:
            user.preferences = {
                **user.preferences,
                "_password_hash": hash_password(data.password),
            }

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update_user(self, user_id: UUID, data: UserUpdate) -> User:
        user = await self.get_user(user_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def soft_delete_user(self, user_id: UUID) -> None:
        user = await self.get_user(user_id)
        user.deleted_at = func.now()
        await self.db.flush()
