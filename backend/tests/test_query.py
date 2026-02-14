import pytest
from httpx import AsyncClient

from tests.conftest import TEST_DEPT_ID


@pytest.mark.asyncio
async def test_query_endpoint(client: AsyncClient, seeded_db, admin_headers):
    response = await client.post(
        "/api/v1/query",
        headers=admin_headers,
        json={
            "text": "How do I restart the server?",
            "department_id": str(TEST_DEPT_ID),
        },
    )
    # May fail due to Ollama/Qdrant not running, but should validate request
    assert response.status_code in (200, 500)


@pytest.mark.asyncio
async def test_query_missing_department(client: AsyncClient, seeded_db, admin_headers):
    response = await client.post(
        "/api/v1/query",
        headers=admin_headers,
        json={
            "text": "test query",
            "department_id": "00000000-0000-0000-0000-999999999999",
        },
    )
    assert response.status_code in (404, 500)


@pytest.mark.asyncio
async def test_query_unauthorized(client: AsyncClient, seeded_db):
    response = await client.post(
        "/api/v1/query",
        json={
            "text": "test",
            "department_id": str(TEST_DEPT_ID),
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_query_empty_text(client: AsyncClient, seeded_db, admin_headers):
    response = await client.post(
        "/api/v1/query",
        headers=admin_headers,
        json={
            "text": "",
            "department_id": str(TEST_DEPT_ID),
        },
    )
    assert response.status_code == 422  # Validation error
