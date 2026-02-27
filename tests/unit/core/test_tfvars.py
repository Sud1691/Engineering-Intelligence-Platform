from __future__ import annotations

from pathlib import Path

from eip.core.tfvars import load_tfvars


def test_load_tfvars_parses_scalars_and_lists(tmp_path: Path) -> None:
    tfvars_path = tmp_path / "platform.auto.tfvars"
    tfvars_path.write_text(
        """
name = "demo"
enabled = true
count = 3
ratio = 1.5
tags = ["a", "b", "c"]
""".strip(),
        encoding="utf-8",
    )

    data = load_tfvars(str(tfvars_path))

    assert data["name"] == "demo"
    assert data["enabled"] is True
    assert data["count"] == 3
    assert data["ratio"] == 1.5
    assert data["tags"] == ["a", "b", "c"]


def test_load_tfvars_json(tmp_path: Path) -> None:
    tfvars_json_path = tmp_path / "platform.auto.tfvars.json"
    tfvars_json_path.write_text(
        '{"eip_runtime_mode":"stub","eip_aws_region":"us-east-1"}',
        encoding="utf-8",
    )

    data = load_tfvars(str(tfvars_json_path))

    assert data["eip_runtime_mode"] == "stub"
    assert data["eip_aws_region"] == "us-east-1"
