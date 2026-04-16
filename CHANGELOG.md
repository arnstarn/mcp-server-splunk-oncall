# Changelog

All notable changes to this project will be documented in this file.

## [0.4.0] - 2026-04-15

### Added
- `get_alert` tool to fetch a single alert by UUID
- Supports alert numbers (e.g. "739914") that were previously confused with incident numbers

### Fixed
- Clarified distinction between alert UUIDs and incident numbers in tool descriptions
- `get_incident_timeline` now has clearer docs noting it expects an incident number, not an alert number

## [0.3.3] - 2026-04-09

### Fixed
- Try v2 API first, fall back to v1 on 404

## [0.3.2] - 2026-04-09

### Fixed
- Fix v2 API endpoints that return 404

## [0.3.1] - 2026-04-09

### Changed
- Bump version for trusted publishing test

## [0.3.0] - 2026-04-09

### Changed
- Updated v2 API endpoint support

## [0.2.3] - 2026-04-08

### Changed
- Transferred repo from amendezsap to arnstarn
- Updated all project URLs

## [0.2.2] - 2026-04-08

### Changed
- Added PyPI/license/python badges to README
- Tool tables in README matching mcp-server-spotinst format
- Added GitHub topics and repo metadata

## [0.2.1] - 2026-04-08

### Added
- `SPLUNK_ONCALL_READ_ONLY` env var to force read-only mode even with a full-access API key
- Skips write-probe detection when forced RO
- `get_access_mode` distinguishes between forced RO and detected RO

## [0.2.0] - 2026-04-08

### Added
- Full Splunk On-Call REST API coverage (45 tools, up from 21)
- Auto-detected read-only mode on startup via write-probe
- Write operations gated with clear error messages in RO mode
- Teams CRUD: create, update, delete, add/remove members, list admins
- Users CRUD: create, delete, contact methods, devices, teams
- Routing keys: create, delete
- Escalation policies: create, delete
- Incidents: acknowledge-all, resolve-all
- Organization timeline
- Alerts listing
- On-call reports per team

## [0.1.0] - 2026-04-08

### Added
- Initial release with 21 tools
- Incidents: list, acknowledge, resolve, reroute, timeline, history
- On-call: current, team schedule, user schedule
- Teams: list, members, policies
- Users: list, get
- Routing keys: list
- Escalation policies: list, get
- Maintenance: list, create, end
- Organization info
