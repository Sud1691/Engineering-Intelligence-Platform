from __future__ import annotations

from datetime import datetime, timedelta, timezone

import boto3
from moto import mock_aws

from eip.core.provider_registry import (
    clear_provider_registry_cache,
    get_provider_registry,
)
from eip.core.settings import clear_settings_cache


def test_provider_registry_live_mode_uses_live_risk_provider(monkeypatch) -> None:
    monkeypatch.setenv("EIP_TFVARS_PATH", "/tmp/non-existent.tfvars")
    monkeypatch.setenv("EIP_RUNTIME_MODE", "live")
    monkeypatch.setenv("EIP_ENABLE_LIVE_MODE", "true")
    monkeypatch.setenv("EIP_AWS_REGION", "us-east-1")
    monkeypatch.setenv("EIP_RISK_SCORES_TABLE_NAME", "eip-risk-scores")

    clear_settings_cache()
    clear_provider_registry_cache()

    with mock_aws():
        ddb = boto3.client("dynamodb", region_name="us-east-1")
        ddb.create_table(
            TableName="eip-risk-scores",
            BillingMode="PAY_PER_REQUEST",
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
                {"AttributeName": "service_name", "AttributeType": "S"},
                {"AttributeName": "created_at", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "service-created-at-index",
                    "KeySchema": [
                        {"AttributeName": "service_name", "KeyType": "HASH"},
                        {"AttributeName": "created_at", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
        )

        table = boto3.resource("dynamodb", region_name="us-east-1").Table(
            "eip-risk-scores"
        )
        now = datetime.now(timezone.utc)
        recent = now.isoformat()
        old = (now - timedelta(days=10)).isoformat()
        table.put_item(
            Item={
                "pk": "DEPLOY#abc",
                "sk": f"SCORE#{recent}",
                "service_name": "payments-api",
                "created_at": recent,
                "risk_tier": "HIGH",
            }
        )
        table.put_item(
            Item={
                "pk": "DEPLOY#def",
                "sk": f"SCORE#{recent}",
                "service_name": "payments-api",
                "created_at": recent,
                "risk_tier": "CRITICAL",
            }
        )
        table.put_item(
            Item={
                "pk": "DEPLOY#old",
                "sk": f"SCORE#{old}",
                "service_name": "payments-api",
                "created_at": old,
                "risk_tier": "CRITICAL",
            }
        )

        registry = get_provider_registry()
        overview = registry.risk.get_risk_overview("payments-api")

        assert registry.source_mode == "live"
        assert overview["high_risk_deployments_last_7d"] == 1
        assert overview["critical_risk_deployments_last_7d"] == 1
