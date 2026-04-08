"""HTTP client for the Splunk On-Call (VictorOps) REST API."""

from __future__ import annotations

import httpx


API_BASE = "https://api.victorops.com/api-public"


class SplunkOnCallClient:
    """Thin wrapper around the Splunk On-Call public REST API."""

    def __init__(self, api_id: str, api_key: str) -> None:
        self._headers = {
            "X-VO-Api-Id": api_id,
            "X-VO-Api-Key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self._client = httpx.AsyncClient(
            base_url=API_BASE,
            headers=self._headers,
            timeout=30.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        resp = await self._client.request(method, path, **kwargs)
        resp.raise_for_status()
        return resp.json()

    # -- Incidents --

    async def list_incidents(self) -> dict:
        return await self._request("GET", "/v2/incidents")

    async def acknowledge_incidents(
        self, user_name: str, incident_names: list[str], message: str | None = None,
    ) -> dict:
        body: dict = {"userName": user_name, "incidentNames": incident_names}
        if message:
            body["message"] = message
        return await self._request("POST", "/v1/incidents/acknowledge", json=body)

    async def resolve_incidents(
        self, user_name: str, incident_names: list[str], message: str | None = None,
    ) -> dict:
        body: dict = {"userName": user_name, "incidentNames": incident_names}
        if message:
            body["message"] = message
        return await self._request("POST", "/v1/incidents/resolve", json=body)

    async def reroute_incidents(
        self, user_name: str, incident_names: list[str], targets: list[dict],
    ) -> dict:
        body = {
            "userName": user_name,
            "incidentNames": incident_names,
            "targets": targets,
        }
        return await self._request("POST", "/v1/incidents/reroute", json=body)

    async def get_incident_timeline(self, incident_number: str) -> dict:
        return await self._request("GET", f"/v1/incidents/{incident_number}/timeline")

    # -- On-Call --

    async def get_oncall(self) -> dict:
        return await self._request("GET", "/v2/oncall/current")

    async def get_team_oncall_schedule(
        self, team_slug: str, days_forward: int = 14, days_skip: int = 0,
    ) -> dict:
        params = {"daysForward": days_forward, "daysSkip": days_skip}
        return await self._request(
            "GET", f"/v2/team/{team_slug}/oncall/schedule", params=params,
        )

    # -- Teams --

    async def list_teams(self) -> dict:
        return await self._request("GET", "/v1/team")

    async def get_team(self, team_slug: str) -> dict:
        return await self._request("GET", f"/v1/team/{team_slug}")

    async def get_team_members(self, team_slug: str) -> dict:
        return await self._request("GET", f"/v1/team/{team_slug}/members")

    async def get_team_policies(self, team_slug: str) -> dict:
        return await self._request("GET", f"/v1/team/{team_slug}/policies")

    # -- Users --

    async def list_users(self) -> dict:
        return await self._request("GET", "/v1/user")

    async def get_user(self, user_name: str) -> dict:
        return await self._request("GET", f"/v1/user/{user_name}")

    async def get_user_oncall_schedule(self, user_name: str) -> dict:
        return await self._request("GET", f"/v1/user/{user_name}/oncall/schedule")

    # -- Routing Keys --

    async def list_routing_keys(self) -> dict:
        return await self._request("GET", "/v1/org/routing-keys")

    # -- Escalation Policies --

    async def list_policies(self) -> dict:
        return await self._request("GET", "/v1/policies")

    async def get_policy(self, policy_slug: str) -> dict:
        return await self._request("GET", f"/v1/policies/{policy_slug}")

    # -- Maintenance Mode --

    async def list_maintenance(self) -> dict:
        return await self._request("GET", "/v1/maintenancemode")

    async def create_maintenance(
        self,
        names: list[str],
        purpose: str,
        start_date: str | None = None,
        end_date: str | None = None,
        is_global: bool = False,
    ) -> dict:
        body: dict = {"names": names, "purpose": purpose, "isGlobal": is_global}
        if start_date:
            body["startDate"] = start_date
        if end_date:
            body["endDate"] = end_date
        return await self._request("POST", "/v1/maintenancemode", json=body)

    async def end_maintenance(self, maintenance_id: str) -> dict:
        return await self._request("DELETE", f"/v1/maintenancemode/{maintenance_id}")

    # -- Organization --

    async def get_org(self) -> dict:
        return await self._request("GET", "/v1/org")

    # -- Reporting --

    async def get_incident_history(
        self, start: str | None = None, end: str | None = None,
    ) -> dict:
        params: dict = {}
        if start:
            params["startedAfter"] = start
        if end:
            params["startedBefore"] = end
        return await self._request("GET", "/v2/reporting/incidents", params=params)
