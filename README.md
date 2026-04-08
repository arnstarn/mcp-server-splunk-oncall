# mcp-server-splunk-oncall

[![PyPI version](https://img.shields.io/pypi/v/mcp-server-splunk-oncall)](https://pypi.org/project/mcp-server-splunk-oncall/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

MCP server for the [Splunk On-Call (VictorOps)](https://www.splunk.com/en_us/products/on-call.html) API. Full coverage of the REST API with automatic read-only detection.

## Tools (45)

### Access

| Tool | Description |
|------|-------------|
| `get_access_mode` | Check if API key is full-access or read-only |

### Incidents

| Tool | Description |
|------|-------------|
| `list_incidents` | List all current incidents |
| `acknowledge_incidents` | Acknowledge incidents by number |
| `resolve_incidents` | Resolve incidents by number |
| `acknowledge_all_incidents` | Acknowledge all triggered incidents |
| `resolve_all_incidents` | Resolve all triggered incidents |
| `reroute_incidents` | Reroute incidents to another user or policy |
| `get_incident_timeline` | Get event timeline for an incident |

### On-Call

| Tool | Description |
|------|-------------|
| `get_oncall` | Who is currently on call across all teams |
| `get_team_oncall_schedule` | On-call schedule for a team |
| `get_user_oncall_schedule` | On-call schedule for a user |

### Teams

| Tool | Description |
|------|-------------|
| `list_teams` | List all teams |
| `get_team` | Get team details |
| `create_team` | Create a new team |
| `update_team` | Update a team name |
| `delete_team` | Delete a team |
| `get_team_members` | List members of a team |
| `add_team_member` | Add a user to a team |
| `remove_team_member` | Remove a user from a team |
| `get_team_admins` | List team admins |
| `get_team_policies` | List escalation policies for a team |

### Users

| Tool | Description |
|------|-------------|
| `list_users` | List all users |
| `get_user` | Get user details |
| `create_user` | Invite a new user |
| `delete_user` | Delete a user (with replacement) |
| `get_user_contact_methods` | List contact methods (phone, email, SMS) |
| `get_user_devices` | List push notification devices |
| `get_user_oncall_schedule` | User on-call schedule |
| `get_user_policies` | User escalation policies |
| `get_user_teams` | User team memberships |

### Routing Keys

| Tool | Description |
|------|-------------|
| `list_routing_keys` | List routing keys and their policies |
| `create_routing_key` | Create a routing key |
| `delete_routing_key` | Delete a routing key |

### Escalation Policies

| Tool | Description |
|------|-------------|
| `list_policies` | List all escalation policies |
| `get_policy` | Get escalation policy details |
| `create_policy` | Create an escalation policy |
| `delete_policy` | Delete an escalation policy |

### Maintenance

| Tool | Description |
|------|-------------|
| `list_maintenance` | List maintenance windows |
| `get_maintenance` | Get maintenance window details |
| `create_maintenance` | Create a maintenance window |
| `end_maintenance` | End a maintenance window early |

### Organization

| Tool | Description |
|------|-------------|
| `get_org_info` | Get organization information |
| `get_org_timeline` | Organization-wide event timeline |

### Alerts and Reporting

| Tool | Description |
|------|-------------|
| `list_alerts` | List recent alerts |
| `get_incident_history` | Historical incident data |
| `get_oncall_report` | On-call report for a team |

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

### Read-Only Mode

The server automatically detects whether the API key is read-only or full-access on first use. When a read-only key is provided, write operations return a clear error message instead of failing with a 403. Use `get_access_mode` to check.

You can also force read-only mode with a full-access key by setting:

```json
"SPLUNK_ONCALL_READ_ONLY": "true"
```

This is useful when you want to use a full-access key but prevent accidental writes.

## License

MIT
