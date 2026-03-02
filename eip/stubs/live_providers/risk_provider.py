from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import BotoCoreError, ClientError

from eip.core.settings import get_settings


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LiveRiskDataProvider:
    """
    Live risk provider backed by DynamoDB query paths.

    This provider intentionally avoids full-table scans and only uses
    partition/range-key query operations.
    """

    def __init__(self) -> None:
        settings = get_settings()
        ddb = boto3.resource("dynamodb", region_name=settings.aws_region)
        self._table = ddb.Table(settings.risk_scores_table_name)

    def get_risk_overview(self, service_name: str | None = None) -> dict[str, Any]:
        if not service_name:
            return {
                "service_name": "all-services",
                "high_risk_deployments_last_7d": 0,
                "critical_risk_deployments_last_7d": 0,
                "generated_at": _utc_iso_now(),
                "note": (
                    "Live risk overview requires service_name to preserve "
                    "query-only DynamoDB access."
                ),
            }

        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        try:
            response = self._table.query(
                IndexName="service-created-at-index",
                KeyConditionExpression=Key("service_name").eq(service_name)
                & Key("created_at").gte(since),
                ScanIndexForward=False,
                Limit=500,
            )
        except (BotoCoreError, ClientError):
            return {
                "service_name": service_name,
                "high_risk_deployments_last_7d": 0,
                "critical_risk_deployments_last_7d": 0,
                "generated_at": _utc_iso_now(),
                "source_error": "risk_scores_query_failed",
            }

        rows = response.get("Items", [])
        high = sum(1 for row in rows if str(row.get("risk_tier")) == "HIGH")
        critical = sum(1 for row in rows if str(row.get("risk_tier")) == "CRITICAL")
        return {
            "service_name": service_name,
            "high_risk_deployments_last_7d": high,
            "critical_risk_deployments_last_7d": critical,
            "generated_at": _utc_iso_now(),
        }
