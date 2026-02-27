"""
PagerDuty API integration.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
import structlog

from eip.core.models import ActionItem, Incident
from eip.core.secrets import get_secret
from eip.core.settings import get_settings


log = structlog.get_logger()


class PagerDutyClient:
    """
    Client for interacting with the PagerDuty API.
    """

    BASE_URL = "https://api.pagerduty.com"

    def __init__(self, token: str | None = None) -> None:
        if not token:
            settings = get_settings()
            secrets = get_secret(settings.integrations_secret_name)
            token = secrets.get("pagerduty_token", "")
            
        self._headers = {
            "Authorization": f"Token token={token}",
            "Accept": "application/vnd.pagerduty+json;version=2",
            "Content-Type": "application/json",
        }

    async def get_recent_incidents(
        self,
        since: datetime | None = None,
        service_ids: List[str] | None = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent incidents from PagerDuty.
        """
        params: Dict[str, Any] = {
            "limit": limit,
            "sort_by": "created_at:desc",
        }
        
        if since:
            params["since"] = since.isoformat()
            
        if service_ids:
            params["service_ids[]"] = service_ids

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/incidents",
                    headers=self._headers,
                    params=params,
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()
                return data.get("incidents", [])
            except httpx.HTTPError as e:
                log.error("pagerduty_api_error", error=str(e), endpoint="/incidents")
                return []

    def parse_incident(self, pd_incident: Dict[str, Any], service_name_mapping: Dict[str, str]) -> Incident:
        """
        Convert a raw PagerDuty incident dictionary into our internal Incident model.
        """
        incident_id = pd_incident.get("id", "unknown")
        
        # Extract service name. In a real system we'd map PD service ID -> Catalog Service Name.
        pd_service_id = pd_incident.get("service", {}).get("id", "")
        service_name = service_name_mapping.get(pd_service_id, pd_incident.get("service", {}).get("summary", "unknown-service"))

        # Map PD urgency/status to severity
        urgency = pd_incident.get("urgency", "low")
        severity = "SEV-1" if urgency == "high" else "SEV-3"
        
        created_at_str = pd_incident.get("created_at")
        started_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00")) if created_at_str else datetime.now(timezone.utc)
        
        resolved_at_str = pd_incident.get("last_status_change_at") if pd_incident.get("status") == "resolved" else None
        resolved_at = datetime.fromisoformat(resolved_at_str.replace("Z", "+00:00")) if resolved_at_str else None

        return Incident(
            id=incident_id,
            service_name=service_name,
            severity=severity,
            started_at=started_at,
            resolved_at=resolved_at,
            action_items=[],  # Would typically be extracted from post-mortem documents, not raw incident API
        )
