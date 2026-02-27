from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_tfvars(path: str | None) -> dict[str, Any]:
    """
    Load variables from either:
    - Terraform JSON vars file: *.tfvars.json
    - Simple Terraform vars file: *.tfvars (flat key=value entries)
    """
    if not path:
        return {}

    file_path = Path(path).expanduser()
    if not file_path.exists():
        return {}

    raw = file_path.read_text(encoding="utf-8")

    if file_path.name.endswith(".json"):
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError(f"Expected object in tfvars json file: {file_path}")
        return data

    return _parse_tfvars_kv(raw)


def _parse_tfvars_kv(content: str) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for line in content.splitlines():
        cleaned = _strip_comments(line).strip()
        if not cleaned:
            continue
        if "=" not in cleaned:
            continue

        key, value = cleaned.split("=", maxsplit=1)
        key = key.strip()
        if not key:
            continue
        result[key] = _parse_scalar_or_list(value.strip())

    return result


def _strip_comments(line: str) -> str:
    in_quotes = False
    idx = 0
    while idx < len(line):
        ch = line[idx]
        if ch == '"':
            in_quotes = not in_quotes
            idx += 1
            continue

        if not in_quotes:
            if ch == "#":
                return line[:idx]
            if ch == "/" and idx + 1 < len(line) and line[idx + 1] == "/":
                return line[:idx]
        idx += 1
    return line


def _parse_scalar_or_list(raw_value: str) -> Any:
    value = raw_value.strip()
    if not value:
        return ""

    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]

    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None

    if value.startswith("[") and value.endswith("]"):
        return _parse_list(value)

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    return value


def _parse_list(raw_list: str) -> list[Any]:
    inner = raw_list[1:-1].strip()
    if not inner:
        return []

    items: list[str] = []
    buffer: list[str] = []
    in_quotes = False

    for ch in inner:
        if ch == '"':
            in_quotes = not in_quotes
            buffer.append(ch)
            continue

        if ch == "," and not in_quotes:
            items.append("".join(buffer).strip())
            buffer = []
            continue

        buffer.append(ch)

    if buffer:
        items.append("".join(buffer).strip())

    return [_parse_scalar_or_list(item) for item in items]

