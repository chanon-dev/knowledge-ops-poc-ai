import pytest
from httpx import AsyncClient

from tests.conftest import TEST_DEPT_ID


@pytest.mark.asyncio
async def test_list_departments(client: AsyncClient, seeded_db, admin_headers):
    response = await client.get("/api/v1/departments", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) > 0
    assert data["data"][0]["name"] == "IT Operations"


@pytest.mark.asyncio
async def test_get_department(client: AsyncClient, seeded_db, admin_headers):
    response = await client.get(
        f"/api/v1/departments/{TEST_DEPT_ID}", headers=admin_headers
    )
    assert response.status_code == 200
    assert response.json()["slug"] == "it-ops"


@pytest.mark.asyncio
async def test_create_department(client: AsyncClient, seeded_db, admin_headers):
    response = await client.post(
        "/api/v1/departments",
        headers=admin_headers,
        json={
            "name": "HR Department",
            "slug": "hr-dept",
            "icon": "👥",
            "description": "Human Resources",
        },
    )
    assert response.status_code == 201
    assert response.json()["name"] == "HR Department"


@pytest.mark.asyncio
async def test_update_department(client: AsyncClient, seeded_db, admin_headers):
    response = await client.put(
        f"/api/v1/departments/{TEST_DEPT_ID}",
        headers=admin_headers,
        json={"name": "IT Operations Updated"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "IT Operations Updated"


@pytest.mark.asyncio
async def test_delete_department(client: AsyncClient, seeded_db, admin_headers):
    # First create one to delete
    create_resp = await client.post(
        "/api/v1/departments",
        headers=admin_headers,
        json={"name": "To Delete", "slug": "to-delete"},
    )
    dept_id = create_resp.json()["id"]

    response = await client.delete(
        f"/api/v1/departments/{dept_id}", headers=admin_headers
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_list_members(client: AsyncClient, seeded_db, admin_headers):
    response = await client.get(
        f"/api/v1/departments/{TEST_DEPT_ID}/members", headers=admin_headers
    )
    assert response.status_code == 200
    assert len(response.json()) > 0


@pytest.mark.asyncio
async def test_department_unauthorized(client: AsyncClient, seeded_db):
    response = await client.get("/api/v1/departments")
    assert response.status_code == 401
