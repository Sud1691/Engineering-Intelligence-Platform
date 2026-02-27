from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Key

from eip.core.models import DeploymentEvent, RiskScore
from eip.core.settings import get_settings


class HistoricalDB:
    """
    DynamoDB access layer for deployments and risk scores.

    Follows the key design patterns defined in `.cursorrules/cursorrules`.
    """

    _stub_deployments: dict[str, list[dict[str, Any]]] = {}
    _stub_scores: dict[str, list[dict[str, Any]]] = {}

    def __init__(
        self,
        deployments_table_name: str | None = None,
        risk_scores_table_name: str | None = None,
    ) -> None:
        settings = get_settings()
        self._runtime_mode = settings.runtime_mode
        self._deployments = None
        self._risk_scores = None

        if self._runtime_mode == "live":
            dynamodb = boto3.resource("dynamodb")
            self._deployments = dynamodb.Table(
                deployments_table_name or settings.deployments_table_name
            )
            self._risk_scores = dynamodb.Table(
                risk_scores_table_name or settings.risk_scores_table_name
            )

    @classmethod
    def reset_stub_state(cls) -> None:
        cls._stub_deployments.clear()
        cls._stub_scores.clear()

    def record_deployment(self, event: DeploymentEvent) -> None:
        now = datetime.now(timezone.utc).isoformat()
        item: Dict[str, Any] = {
            "pk": f"SERVICE#{event.service_name}",
            "sk": f"DEPLOY#{now}#{event.commit_sha[:8]}",
            "service_name": event.service_name,
            "environment": event.environment,
            "branch": event.branch,
            "commit_sha": event.commit_sha,
            "commit_message": event.commit_message,
            "commit_author": event.commit_author,
            "commit_author_email": event.commit_author_email,
            "changed_files": event.changed_files,
            "lines_added": event.lines_added,
            "lines_deleted": event.lines_deleted,
            "deploy_hour": event.deploy_hour,
            "deploy_day": event.deploy_day,
            "build_url": event.build_url,
            "coverage_delta": event.coverage_delta,
            "created_at": now,
        }
        if self._runtime_mode == "stub":
            pk = item["pk"]
            self._stub_deployments.setdefault(pk, []).append(item)
            self._stub_deployments[pk].sort(key=lambda row: row["sk"], reverse=True)
            return

        self._deployments.put_item(Item=item)

    def save_risk_score(
        self,
        event: DeploymentEvent,
        score: RiskScore,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        item: Dict[str, Any] = {
            "pk": f"DEPLOY#{event.commit_sha}",
            "sk": f"SCORE#{now}",
            "service_name": event.service_name,
            "environment": event.environment,
            "commit_sha": event.commit_sha,
            "risk_score": score.score,
            "risk_tier": score.tier,
            "probability_score": score.probability_score,
            "impact_score": score.impact_score,
            "recommended_action": score.recommended_action,
            "resulted_in_incident": score.resulted_in_incident,
            "created_at": now,
        }
        if self._runtime_mode == "stub":
            pk = item["pk"]
            self._stub_scores.setdefault(pk, []).append(item)
            self._stub_scores[pk].sort(key=lambda row: row["sk"], reverse=True)
            return

        self._risk_scores.put_item(Item=item)

    def get_recent_deployments(
        self,
        service_name: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        pk = f"SERVICE#{service_name}"
        if self._runtime_mode == "stub":
            return list(self._stub_deployments.get(pk, []))[:limit]

        response = self._deployments.query(
            KeyConditionExpression=Key("pk").eq(pk),
            ScanIndexForward=False,
            Limit=limit,
        )
        return response.get("Items", [])

    def get_latest_risk_score(self, commit_sha: str) -> Optional[Dict[str, Any]]:
        pk = f"DEPLOY#{commit_sha}"

        if self._runtime_mode == "stub":
            scores = self._stub_scores.get(pk, [])
            return scores[0] if scores else None

        response = self._risk_scores.query(
            KeyConditionExpression=Key("pk").eq(pk) & Key("sk").begins_with("SCORE#"),
            ScanIndexForward=False,
            Limit=1,
        )
        items = response.get("Items", [])
        return items[0] if items else None

    def mark_resulted_in_incident(
        self,
        commit_sha: str,
        incident_id: str,
        linked_at: str,
    ) -> bool:
        pk = f"DEPLOY#{commit_sha}"

        if self._runtime_mode == "stub":
            scores = self._stub_scores.get(pk, [])
            if not scores:
                return False
            scores[0]["resulted_in_incident"] = True
            scores[0]["linked_incident_id"] = incident_id
            scores[0]["incident_linked_at"] = linked_at
            return True

        latest = self.get_latest_risk_score(commit_sha)
        if not latest:
            return False

        self._risk_scores.update_item(
            Key={"pk": latest["pk"], "sk": latest["sk"]},
            UpdateExpression=(
                "SET resulted_in_incident = :resulted, "
                "linked_incident_id = :incident_id, "
                "incident_linked_at = :linked_at"
            ),
            ExpressionAttributeValues={
                ":resulted": True,
                ":incident_id": incident_id,
                ":linked_at": linked_at,
            },
        )
        return True

    def list_recent_risk_scores(self, limit: int = 200) -> List[Dict[str, Any]]:
        if self._runtime_mode == "stub":
            rows: list[dict[str, Any]] = []
            for scores in self._stub_scores.values():
                rows.extend(scores)
            rows.sort(key=lambda row: row.get("sk", ""), reverse=True)
            return rows[:limit]

        # In live mode this should query a dedicated GSI rather than scanning.
        raise NotImplementedError(
            "Live list_recent_risk_scores requires a GSI-backed query path."
        )
