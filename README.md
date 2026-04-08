# mcp-server-splunk-oncall

MCP server for Splunk On-Call (VictorOps) incident management. Provides tools for managing incidents, on-call schedules, maintenance windows, and team operations from any MCP client.

## Installation

```bash
uvx mcp-server-splunk-oncall
```

Or install from PyPI:

```bash
pip install mcp-server-splunk-oncall
```

## Configuration

The server requires two environment variables:

- `SPLUNK_ONCALL_API_ID` - Your Splunk On-Call API ID
- `SPLUNK_ONCALL_API_KEY` - Your Splunk On-Call API key

### Claude Code

Add to your Claude Code MCP settings:

```json
{
  "mcpServers": {
    "splunk-oncall": {
      "command": "uvx",
      "args": ["mcp-server-splunk-oncall"],
      "env": {
        "SPLUNK_ONCALL_API_ID": "your-api-id",
        "SPLUNK_ONCALL_API_KEY": "your-api-key"
      }
    }
  }
}
```

For read-only access, use a read-only API key. For full access (acknowledge, resolve, reroute incidents), use a full-access API key.

## Available Tools

### Incidents
- `list_incidents` - List all current incidents
- `acknowledge_incidents` - Acknowledge incidents by number
- `resolve_incidents` - Resolve incidents by number
- `reroute_incidents` - Reroute incidents to another user or policy
- `get_incident_timeline` - Get event timeline for an incident
- `get_incident_history` - Query historical incident data

### On-Call
- `get_oncall` - Who is currently on call across all teams
- `get_team_oncall_schedule` - On-call schedule for a team
- `get_user_oncall_schedule` - On-call schedule for a user

### Teams and Users
- `list_teams` - List all teams
- `get_team_members` - List members of a team
- `get_team_policies` - List escalation policies for a team
- `list_users` - List all users
- `get_user` - Get user details

### Routing and Policies
- `list_routing_keys` - List routing keys and their policies
- `list_policies` - List all escalation policies
- `get_policy` - Get escalation policy details

### Maintenance
- `list_maintenance` - List active and scheduled maintenance windows
- `create_maintenance` - Create a maintenance window
- `end_maintenance` - End a maintenance window early

### Organization
- `get_org_info` - Get organization information

## License

MIT
