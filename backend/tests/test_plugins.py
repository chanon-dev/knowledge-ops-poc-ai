"""Tests for plugin endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_plugins(client: AsyncClient, admin_headers: dict):
    resp = await client.get("/api/v1/plugins", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 3
    names = [p["name"] for p in data]
    assert "log-parser" in names


@pytest.mark.asyncio
async def test_execute_log_parser(client: AsyncClient, admin_headers: dict):
    resp = await client.post(
        "/api/v1/plugins/execute",
        headers=admin_headers,
        json={
            "plugin_name": "log-parser",
            "input_data": {"log_text": "ERROR Connection refused\nINFO OK"},
        },
    )
    assert resp.status_code == 200
    result = resp.json()["result"]
    assert result["errors"] == 1


@pytest.mark.asyncio
async def test_execute_config_validator(client: AsyncClient, admin_headers: dict):
    resp = await client.post(
        "/api/v1/plugins/execute",
        headers=admin_headers,
        json={
            "plugin_name": "config-validator",
            "input_data": {"config_text": '{"password": "secret123"}'},
        },
    )
    assert resp.status_code == 200
    assert resp.json()["result"]["valid"] is False


@pytest.mark.asyncio
async def test_execute_unknown_plugin(client: AsyncClient, admin_headers: dict):
    resp = await client.post(
        "/api/v1/plugins/execute",
        headers=admin_headers,
        json={"plugin_name": "nonexistent", "input_data": {}},
    )
    assert resp.status_code == 200
    assert "error" in resp.json()["result"]
