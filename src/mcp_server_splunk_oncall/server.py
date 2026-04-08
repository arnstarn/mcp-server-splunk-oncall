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
_access_detected: bool = False
_force_read_only: bool = os.environ.get("SPLUNK_ONCALL_READ_ONLY", "").lower() in (
    "1", "true", "yes",
)


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
        if _force_read_only:
            _client._read_only = True
    return _client


async def _ensure_access_detected() -> None:
    global _access_detected
    if not _access_detected:
        if not _force_read_only:
            await _get_client().detect_access_mode()
        _access_detected = True


def _require_write(action: str) -> str | None:
    """Return an error message if the key is read-only, None if write is allowed."""
    client = _get_client()
    if _force_read_only:
        return (
            f"Cannot {action}: server is running in read-only mode "
            f"(SPLUNK_ONCALL_READ_ONLY=true). Restart with a writable configuration."
        )
    if client.is_read_only:
        return (
            f"Cannot {action}: current API key is read-only. "
            f"Use a full-access API key to perform write operations."
        )
    return None


def _fmt(data: dict) -> str:
    return json.dumps(data, indent=2, default=str)


# -- Access Mode --


@mcp.tool()
async def get_access_mode() -> str:
    """Check whether the server is running in full-access or read-only mode."""
    await _ensure_access_detected()
    client = _get_client()
    if _force_read_only:
        mode = "read-only (forced via SPLUNK_ONCALL_READ_ONLY)"
    elif client.is_read_only:
        mode = "read-only (detected from API key)"
    else:
        mode = "full-access"
    return json.dumps({"access_mode": mode})


# -- Incidents --


@mcp.tool()
async def list_incidents() -> str:
    """List all current incidents (triggered, acknowledged, resolved)."""
    await _ensure_access_detected()
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
    await _ensure_access_detected()
    if err := _require_write("acknowledge incidents"):
        return err
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
    await _ensure_access_detected()
    if err := _require_write("resolve incidents"):
        return err
    result = await _get_client().resolve_incidents(
        user_name, incident_numbers, message or None,
    )
    return _fmt(result)


@mcp.tool()
async def acknowledge_all_incidents(user_name: str) -> str:
    """Acknowledge all currently triggered incidents.

    Args:
        user_name: Your Splunk On-Call username
    """
    await _ensure_access_detected()
    if err := _require_write("acknowledge all incidents"):
        return err
    result = await _get_client().acknowledge_all_incidents(user_name)
    return _fmt(result)


@mcp.tool()
async def resolve_all_incidents(user_name: str) -> str:
    """Resolve all currently triggered incidents.

    Args:
        user_name: Your Splunk On-Call username
    """
    await _ensure_access_detected()
    if err := _require_write("resolve all incidents"):
        return err
    result = await _get_client().resolve_all_incidents(user_name)
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
    await _ensure_access_detected()
    if err := _require_write("reroute incidents"):
        return err
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
    await _ensure_access_detected()
    result = await _get_client().get_incident_timeline(incident_number)
    return _fmt(result)


# -- On-Call --


@mcp.tool()
async def get_oncall() -> str:
    """Get who is currently on call across all teams and policies."""
    await _ensure_access_detected()
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
    await _ensure_access_detected()
    result = await _get_client().get_team_oncall_schedule(team_slug, days_forward)
    return _fmt(result)


@mcp.tool()
async def get_user_oncall_schedule(user_name: str) -> str:
    """Get the on-call schedule for a specific user.

    Args:
        user_name: The username to look up
    """
    await _ensure_access_detected()
    result = await _get_client().get_user_oncall_schedule(user_name)
    return _fmt(result)


# -- Teams --


@mcp.tool()
async def list_teams() -> str:
    """List all teams in the organization."""
    await _ensure_access_detected()
    result = await _get_client().list_teams()
    return _fmt(result)


@mcp.tool()
async def get_team(team_slug: str) -> str:
    """Get details for a specific team.

    Args:
        team_slug: The team slug identifier
    """
    await _ensure_access_detected()
    result = await _get_client().get_team(team_slug)
    return _fmt(result)


@mcp.tool()
async def create_team(name: str) -> str:
    """Create a new team.

    Args:
        name: The team name
    """
    await _ensure_access_detected()
    if err := _require_write("create team"):
        return err
    result = await _get_client().create_team(name)
    return _fmt(result)


@mcp.tool()
async def update_team(team_slug: str, name: str) -> str:
    """Update a team's name.

    Args:
        team_slug: The team slug identifier
        name: The new team name
    """
    await _ensure_access_detected()
    if err := _require_write("update team"):
        return err
    result = await _get_client().update_team(team_slug, name)
    return _fmt(result)


@mcp.tool()
async def delete_team(team_slug: str) -> str:
    """Delete a team.

    Args:
        team_slug: The team slug identifier
    """
    await _ensure_access_detected()
    if err := _require_write("delete team"):
        return err
    result = await _get_client().delete_team(team_slug)
    return _fmt(result)


@mcp.tool()
async def get_team_members(team_slug: str) -> str:
    """List members of a specific team.

    Args:
        team_slug: The team slug identifier
    """
    await _ensure_access_detected()
    result = await _get_client().get_team_members(team_slug)
    return _fmt(result)


@mcp.tool()
async def add_team_member(team_slug: str, user_name: str) -> str:
    """Add a user to a team.

    Args:
        team_slug: The team slug identifier
        user_name: The username to add
    """
    await _ensure_access_detected()
    if err := _require_write("add team member"):
        return err
    result = await _get_client().add_team_member(team_slug, user_name)
    return _fmt(result)


@mcp.tool()
async def remove_team_member(team_slug: str, user_name: str) -> str:
    """Remove a user from a team.

    Args:
        team_slug: The team slug identifier
        user_name: The username to remove
    """
    await _ensure_access_detected()
    if err := _require_write("remove team member"):
        return err
    result = await _get_client().remove_team_member(team_slug, user_name)
    return _fmt(result)


@mcp.tool()
async def get_team_admins(team_slug: str) -> str:
    """List admins of a specific team.

    Args:
        team_slug: The team slug identifier
    """
    await _ensure_access_detected()
    result = await _get_client().get_team_admins(team_slug)
    return _fmt(result)


@mcp.tool()
async def get_team_policies(team_slug: str) -> str:
    """List escalation policies for a specific team.

    Args:
        team_slug: The team slug identifier
    """
    await _ensure_access_detected()
    result = await _get_client().get_team_policies(team_slug)
    return _fmt(result)


# -- Users --


@mcp.tool()
async def list_users() -> str:
    """List all users in the organization."""
    await _ensure_access_detected()
    result = await _get_client().list_users()
    return _fmt(result)


@mcp.tool()
async def get_user(user_name: str) -> str:
    """Get details for a specific user.

    Args:
        user_name: The username to look up
    """
    await _ensure_access_detected()
    result = await _get_client().get_user(user_name)
    return _fmt(result)


@mcp.tool()
async def create_user(
    first_name: str, last_name: str, user_name: str, email: str,
) -> str:
    """Create (invite) a new user.

    Args:
        first_name: User's first name
        last_name: User's last name
        user_name: Desired username
        email: User's email address
    """
    await _ensure_access_detected()
    if err := _require_write("create user"):
        return err
    result = await _get_client().create_user(first_name, last_name, user_name, email)
    return _fmt(result)


@mcp.tool()
async def delete_user(user_name: str, replacement: str) -> str:
    """Delete a user. Requires a replacement user for their on-call shifts.

    Args:
        user_name: The username to delete
        replacement: Username who will take over on-call responsibilities
    """
    await _ensure_access_detected()
    if err := _require_write("delete user"):
        return err
    result = await _get_client().delete_user(user_name, replacement)
    return _fmt(result)


@mcp.tool()
async def get_user_contact_methods(user_name: str) -> str:
    """List contact methods (phone, email, SMS) for a user.

    Args:
        user_name: The username to look up
    """
    await _ensure_access_detected()
    result = await _get_client().get_user_contact_methods(user_name)
    return _fmt(result)


@mcp.tool()
async def get_user_devices(user_name: str) -> str:
    """List push notification devices for a user.

    Args:
        user_name: The username to look up
    """
    await _ensure_access_detected()
    result = await _get_client().get_user_devices(user_name)
    return _fmt(result)


@mcp.tool()
async def get_user_policies(user_name: str) -> str:
    """Get escalation policies a user belongs to.

    Args:
        user_name: The username to look up
    """
    await _ensure_access_detected()
    result = await _get_client().get_user_policies(user_name)
    return _fmt(result)


@mcp.tool()
async def get_user_teams(user_name: str) -> str:
    """Get teams a user belongs to.

    Args:
        user_name: The username to look up
    """
    await _ensure_access_detected()
    result = await _get_client().get_user_teams(user_name)
    return _fmt(result)


# -- Routing Keys --


@mcp.tool()
async def list_routing_keys() -> str:
    """List all routing keys and their associated escalation policies."""
    await _ensure_access_detected()
    result = await _get_client().list_routing_keys()
    return _fmt(result)


@mcp.tool()
async def create_routing_key(routing_key: str, targets: list[dict]) -> str:
    """Create a new routing key.

    Args:
        routing_key: The routing key name
        targets: List of target dicts, e.g. [{"policySlug": "my-policy", "type": "escalationPolicy"}]
    """
    await _ensure_access_detected()
    if err := _require_write("create routing key"):
        return err
    result = await _get_client().create_routing_key(routing_key, targets)
    return _fmt(result)


@mcp.tool()
async def delete_routing_key(routing_key: str) -> str:
    """Delete a routing key.

    Args:
        routing_key: The routing key name to delete
    """
    await _ensure_access_detected()
    if err := _require_write("delete routing key"):
        return err
    result = await _get_client().delete_routing_key(routing_key)
    return _fmt(result)


# -- Escalation Policies --


@mcp.tool()
async def list_policies() -> str:
    """List all escalation policies in the organization."""
    await _ensure_access_detected()
    result = await _get_client().list_policies()
    return _fmt(result)


@mcp.tool()
async def get_policy(policy_slug: str) -> str:
    """Get details for a specific escalation policy.

    Args:
        policy_slug: The escalation policy slug
    """
    await _ensure_access_detected()
    result = await _get_client().get_policy(policy_slug)
    return _fmt(result)


@mcp.tool()
async def create_policy(name: str, team_slug: str, steps: list[dict]) -> str:
    """Create a new escalation policy.

    Args:
        name: Policy name
        team_slug: Team slug to associate with
        steps: List of escalation step dicts
    """
    await _ensure_access_detected()
    if err := _require_write("create escalation policy"):
        return err
    result = await _get_client().create_policy(name, team_slug, steps)
    return _fmt(result)


@mcp.tool()
async def delete_policy(policy_slug: str) -> str:
    """Delete an escalation policy.

    Args:
        policy_slug: The escalation policy slug to delete
    """
    await _ensure_access_detected()
    if err := _require_write("delete escalation policy"):
        return err
    result = await _get_client().delete_policy(policy_slug)
    return _fmt(result)


# -- Maintenance Mode --


@mcp.tool()
async def list_maintenance() -> str:
    """List all active and scheduled maintenance windows."""
    await _ensure_access_detected()
    result = await _get_client().list_maintenance()
    return _fmt(result)


@mcp.tool()
async def get_maintenance(maintenance_id: str) -> str:
    """Get details for a specific maintenance window.

    Args:
        maintenance_id: The maintenance window ID
    """
    await _ensure_access_detected()
    result = await _get_client().get_maintenance(maintenance_id)
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
    await _ensure_access_detected()
    if err := _require_write("create maintenance window"):
        return err
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
    await _ensure_access_detected()
    if err := _require_write("end maintenance window"):
        return err
    result = await _get_client().end_maintenance(maintenance_id)
    return _fmt(result)


# -- Organization --


@mcp.tool()
async def get_org_info() -> str:
    """Get organization information."""
    await _ensure_access_detected()
    result = await _get_client().get_org()
    return _fmt(result)


@mcp.tool()
async def get_org_timeline() -> str:
    """Get organization-wide timeline of events."""
    await _ensure_access_detected()
    result = await _get_client().get_org_timeline()
    return _fmt(result)


# -- Alerts --


@mcp.tool()
async def list_alerts() -> str:
    """List recent alerts."""
    await _ensure_access_detected()
    result = await _get_client().list_alerts()
    return _fmt(result)


# -- Reporting --


@mcp.tool()
async def get_incident_history(start: str = "", end: str = "") -> str:
    """Get historical incident data for reporting.

    Args:
        start: ISO 8601 start time filter (e.g. "2026-04-01T00:00:00Z")
        end: ISO 8601 end time filter (e.g. "2026-04-08T00:00:00Z")
    """
    await _ensure_access_detected()
    result = await _get_client().get_incident_history(
        start=start or None, end=end or None,
    )
    return _fmt(result)


@mcp.tool()
async def get_oncall_report(team_slug: str, start: str = "", end: str = "") -> str:
    """Get on-call report for a team over a time period.

    Args:
        team_slug: The team slug identifier
        start: ISO 8601 start time
        end: ISO 8601 end time
    """
    await _ensure_access_detected()
    result = await _get_client().get_oncall_report(
        team_slug, start=start or None, end=end or None,
    )
    return _fmt(result)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
