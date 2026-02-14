"""Seed data script for development.

Run: cd backend && python -m app.db.seed
"""
import asyncio
from uuid import UUID

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.department import Department, DepartmentMember
from app.models.tenant import Tenant
from app.models.user import User

# Fixed UUIDs for predictable dev data
DEMO_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
ADMIN_USER_ID = UUID("00000000-0000-0000-0000-000000000010")
MEMBER_USER_ID = UUID("00000000-0000-0000-0000-000000000011")
IT_OPS_DEPT_ID = UUID("00000000-0000-0000-0000-000000000100")
HR_DEPT_ID = UUID("00000000-0000-0000-0000-000000000101")
LEGAL_DEPT_ID = UUID("00000000-0000-0000-0000-000000000102")


async def seed():
    async with SessionLocal() as db:
        # Check if already seeded
        existing = await db.execute(select(Tenant).where(Tenant.id == DEMO_TENANT_ID))
        if existing.scalar_one_or_none():
            print("Seed data already exists. Skipping.")
            return

        # 1. Create demo tenant
        tenant = Tenant(
            id=DEMO_TENANT_ID,
            name="Demo Corp",
            slug="demo-corp",
            plan_tier="enterprise",
            status="active",
            settings={
                "logo_url": None,
                "timezone": "Asia/Bangkok",
                "language": "th",
                "features": {
                    "vision": True,
                    "custom_model": True,
                    "approval_workflow": True,
                },
            },
        )
        db.add(tenant)

        # 2. Create admin user
        admin = User(
            id=ADMIN_USER_ID,
            tenant_id=DEMO_TENANT_ID,
            email="admin@demo.com",
            full_name="Admin User",
            role="owner",
            preferences={
                "_password_hash": hash_password("admin123"),
                "theme": "light",
                "language": "th",
            },
        )
        db.add(admin)

        # 3. Create member user
        member = User(
            id=MEMBER_USER_ID,
            tenant_id=DEMO_TENANT_ID,
            email="member@demo.com",
            full_name="Member User",
            role="member",
            preferences={
                "_password_hash": hash_password("member123"),
                "theme": "light",
                "language": "th",
            },
        )
        db.add(member)

        # 4. Create departments
        it_ops = Department(
            id=IT_OPS_DEPT_ID,
            tenant_id=DEMO_TENANT_ID,
            name="IT Operations",
            slug="it-ops",
            icon="🖥️",
            description="Server, network, and infrastructure troubleshooting",
            config={
                "model": "llama3-8b",
                "confidence_threshold": 0.85,
                "auto_approve": False,
                "system_prompt": "You are an IT operations expert specializing in server, network, and infrastructure troubleshooting.",
            },
            sort_order=0,
        )
        db.add(it_ops)

        hr = Department(
            id=HR_DEPT_ID,
            tenant_id=DEMO_TENANT_ID,
            name="Human Resources",
            slug="hr",
            icon="👥",
            description="HR policies, benefits, and onboarding",
            config={
                "model": "llama3-8b",
                "confidence_threshold": 0.80,
                "auto_approve": False,
                "system_prompt": "You are an HR expert specializing in company policies, benefits, and employee onboarding.",
            },
            sort_order=1,
        )
        db.add(hr)

        legal = Department(
            id=LEGAL_DEPT_ID,
            tenant_id=DEMO_TENANT_ID,
            name="Legal & Compliance",
            slug="legal",
            icon="⚖️",
            description="Contracts, compliance, and legal Q&A",
            config={
                "model": "llama3-8b",
                "confidence_threshold": 0.90,
                "auto_approve": False,
                "system_prompt": "You are a legal expert specializing in contracts, compliance, and corporate governance.",
            },
            sort_order=2,
        )
        db.add(legal)

        await db.flush()

        # 5. Create department memberships
        memberships = [
            DepartmentMember(department_id=IT_OPS_DEPT_ID, user_id=ADMIN_USER_ID, tenant_id=DEMO_TENANT_ID, role="lead"),
            DepartmentMember(department_id=IT_OPS_DEPT_ID, user_id=MEMBER_USER_ID, tenant_id=DEMO_TENANT_ID, role="member"),
            DepartmentMember(department_id=HR_DEPT_ID, user_id=ADMIN_USER_ID, tenant_id=DEMO_TENANT_ID, role="approver"),
            DepartmentMember(department_id=LEGAL_DEPT_ID, user_id=ADMIN_USER_ID, tenant_id=DEMO_TENANT_ID, role="approver"),
        ]
        for m in memberships:
            db.add(m)

        await db.commit()
        print("Seed data created successfully!")
        print(f"  Tenant: Demo Corp ({DEMO_TENANT_ID})")
        print(f"  Admin:  admin@demo.com / admin123")
        print(f"  Member: member@demo.com / member123")
        print(f"  Departments: IT Ops, HR, Legal")


if __name__ == "__main__":
    asyncio.run(seed())
