import json
from functools import lru_cache

import boto3

from eip.core.settings import get_settings


def _build_stub_secrets() -> dict[str, dict]:
    settings = get_settings()
    return {
        settings.integrations_secret_name: {
            "slack_bot_token": "stub-placeholder-slack-token",
            "slack_default_channel": settings.slack_default_channel,
            "pagerduty_token": "stub-placeholder-pagerduty-token",
        }
    }


_STATIC_STUB_SECRETS: dict[str, dict] = {
    "eip/integrations": {
        "slack_bot_token": "stub-placeholder-slack-token",
        "slack_default_channel": "#deployments",
        "pagerduty_token": "stub-placeholder-pagerduty-token",
    }
}


@lru_cache(maxsize=32)
def get_secret(name: str) -> dict:
    """
    Fetch and cache a secret from AWS Secrets Manager.

    This follows the pattern defined in `.cursorrules/cursorrules`.
    """

    if get_settings().runtime_mode == "stub":
        stub_values = _build_stub_secrets()
        if name in stub_values:
            return dict(stub_values[name])
        return dict(_STATIC_STUB_SECRETS.get(name, {}))

    client = boto3.client("secretsmanager", region_name=get_settings().aws_region)
    response = client.get_secret_value(SecretId=name)
    return json.loads(response["SecretString"])
