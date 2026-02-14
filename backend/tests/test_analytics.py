"""Tests for analytics endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_usage_overview(client: AsyncClient, admin_headers: dict):
    resp = await client.get("/api/v1/analytics/usage", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_queries" in data
    assert "active_users" in data


@pytest.mark.asyncio
async def test_get_ai_performance(client: AsyncClient, admin_headers: dict):
    resp = await client.get("/api/v1/analytics/ai-performance", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "avg_latency_ms" in data
    assert "drift_detected" in data


@pytest.mark.asyncio
async def test_get_top_topics(client: AsyncClient, admin_headers: dict):
    resp = await client.get("/api/v1/analytics/top-topics", headers=admin_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_team_productivity(client: AsyncClient, admin_headers: dict):
    resp = await client.get("/api/v1/analytics/team-productivity", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "self_service_rate" in data


@pytest.mark.asyncio
async def test_export_analytics(client: AsyncClient, admin_headers: dict):
    resp = await client.get("/api/v1/analytics/export", headers=admin_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_analytics_unauthorized(client: AsyncClient):
    resp = await client.get("/api/v1/analytics/usage")
    assert resp.status_code in (401, 403)
