"""
DynamoDB access layer for incidents and their linkage to deployments.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Key

from eip.core.models import Incident
from eip.core.settings import get_settings


class IncidentDB:
    """
    DynamoDB access layer for incidents.

    Follows the key design patterns defined in `.cursorrules/cursorrules`.
    pk = SERVICE#{service_name}
    sk = INCIDENT#{started_at_iso}#{incident_id}
    """

    _stub_incidents: dict[str, list[dict[str, Any]]] = {}

    def __init__(self, table_name: str | None = None) -> None:
        settings = get_settings()
        self._runtime_mode = settings.runtime_mode
        self._table = None

        if self._runtime_mode == "live":
            dynamodb = boto3.resource("dynamodb")
            self._table = dynamodb.Table(table_name or settings.incidents_table_name)

    @classmethod
    def reset_stub_state(cls) -> None:
        cls._stub_incidents.clear()

    def record_incident(self, incident: Incident) -> None:
        """
        Save a new or updated incident to DynamoDB.
        """
        # Convert Pydantic models to dicts suitable for boto3
        action_items = [ai.model_dump(mode="python") for ai in incident.action_items]

        # Convert datetimes to iso strings for DynamoDB
        for ai in action_items:
            if ai.get("due_at"):
                ai["due_at"] = ai["due_at"].isoformat()
            if ai.get("completed_at"):
                ai["completed_at"] = ai["completed_at"].isoformat()

        started_at_iso = incident.started_at.isoformat()
        resolved_at_iso = incident.resolved_at.isoformat() if incident.resolved_at else None

        item: Dict[str, Any] = {
            "pk": f"SERVICE#{incident.service_name}",
            "sk": f"INCIDENT#{started_at_iso}#{incident.id}",
            "id": incident.id,
            "service_name": incident.service_name,
            "severity": incident.severity,
            "started_at": started_at_iso,
            "resolved_at": resolved_at_iso,
            "root_cause": incident.root_cause,
            "linked_deploy": incident.linked_deploy,
            "action_items": action_items,
            "recurrence_of": incident.recurrence_of,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Remove None values to avoid boto3 errors
        item = {k: v for k, v in item.items() if v is not None}

        if self._runtime_mode == "stub":
            pk = item["pk"]
            self._stub_incidents.setdefault(pk, []).append(item)
            self._stub_incidents[pk].sort(key=lambda row: row["sk"], reverse=True)
            return

        self._table.put_item(Item=item)

    def get_incidents_by_service(
        self, service_name: str, limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent incidents for a given service.
        Query uses partition key, avoiding scans.
        """
        if self._runtime_mode == "stub":
            return list(self._stub_incidents.get(f"SERVICE#{service_name}", []))[:limit]

        response = self._table.query(
            KeyConditionExpression=Key("pk").eq(f"SERVICE#{service_name}"),
            ScanIndexForward=False,  # Descending by sort key (started_at)
            Limit=limit,
        )
        return response.get("Items", [])

    def get_incident(self, service_name: str, started_at_iso: str, incident_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a specific incident by its exact primary key.
        """
        if self._runtime_mode == "stub":
            items = self._stub_incidents.get(f"SERVICE#{service_name}", [])
            target_sk = f"INCIDENT#{started_at_iso}#{incident_id}"
            for item in items:
                if item.get("sk") == target_sk:
                    return item
            return None

        response = self._table.get_item(
            Key={
                "pk": f"SERVICE#{service_name}",
                "sk": f"INCIDENT#{started_at_iso}#{incident_id}"
            }
        )
        return response.get("Item")
