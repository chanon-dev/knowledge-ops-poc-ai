"""Tests for webhook endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_webhook(client: AsyncClient, admin_headers: dict):
    resp = await client.post(
        "/api/v1/webhooks",
        headers=admin_headers,
        json={"url": "https://example.com/hook", "events": ["query.created"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data


@pytest.mark.asyncio
async def test_list_webhooks(client: AsyncClient, admin_headers: dict):
    resp = await client.get("/api/v1/webhooks", headers=admin_headers)
    assert resp.status_code == 200
    assert "data" in resp.json()


@pytest.mark.asyncio
async def test_webhooks_unauthorized(client: AsyncClient):
    resp = await client.get("/api/v1/webhooks")
    assert resp.status_code in (401, 403)
