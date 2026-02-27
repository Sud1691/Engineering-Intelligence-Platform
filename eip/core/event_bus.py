from __future__ import annotations

import json
from typing import Any, Dict

import boto3
import structlog

from eip.core.settings import get_settings


log = structlog.get_logger()


class EventBus:
    """
    Thin wrapper around AWS EventBridge for the EIP event bus.

    All events must follow the naming convention: `eip.{noun}.{verb_past_tense}`.
    """

    def __init__(self, bus_name: str | None = None) -> None:
        settings = get_settings()
        self._runtime_mode = settings.runtime_mode
        self._client = boto3.client("events") if self._runtime_mode == "live" else None
        self._bus_name = bus_name or settings.event_bus_name

    async def emit(self, event_name: str, detail: Dict[str, Any]) -> None:
        """
        Emit a single event onto the central EventBridge bus.
        """

        if not event_name.startswith("eip."):
            raise ValueError("Event name must start with 'eip.'")

        if self._runtime_mode == "stub":
            log.info(
                "event_emitted_stub",
                event_name=event_name,
                detail=detail,
                event_bus=self._bus_name,
            )
            return

        self._client.put_events(
            Entries=[
                {
                    "Source": "eip.platform",
                    "DetailType": event_name,
                    "Detail": json.dumps(detail),
                    "EventBusName": self._bus_name,
                }
            ]
        )


_default_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    global _default_bus
    if _default_bus is None:
        _default_bus = EventBus()
    return _default_bus


async def emit(event_name: str, detail: Dict[str, Any]) -> None:
    """
    Convenience function matching the pattern shown in `.cursorrules/cursorrules`.
    """

    bus = get_event_bus()
    await bus.emit(event_name, detail)
