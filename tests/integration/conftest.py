from __future__ import annotations

import os
from collections.abc import Iterator

import boto3
import pytest
from moto import mock_aws

from eip.core.provider_registry import clear_provider_registry_cache
from eip.core.settings import clear_settings_cache


@pytest.fixture(autouse=True)
def integration_runtime_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """
    Force deterministic local AWS emulation and live-runtime code paths.
    """
    monkeypatch.setenv("EIP_TFVARS_PATH", "/tmp/non-existent.tfvars")
    monkeypatch.setenv("EIP_RUNTIME_MODE", "live")
    monkeypatch.setenv("EIP_ENABLE_LIVE_MODE", "true")
    monkeypatch.setenv("EIP_AWS_REGION", "us-east-1")
    monkeypatch.setenv("EIP_DEPLOYMENTS_TABLE_NAME", "eip-deployments")
    monkeypatch.setenv("EIP_RISK_SCORES_TABLE_NAME", "eip-risk-scores")
    monkeypatch.setenv("EIP_INCIDENTS_TABLE_NAME", "eip-incidents")
    monkeypatch.setenv("EIP_EVENT_BUS_NAME", "eip-event-bus")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    clear_settings_cache()
    clear_provider_registry_cache()
    yield
    clear_settings_cache()
    clear_provider_registry_cache()


@pytest.fixture
def aws_mock() -> Iterator[None]:
    with mock_aws():
        yield


@pytest.fixture
def dynamodb_tables(aws_mock: None):
    ddb = boto3.client("dynamodb", region_name="us-east-1")

    ddb.create_table(
        TableName="eip-deployments",
        BillingMode="PAY_PER_REQUEST",
        KeySchema=[
            {"AttributeName": "pk", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "pk", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
        ],
    )

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

    ddb.create_table(
        TableName="eip-incidents",
        BillingMode="PAY_PER_REQUEST",
        KeySchema=[
            {"AttributeName": "pk", "KeyType": "HASH"},
            {"AttributeName": "sk", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "pk", "AttributeType": "S"},
            {"AttributeName": "sk", "AttributeType": "S"},
            {"AttributeName": "id", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "incident-id-index",
                "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
    )

    return ddb
