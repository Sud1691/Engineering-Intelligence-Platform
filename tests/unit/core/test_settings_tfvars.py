from __future__ import annotations

from pathlib import Path

from eip.core.settings import clear_settings_cache, get_settings


def test_settings_load_from_tfvars(monkeypatch, tmp_path: Path) -> None:
    tfvars_path = tmp_path / "platform.auto.tfvars"
    tfvars_path.write_text(
        """
eip_runtime_mode = "stub"
eip_enable_live_mode = false
eip_aws_region = "eu-west-1"
eip_event_bus_name = "eip-bus-custom"
eip_deployments_table_name = "deploy-custom"
eip_risk_scores_table_name = "risk-custom"
eip_incidents_table_name = "incident-custom"
eip_integrations_secret_name = "eip/integrations/custom"
eip_slack_default_channel = "#custom-alerts"
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv("EIP_TFVARS_PATH", str(tfvars_path))
    monkeypatch.delenv("EIP_RUNTIME_MODE", raising=False)
    monkeypatch.delenv("EIP_AWS_REGION", raising=False)
    clear_settings_cache()

    settings = get_settings()

    assert settings.runtime_mode == "stub"
    assert settings.aws_region == "eu-west-1"
    assert settings.event_bus_name == "eip-bus-custom"
    assert settings.deployments_table_name == "deploy-custom"
    assert settings.risk_scores_table_name == "risk-custom"
    assert settings.incidents_table_name == "incident-custom"
    assert settings.integrations_secret_name == "eip/integrations/custom"
    assert settings.slack_default_channel == "#custom-alerts"


def test_settings_env_overrides_tfvars(monkeypatch, tmp_path: Path) -> None:
    tfvars_path = tmp_path / "platform.auto.tfvars"
    tfvars_path.write_text(
        """
eip_runtime_mode = "stub"
eip_aws_region = "eu-west-1"
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setenv("EIP_TFVARS_PATH", str(tfvars_path))
    monkeypatch.setenv("EIP_RUNTIME_MODE", "stub")
    monkeypatch.setenv("EIP_AWS_REGION", "ap-southeast-2")
    clear_settings_cache()

    settings = get_settings()

    assert settings.runtime_mode == "stub"
    assert settings.aws_region == "ap-southeast-2"
