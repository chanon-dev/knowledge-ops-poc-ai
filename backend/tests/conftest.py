import asyncio
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token, hash_password
from app.db.base_class import Base
from app.main import app

# Test database URL (in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSession = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

# Fixed test UUIDs
TEST_TENANT_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_ADMIN_ID = UUID("00000000-0000-0000-0000-000000000010")
TEST_MEMBER_ID = UUID("00000000-0000-0000-0000-000000000011")
TEST_DEPT_ID = UUID("00000000-0000-0000-0000-000000000100")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSession() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def seeded_db(db: AsyncSession):
    from app.models.department import Department, DepartmentMember
    from app.models.tenant import Tenant
    from app.models.user import User

    tenant = Tenant(
        id=TEST_TENANT_ID,
        name="Test Corp",
        slug="test-corp",
        plan_tier="enterprise",
        status="active",
        settings={},
    )
    db.add(tenant)

    admin = User(
        id=TEST_ADMIN_ID,
        tenant_id=TEST_TENANT_ID,
        email="admin@test.com",
        full_name="Admin User",
        role="owner",
        preferences={"_password_hash": hash_password("admin123")},
    )
    db.add(admin)

    member = User(
        id=TEST_MEMBER_ID,
        tenant_id=TEST_TENANT_ID,
        email="member@test.com",
        full_name="Member User",
        role="member",
        preferences={"_password_hash": hash_password("member123")},
    )
    db.add(member)

    dept = Department(
        id=TEST_DEPT_ID,
        tenant_id=TEST_TENANT_ID,
        name="IT Operations",
        slug="it-ops",
        icon="🖥️",
        config={"model": "llama3:8b", "confidence_threshold": 0.85},
    )
    db.add(dept)

    membership = DepartmentMember(
        department_id=TEST_DEPT_ID,
        user_id=TEST_ADMIN_ID,
        tenant_id=TEST_TENANT_ID,
        role="lead",
    )
    db.add(membership)

    await db.commit()
    yield db


def make_auth_header(user_id: UUID = TEST_ADMIN_ID, role: str = "owner") -> dict:
    token = create_access_token(
        data={
            "sub": str(user_id),
            "tenant_id": str(TEST_TENANT_ID),
            "email": "admin@test.com",
            "role": role,
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
def admin_headers():
    return make_auth_header(TEST_ADMIN_ID, "owner")


@pytest_asyncio.fixture
def member_headers():
    return make_auth_header(TEST_MEMBER_ID, "member")
