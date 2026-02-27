from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, cast

from eip.core.tfvars import load_tfvars


RuntimeMode = Literal["stub", "live"]


@dataclass(frozen=True)
class Settings:
    runtime_mode: RuntimeMode
    live_mode_enabled: bool
    tfvars_path: str | None
    aws_region: str
    event_bus_name: str
    deployments_table_name: str
    risk_scores_table_name: str
    incidents_table_name: str
    integrations_secret_name: str
    slack_default_channel: str
    incident_link_window_hours: int


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _resolve_value(
    env_name: str,
    tfvars_key: str,
    tfvars_data: dict[str, Any],
    default: Any,
) -> Any:
    env_value = os.getenv(env_name)
    if env_value is not None:
        return env_value
    if tfvars_key in tfvars_data:
        return tfvars_data[tfvars_key]
    return default


def _resolve_tfvars_path() -> str | None:
    explicit = os.getenv("EIP_TFVARS_PATH")
    if explicit:
        return explicit

    project_root = Path(__file__).resolve().parents[2]
    for candidate in ("platform.auto.tfvars", "platform.auto.tfvars.json"):
        cwd_path = Path(candidate)
        if cwd_path.exists():
            return str(cwd_path)

        root_path = project_root / candidate
        if root_path.exists():
            return str(root_path)
    return None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    tfvars_path = _resolve_tfvars_path()
    tfvars_data = load_tfvars(tfvars_path)

    raw_mode = str(
        _resolve_value(
            env_name="EIP_RUNTIME_MODE",
            tfvars_key="eip_runtime_mode",
            tfvars_data=tfvars_data,
            default="stub",
        )
    ).strip().lower()

    if raw_mode not in {"stub", "live"}:
        raise ValueError(
            "Invalid runtime mode. Expected 'stub' or 'live'. "
            f"Received: {raw_mode!r}"
        )

    live_enabled = _as_bool(
        _resolve_value(
            env_name="EIP_ENABLE_LIVE_MODE",
            tfvars_key="eip_enable_live_mode",
            tfvars_data=tfvars_data,
            default=False,
        )
    )

    if raw_mode == "live" and not live_enabled:
        raise ValueError(
            "Live runtime mode is disabled. Set EIP_ENABLE_LIVE_MODE=true or "
            "eip_enable_live_mode = true in tfvars."
        )

    return Settings(
        runtime_mode=cast(RuntimeMode, raw_mode),
        live_mode_enabled=live_enabled,
        tfvars_path=tfvars_path,
        aws_region=str(
            _resolve_value(
                env_name="EIP_AWS_REGION",
                tfvars_key="eip_aws_region",
                tfvars_data=tfvars_data,
                default="us-east-1",
            )
        ),
        event_bus_name=str(
            _resolve_value(
                env_name="EIP_EVENT_BUS_NAME",
                tfvars_key="eip_event_bus_name",
                tfvars_data=tfvars_data,
                default="eip-event-bus",
            )
        ),
        deployments_table_name=str(
            _resolve_value(
                env_name="EIP_DEPLOYMENTS_TABLE_NAME",
                tfvars_key="eip_deployments_table_name",
                tfvars_data=tfvars_data,
                default="eip-deployments",
            )
        ),
        risk_scores_table_name=str(
            _resolve_value(
                env_name="EIP_RISK_SCORES_TABLE_NAME",
                tfvars_key="eip_risk_scores_table_name",
                tfvars_data=tfvars_data,
                default="eip-risk-scores",
            )
        ),
        incidents_table_name=str(
            _resolve_value(
                env_name="EIP_INCIDENTS_TABLE_NAME",
                tfvars_key="eip_incidents_table_name",
                tfvars_data=tfvars_data,
                default="eip-incidents",
            )
        ),
        integrations_secret_name=str(
            _resolve_value(
                env_name="EIP_INTEGRATIONS_SECRET_NAME",
                tfvars_key="eip_integrations_secret_name",
                tfvars_data=tfvars_data,
                default="eip/integrations",
            )
        ),
        slack_default_channel=str(
            _resolve_value(
                env_name="EIP_SLACK_DEFAULT_CHANNEL",
                tfvars_key="eip_slack_default_channel",
                tfvars_data=tfvars_data,
                default="#deployments",
            )
        ),
        incident_link_window_hours=int(
            _resolve_value(
                env_name="EIP_INCIDENT_LINK_WINDOW_HOURS",
                tfvars_key="eip_incident_link_window_hours",
                tfvars_data=tfvars_data,
                default=2,
            )
        ),
    )


def clear_settings_cache() -> None:
    get_settings.cache_clear()
