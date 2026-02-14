import pytest
from httpx import AsyncClient

from tests.conftest import TEST_ADMIN_ID, TEST_MEMBER_ID


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient, seeded_db, admin_headers):
    response = await client.get("/api/v1/users", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 2


@pytest.mark.asyncio
async def test_get_user(client: AsyncClient, seeded_db, admin_headers):
    response = await client.get(
        f"/api/v1/users/{TEST_ADMIN_ID}", headers=admin_headers
    )
    assert response.status_code == 200
    assert response.json()["email"] == "admin@test.com"


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient, seeded_db, admin_headers):
    response = await client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "email": "newuser@test.com",
            "full_name": "New User",
            "role": "member",
            "password": "password123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@test.com"
    assert "_password_hash" not in str(data.get("preferences", {}))


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient, seeded_db, admin_headers):
    response = await client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "email": "admin@test.com",
            "full_name": "Duplicate",
            "role": "member",
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, seeded_db, admin_headers):
    response = await client.get("/api/v1/users/me", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["role"] == "owner"


@pytest.mark.asyncio
async def test_update_me(client: AsyncClient, seeded_db, admin_headers):
    response = await client.put(
        "/api/v1/users/me",
        headers=admin_headers,
        json={"full_name": "Updated Admin"},
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Admin"


@pytest.mark.asyncio
async def test_member_cannot_list_users(client: AsyncClient, seeded_db, member_headers):
    response = await client.get("/api/v1/users", headers=member_headers)
    assert response.status_code == 403
