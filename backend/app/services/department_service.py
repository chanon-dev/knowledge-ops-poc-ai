from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.department import Department, DepartmentMember
from app.schemas.department import (
    DepartmentCreate,
    DepartmentMemberCreate,
    DepartmentUpdate,
)


class DepartmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_departments(
        self, tenant_id: UUID, page: int = 1, per_page: int = 20
    ) -> tuple[list[Department], int]:
        base = select(Department).where(
            Department.tenant_id == tenant_id, Department.deleted_at.is_(None)
        )
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = (
            base.order_by(Department.sort_order.asc(), Department.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def get_department(self, department_id: UUID) -> Department:
        stmt = select(Department).where(
            Department.id == department_id, Department.deleted_at.is_(None)
        )
        result = await self.db.execute(stmt)
        dept = result.scalar_one_or_none()
        if not dept:
            raise NotFoundError(f"Department {department_id} not found")
        return dept

    async def create_department(
        self, tenant_id: UUID, data: DepartmentCreate
    ) -> Department:
        existing = await self.db.execute(
            select(Department).where(
                Department.tenant_id == tenant_id,
                Department.slug == data.slug,
                Department.deleted_at.is_(None),
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Department with slug '{data.slug}' already exists in this tenant")

        dept = Department(tenant_id=tenant_id, **data.model_dump())
        self.db.add(dept)
        await self.db.flush()
        await self.db.refresh(dept)
        return dept

    async def update_department(
        self, department_id: UUID, data: DepartmentUpdate
    ) -> Department:
        dept = await self.get_department(department_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(dept, field, value)
        await self.db.flush()
        await self.db.refresh(dept)
        return dept

    async def soft_delete_department(self, department_id: UUID) -> None:
        dept = await self.get_department(department_id)
        dept.deleted_at = func.now()
        await self.db.flush()

    async def list_members(
        self, department_id: UUID
    ) -> list[DepartmentMember]:
        stmt = select(DepartmentMember).where(
            DepartmentMember.department_id == department_id
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def add_member(
        self, department_id: UUID, tenant_id: UUID, data: DepartmentMemberCreate
    ) -> DepartmentMember:
        # Check if already a member
        existing = await self.db.execute(
            select(DepartmentMember).where(
                DepartmentMember.department_id == department_id,
                DepartmentMember.user_id == data.user_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError("User is already a member of this department")

        member = DepartmentMember(
            department_id=department_id,
            tenant_id=tenant_id,
            user_id=data.user_id,
            role=data.role,
        )
        self.db.add(member)
        await self.db.flush()
        await self.db.refresh(member)
        return member

    async def remove_member(
        self, department_id: UUID, user_id: UUID
    ) -> None:
        stmt = select(DepartmentMember).where(
            DepartmentMember.department_id == department_id,
            DepartmentMember.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        member = result.scalar_one_or_none()
        if not member:
            raise NotFoundError("Member not found in this department")
        await self.db.delete(member)
        await self.db.flush()
