"""Tests for billing endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_subscription(client: AsyncClient, admin_headers: dict):
    resp = await client.get("/api/v1/billing/subscription", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "plan_tier" in data
    assert "status" in data


@pytest.mark.asyncio
async def test_get_quota(client: AsyncClient, admin_headers: dict):
    resp = await client.get("/api/v1/billing/quota", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "allowed" in data
    assert "query_limit" in data


@pytest.mark.asyncio
async def test_get_usage(client: AsyncClient, admin_headers: dict):
    resp = await client.get("/api/v1/billing/usage", headers=admin_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_invoices(client: AsyncClient, admin_headers: dict):
    resp = await client.get("/api/v1/billing/invoices", headers=admin_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_billing_unauthorized(client: AsyncClient):
    resp = await client.get("/api/v1/billing/subscription")
    assert resp.status_code in (401, 403)
