"""Tests for mcp-server-splunk-oncall."""

from __future__ import annotations

import json
import os

import pytest
import respx
from httpx import Response

os.environ["SPLUNK_ONCALL_API_ID"] = "test-id"
os.environ["SPLUNK_ONCALL_API_KEY"] = "test-key"

from mcp_server_splunk_oncall import server as srv


@pytest.fixture(autouse=True)
def reset_client():
    """Reset the global client between tests."""
    srv._client = None
    srv._access_detected = False
    yield
    srv._client = None
    srv._access_detected = False


def test_tool_count():
    """All 45 tools are registered."""
    assert len(srv.mcp._tool_manager._tools) == 45


def test_read_tools_present():
    tools = srv.mcp._tool_manager._tools
    read_tools = [
        "list_incidents", "get_oncall", "list_teams", "list_users",
        "list_routing_keys", "list_policies", "list_maintenance",
        "get_org_info", "get_access_mode", "list_alerts",
    ]
    for t in read_tools:
        assert t in tools, f"Missing read tool: {t}"


def test_write_tools_present():
    tools = srv.mcp._tool_manager._tools
    write_tools = [
        "acknowledge_incidents", "resolve_incidents", "reroute_incidents",
        "create_team", "delete_team", "create_user", "delete_user",
        "create_routing_key", "delete_routing_key", "create_policy",
        "delete_policy", "create_maintenance", "end_maintenance",
    ]
    for t in write_tools:
        assert t in tools, f"Missing write tool: {t}"


@pytest.mark.asyncio
@respx.mock
async def test_list_incidents():
    respx.post("https://api.victorops.com/api-public/v1/incidents/resolve").mock(
        return_value=Response(403)
    )
    respx.get("https://api.victorops.com/api-public/v1/incidents").mock(
        return_value=Response(200, json={"incidents": []})
    )
    result = await srv.list_incidents()
    data = json.loads(result)
    assert "incidents" in data


@pytest.mark.asyncio
@respx.mock
async def test_ro_detection():
    respx.post("https://api.victorops.com/api-public/v1/incidents/resolve").mock(
        return_value=Response(403)
    )
    result = await srv.get_access_mode()
    data = json.loads(result)
    assert "read-only" in data["access_mode"]


@pytest.mark.asyncio
@respx.mock
async def test_write_blocked_in_ro():
    respx.post("https://api.victorops.com/api-public/v1/incidents/resolve").mock(
        return_value=Response(403)
    )
    result = await srv.acknowledge_incidents("testuser", ["123"])
    assert "read-only" in result


@pytest.mark.asyncio
@respx.mock
async def test_full_access_detection():
    respx.post("https://api.victorops.com/api-public/v1/incidents/resolve").mock(
        return_value=Response(400)
    )
    result = await srv.get_access_mode()
    data = json.loads(result)
    assert data["access_mode"] == "full-access"


@pytest.mark.asyncio
async def test_forced_ro_mode():
    srv._client = None
    srv._access_detected = False
    original = os.environ.get("SPLUNK_ONCALL_READ_ONLY")
    os.environ["SPLUNK_ONCALL_READ_ONLY"] = "true"
    # Reload the flag
    srv._force_read_only = True
    try:
        result = await srv.get_access_mode()
        data = json.loads(result)
        assert "forced" in data["access_mode"]

        result = await srv.resolve_incidents("testuser", ["123"])
        assert "read-only mode" in result
    finally:
        srv._force_read_only = False
        if original is None:
            os.environ.pop("SPLUNK_ONCALL_READ_ONLY", None)
        else:
            os.environ["SPLUNK_ONCALL_READ_ONLY"] = original


@pytest.mark.asyncio
@respx.mock
async def test_get_oncall():
    respx.post("https://api.victorops.com/api-public/v1/incidents/resolve").mock(
        return_value=Response(400)
    )
    respx.get("https://api.victorops.com/api-public/v2/oncall/current").mock(
        return_value=Response(200, json={"teamsOnCall": []})
    )
    result = await srv.get_oncall()
    data = json.loads(result)
    assert "teamsOnCall" in data


@pytest.mark.asyncio
@respx.mock
async def test_list_teams():
    respx.post("https://api.victorops.com/api-public/v1/incidents/resolve").mock(
        return_value=Response(400)
    )
    respx.get("https://api.victorops.com/api-public/v1/team").mock(
        return_value=Response(200, json=[{"name": "test-team", "slug": "test-team"}])
    )
    result = await srv.list_teams()
    data = json.loads(result)
    assert isinstance(data, list)
