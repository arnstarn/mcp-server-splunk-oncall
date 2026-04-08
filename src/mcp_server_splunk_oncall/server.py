"""MCP server for Splunk On-Call (VictorOps) incident management."""

from __future__ import annotations

import json
import os

from mcp.server.fastmcp import FastMCP

from .client import SplunkOnCallClient

mcp = FastMCP(
    "splunk-oncall",
    instructions="Manage Splunk On-Call (VictorOps) incidents, on-call schedules, and maintenance windows",
)

_client: SplunkOnCallClient | None = None


def _get_client() -> SplunkOnCallClient:
    global _client
    if _client is None:
        api_id = os.environ.get("SPLUNK_ONCALL_API_ID")
        api_key = os.environ.get("SPLUNK_ONCALL_API_KEY")
        if not api_id or not api_key:
            raise ValueError(
                "SPLUNK_ONCALL_API_ID and SPLUNK_ONCALL_API_KEY environment variables are required"
            )
        _client = SplunkOnCallClient(api_id, api_key)
    return _client


def _fmt(data: dict) -> str:
    return json.dumps(data, indent=2, default=str)


# -- Incidents --


@mcp.tool()
async def list_incidents() -> str:
    """List all current incidents (triggered, acknowledged, resolved)."""
    result = await _get_client().list_incidents()
    return _fmt(result)


@mcp.tool()
async def acknowledge_incidents(
    user_name: str, incident_numbers: list[str], message: str = "",
) -> str:
    """Acknowledge one or more incidents.

    Args:
        user_name: Your Splunk On-Call username
        incident_numbers: List of incident numbers to acknowledge (e.g. ["123", "456"])
        message: Optional message to attach to the acknowledgment
    """
    result = await _get_client().acknowledge_incidents(
        user_name, incident_numbers, message or None,
    )
    return _fmt(result)


@mcp.tool()
async def resolve_incidents(
    user_name: str, incident_numbers: list[str], message: str = "",
) -> str:
    """Resolve one or more incidents.

    Args:
        user_name: Your Splunk On-Call username
        incident_numbers: List of incident numbers to resolve (e.g. ["123", "456"])
        message: Optional message to attach to the resolution
    """
    result = await _get_client().resolve_incidents(
        user_name, incident_numbers, message or None,
    )
    return _fmt(result)


@mcp.tool()
async def reroute_incidents(
    user_name: str,
    incident_numbers: list[str],
    target_user: str = "",
    target_policy: str = "",
) -> str:
    """Reroute incidents to another user or escalation policy.

    Args:
        user_name: Your Splunk On-Call username
        incident_numbers: List of incident numbers to reroute
        target_user: Username to reroute to (provide this or target_policy)
        target_policy: Escalation policy slug to reroute to (provide this or target_user)
    """
    targets = []
    if target_user:
        targets.append({"type": "User", "slug": target_user})
    if target_policy:
        targets.append({"type": "EscalationPolicy", "slug": target_policy})
    if not targets:
        return "Error: provide either target_user or target_policy"
    result = await _get_client().reroute_incidents(user_name, incident_numbers, targets)
    return _fmt(result)


@mcp.tool()
async def get_incident_timeline(incident_number: str) -> str:
    """Get the event timeline for a specific incident.

    Args:
        incident_number: The incident number to get the timeline for
    """
    result = await _get_client().get_incident_timeline(incident_number)
    return _fmt(result)


# -- On-Call --


@mcp.tool()
async def get_oncall() -> str:
    """Get who is currently on call across all teams and policies."""
    result = await _get_client().get_oncall()
    return _fmt(result)


@mcp.tool()
async def get_team_oncall_schedule(
    team_slug: str, days_forward: int = 14,
) -> str:
    """Get the on-call schedule for a specific team.

    Args:
        team_slug: The team slug identifier
        days_forward: Number of days to look ahead (default 14)
    """
    result = await _get_client().get_team_oncall_schedule(team_slug, days_forward)
    return _fmt(result)


@mcp.tool()
async def get_user_oncall_schedule(user_name: str) -> str:
    """Get the on-call schedule for a specific user.

    Args:
        user_name: The username to look up
    """
    result = await _get_client().get_user_oncall_schedule(user_name)
    return _fmt(result)


# -- Teams --


@mcp.tool()
async def list_teams() -> str:
    """List all teams in the organization."""
    result = await _get_client().list_teams()
    return _fmt(result)


@mcp.tool()
async def get_team_members(team_slug: str) -> str:
    """List members of a specific team.

    Args:
        team_slug: The team slug identifier
    """
    result = await _get_client().get_team_members(team_slug)
    return _fmt(result)


@mcp.tool()
async def get_team_policies(team_slug: str) -> str:
    """List escalation policies for a specific team.

    Args:
        team_slug: The team slug identifier
    """
    result = await _get_client().get_team_policies(team_slug)
    return _fmt(result)


# -- Users --


@mcp.tool()
async def list_users() -> str:
    """List all users in the organization."""
    result = await _get_client().list_users()
    return _fmt(result)


@mcp.tool()
async def get_user(user_name: str) -> str:
    """Get details for a specific user.

    Args:
        user_name: The username to look up
    """
    result = await _get_client().get_user(user_name)
    return _fmt(result)


# -- Routing Keys --


@mcp.tool()
async def list_routing_keys() -> str:
    """List all routing keys and their associated escalation policies."""
    result = await _get_client().list_routing_keys()
    return _fmt(result)


# -- Escalation Policies --


@mcp.tool()
async def list_policies() -> str:
    """List all escalation policies in the organization."""
    result = await _get_client().list_policies()
    return _fmt(result)


@mcp.tool()
async def get_policy(policy_slug: str) -> str:
    """Get details for a specific escalation policy.

    Args:
        policy_slug: The escalation policy slug
    """
    result = await _get_client().get_policy(policy_slug)
    return _fmt(result)


# -- Maintenance Mode --


@mcp.tool()
async def list_maintenance() -> str:
    """List all active and scheduled maintenance windows."""
    result = await _get_client().list_maintenance()
    return _fmt(result)


@mcp.tool()
async def create_maintenance(
    routing_keys: list[str],
    purpose: str,
    end_date: str = "",
    start_date: str = "",
) -> str:
    """Create a maintenance window to suppress alerts.

    Args:
        routing_keys: List of routing key names to suppress alerts for
        purpose: Description of why maintenance is being performed
        end_date: ISO 8601 end time (e.g. "2026-04-09T06:00:00Z"). Required.
        start_date: ISO 8601 start time. Defaults to now if omitted.
    """
    if not end_date:
        return "Error: end_date is required"
    result = await _get_client().create_maintenance(
        names=routing_keys,
        purpose=purpose,
        start_date=start_date or None,
        end_date=end_date,
    )
    return _fmt(result)


@mcp.tool()
async def end_maintenance(maintenance_id: str) -> str:
    """End a maintenance window early.

    Args:
        maintenance_id: The maintenance window ID to end
    """
    result = await _get_client().end_maintenance(maintenance_id)
    return _fmt(result)


# -- Organization --


@mcp.tool()
async def get_org_info() -> str:
    """Get organization information."""
    result = await _get_client().get_org()
    return _fmt(result)


# -- Reporting --


@mcp.tool()
async def get_incident_history(start: str = "", end: str = "") -> str:
    """Get historical incident data for reporting.

    Args:
        start: ISO 8601 start time filter (e.g. "2026-04-01T00:00:00Z")
        end: ISO 8601 end time filter (e.g. "2026-04-08T00:00:00Z")
    """
    result = await _get_client().get_incident_history(
        start=start or None, end=end or None,
    )
    return _fmt(result)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
