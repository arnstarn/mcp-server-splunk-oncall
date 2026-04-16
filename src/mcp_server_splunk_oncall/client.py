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
        self._read_only: bool | None = None

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        resp = await self._client.request(method, path, **kwargs)
        resp.raise_for_status()
        return resp.json()

    async def _request_with_fallback(
        self, method: str, v2_path: str, v1_path: str, **kwargs,
    ) -> dict:
        """Try v2 endpoint first, fall back to v1 if v2 returns 404."""
        resp = await self._client.request(method, v2_path, **kwargs)
        if resp.status_code == 404:
            resp = await self._client.request(method, v1_path, **kwargs)
        resp.raise_for_status()
        return resp.json()

    async def detect_access_mode(self) -> bool:
        """Detect whether the API key is read-only.

        Attempts a write-like probe (POST to incidents/resolve with empty body).
        A read-only key returns 403. A full key returns 400 (bad request, which
        means it has write access but the body was invalid). Returns True if
        read-only.
        """
        if self._read_only is not None:
            return self._read_only
        resp = await self._client.request(
            "POST", "/v1/incidents/resolve", json={"userName": "", "incidentNames": []},
        )
        if resp.status_code == 403:
            self._read_only = True
        else:
            # 400 = key has write access but body was invalid
            # 200 = key has write access and succeeded
            self._read_only = False
        return self._read_only

    @property
    def is_read_only(self) -> bool | None:
        return self._read_only

    # -- Incidents --

    async def list_incidents(self) -> dict:
        return await self._request_with_fallback("GET", "/v2/incidents", "/v1/incidents")

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

    async def acknowledge_all_incidents(self, user_name: str) -> dict:
        return await self._request(
            "POST", "/v1/incidents/ack-all", json={"userName": user_name},
        )

    async def resolve_all_incidents(self, user_name: str) -> dict:
        return await self._request(
            "POST", "/v1/incidents/resolve-all", json={"userName": user_name},
        )

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

    async def create_team(self, name: str, members: list[dict] | None = None) -> dict:
        body: dict = {"name": name}
        if members:
            body["members"] = members
        return await self._request("POST", "/v1/team", json=body)

    async def update_team(self, team_slug: str, name: str) -> dict:
        return await self._request("PUT", f"/v1/team/{team_slug}", json={"name": name})

    async def delete_team(self, team_slug: str) -> dict:
        return await self._request("DELETE", f"/v1/team/{team_slug}")

    async def get_team_members(self, team_slug: str) -> dict:
        return await self._request("GET", f"/v1/team/{team_slug}/members")

    async def add_team_member(self, team_slug: str, user_name: str) -> dict:
        return await self._request(
            "POST", f"/v1/team/{team_slug}/members", json={"username": user_name},
        )

    async def remove_team_member(self, team_slug: str, user_name: str) -> dict:
        return await self._request(
            "DELETE", f"/v1/team/{team_slug}/members/{user_name}",
        )

    async def get_team_admins(self, team_slug: str) -> dict:
        return await self._request("GET", f"/v1/team/{team_slug}/admins")

    async def get_team_policies(self, team_slug: str) -> dict:
        return await self._request("GET", f"/v1/team/{team_slug}/policies")

    # -- Users --

    async def list_users(self) -> dict:
        return await self._request("GET", "/v1/user")

    async def get_user(self, user_name: str) -> dict:
        return await self._request("GET", f"/v1/user/{user_name}")

    async def create_user(
        self, first_name: str, last_name: str, user_name: str, email: str,
    ) -> dict:
        return await self._request("POST", "/v1/user", json={
            "firstName": first_name,
            "lastName": last_name,
            "username": user_name,
            "email": email,
        })

    async def update_user(self, user_name: str, fields: dict) -> dict:
        return await self._request("PUT", f"/v1/user/{user_name}", json=fields)

    async def delete_user(self, user_name: str, replacement: str) -> dict:
        return await self._request(
            "DELETE", f"/v1/user/{user_name}", params={"replacement": replacement},
        )

    async def get_user_contact_methods(self, user_name: str) -> dict:
        return await self._request("GET", f"/v1/user/{user_name}/contact-methods")

    async def get_user_devices(self, user_name: str) -> dict:
        return await self._request(
            "GET", f"/v1/user/{user_name}/contact-methods/devices",
        )

    async def get_user_oncall_schedule(self, user_name: str) -> dict:
        return await self._request("GET", f"/v1/user/{user_name}/oncall/schedule")

    async def get_user_policies(self, user_name: str) -> dict:
        return await self._request("GET", f"/v1/user/{user_name}/policies")

    async def get_user_teams(self, user_name: str) -> dict:
        return await self._request("GET", f"/v1/user/{user_name}/teams")

    # -- Routing Keys --

    async def list_routing_keys(self) -> dict:
        return await self._request("GET", "/v1/org/routing-keys")

    async def create_routing_key(self, routing_key: str, targets: list[dict]) -> dict:
        return await self._request("POST", "/v1/org/routing-keys", json={
            "routingKey": routing_key, "targets": targets,
        })

    async def delete_routing_key(self, routing_key: str) -> dict:
        return await self._request("DELETE", f"/v1/org/routing-keys/{routing_key}")

    # -- Escalation Policies --

    async def list_policies(self) -> dict:
        return await self._request("GET", "/v1/policies")

    async def get_policy(self, policy_slug: str) -> dict:
        return await self._request("GET", f"/v1/policies/{policy_slug}")

    async def create_policy(self, name: str, team_slug: str, steps: list[dict]) -> dict:
        return await self._request("POST", "/v1/policies", json={
            "name": name, "team": {"slug": team_slug}, "steps": steps,
        })

    async def update_policy(self, policy_slug: str, policy: dict) -> dict:
        return await self._request("PUT", f"/v1/policies/{policy_slug}", json=policy)

    async def delete_policy(self, policy_slug: str) -> dict:
        return await self._request("DELETE", f"/v1/policies/{policy_slug}")

    # -- Maintenance Mode --

    async def list_maintenance(self) -> dict:
        return await self._request("GET", "/v1/maintenancemode")

    async def get_maintenance(self, maintenance_id: str) -> dict:
        return await self._request("GET", f"/v1/maintenancemode/{maintenance_id}")

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

    async def update_maintenance(self, maintenance_id: str, fields: dict) -> dict:
        return await self._request(
            "PUT", f"/v1/maintenancemode/{maintenance_id}", json=fields,
        )

    async def end_maintenance(self, maintenance_id: str) -> dict:
        return await self._request("DELETE", f"/v1/maintenancemode/{maintenance_id}")

    # -- Organization --

    async def get_org(self) -> dict:
        return await self._request("GET", "/v1/org")

    async def get_org_timeline(self) -> dict:
        return await self._request("GET", "/v1/org/timeline")

    # -- Reporting --

    async def get_incident_history(
        self, start: str | None = None, end: str | None = None,
    ) -> dict:
        params: dict = {}
        if start:
            params["startedAfter"] = start
        if end:
            params["startedBefore"] = end
        return await self._request_with_fallback(
            "GET", "/v2/reporting/incidents", "/v1/incidents", params=params,
        )

    async def get_oncall_report(
        self, team_slug: str, start: str | None = None, end: str | None = None,
    ) -> dict:
        params: dict = {}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        return await self._request(
            "GET", f"/v1/reporting/oncall/{team_slug}", params=params,
        )

    # -- Alerts --

    async def list_alerts(self) -> dict:
        return await self._request_with_fallback("GET", "/v2/alerts", "/v1/incidents")

    async def get_alert(self, uuid: str) -> dict:
        return await self._request("GET", f"/v1/alerts/{uuid}")
