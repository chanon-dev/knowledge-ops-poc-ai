import pytest
from httpx import AsyncClient

from tests.conftest import TEST_TENANT_ID


@pytest.mark.asyncio
async def test_list_tenants(client: AsyncClient, seeded_db, admin_headers):
    response = await client.get("/api/v1/tenants", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "pagination" in data
    assert len(data["data"]) > 0


@pytest.mark.asyncio
async def test_get_tenant(client: AsyncClient, seeded_db, admin_headers):
    response = await client.get(
        f"/api/v1/tenants/{TEST_TENANT_ID}", headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Corp"
    assert data["slug"] == "test-corp"


@pytest.mark.asyncio
async def test_create_tenant(client: AsyncClient, seeded_db, admin_headers):
    response = await client.post(
        "/api/v1/tenants",
        headers=admin_headers,
        json={
            "name": "New Tenant",
            "slug": "new-tenant",
            "plan_tier": "free",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Tenant"
    assert data["slug"] == "new-tenant"


@pytest.mark.asyncio
async def test_create_tenant_duplicate_slug(client: AsyncClient, seeded_db, admin_headers):
    response = await client.post(
        "/api/v1/tenants",
        headers=admin_headers,
        json={
            "name": "Duplicate",
            "slug": "test-corp",  # Already exists
            "plan_tier": "free",
        },
    )
    assert response.status_code == 409
