"""
Async worker to keep the architecture map fresh.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict

import structlog

from eip.core.models import ServiceNode
from eip.core.provider_registry import get_provider_registry
from eip.pillars.architecture_map.updater import ArchitectureGraphUpdater


log = structlog.get_logger()

# Global updater instance for the worker
updater = ArchitectureGraphUpdater()


async def process_architecture_update(event_payload: Dict[str, Any]) -> None:
    """
    Consume events from CloudTrail or Terraform state changes 
    and update the architecture graph.
    """
    event_type = event_payload.get("event_type", "unknown")
    correlation_id = event_payload.get("correlation_id")
    
    log.info(
        "graph_update_started",
        event_type=event_type,
        correlation_id=correlation_id,
        service_name="architecture-map",
    )

    providers = get_provider_registry()

    raw_services = event_payload.get("services")
    if raw_services:
        services = [ServiceNode.model_validate(item) for item in raw_services]
    else:
        services = providers.architecture.get_services()

    raw_extra = event_payload.get("extra_dependencies")
    if raw_extra:
        extra_dependencies = [
            (str(item[0]), str(item[1]))
            for item in raw_extra
            if isinstance(item, (list, tuple)) and len(item) == 2
        ]
    else:
        extra_dependencies = providers.architecture.get_extra_dependencies()

    graph = await updater.apply_snapshot(services, extra_dependencies)

    log.info(
        "graph_update_completed",
        event_type=event_type,
        correlation_id=correlation_id,
        service_name="architecture-map",
        service_count=graph.number_of_nodes(),
        dependency_count=graph.number_of_edges(),
    )


def _event_to_payload(event: Dict[str, Any]) -> Dict[str, Any]:
    detail = event.get("detail")
    if isinstance(detail, str):
        try:
            detail = json.loads(detail)
        except ValueError:
            detail = {}
    if isinstance(detail, dict):
        return detail
    return event if isinstance(event, dict) else {}


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    payload = _event_to_payload(event)
    asyncio.run(process_architecture_update(payload))
    return {"statusCode": 200, "processed": True}
