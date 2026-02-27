"""
API router for the Living Architecture Map.
"""

from __future__ import annotations

from time import perf_counter
from typing import List

from fastapi import APIRouter
import structlog

from eip.core.models import APIResponse
from eip.core.provider_registry import build_endpoint_meta, get_provider_registry
from eip.pillars.architecture_map.graph_builder import ArchitectureGraphBuilder
from eip.pillars.architecture_map.query_engine import ArchitectureQueryEngine


log = structlog.get_logger()
router = APIRouter()


def _build_query_engine() -> ArchitectureQueryEngine:
    providers = get_provider_registry()
    builder = ArchitectureGraphBuilder()
    graph = builder.build(providers.architecture.get_services())

    for caller, callee in providers.architecture.get_extra_dependencies():
        if caller not in graph:
            graph.add_node(caller)
        if callee not in graph:
            graph.add_node(callee)
        graph.add_edge(caller, callee)

    return ArchitectureQueryEngine(graph)


@router.get(
    "/{service_name}/blast-radius",
    response_model=APIResponse[List[str]],
    summary="Get the blast radius of a service",
)
async def get_blast_radius(service_name: str, max_depth: int = 3) -> APIResponse[List[str]]:
    """
    Returns the list of downstream services that would be impacted if this service degraded.
    """
    started_at = perf_counter()
    log.info("architecture_blast_radius_query", service_name=service_name, max_depth=max_depth)

    engine = _build_query_engine()
    impacted = engine.get_blast_radius(service_name, max_depth)

    if not impacted and not engine.has_service(service_name):
        return APIResponse[List[str]](
            success=False,
            data=None,
            error=f"Service '{service_name}' not found in architecture map.",
            meta=build_endpoint_meta(
                pillar="architecture",
                started_at=started_at,
                extra={"service_name": service_name},
            ),
        )

    return APIResponse[List[str]](
        success=True,
        data=impacted,
        error=None,
        meta=build_endpoint_meta(
            pillar="architecture",
            started_at=started_at,
            extra={"service_name": service_name},
        ),
    )


@router.get(
    "/{service_name}/dependencies",
    response_model=APIResponse[List[str]],
    summary="Get upstream dependencies",
)
async def get_dependencies(service_name: str, max_depth: int = 3) -> APIResponse[List[str]]:
    """
    Returns the list of upstream services that this service depends on.
    """
    started_at = perf_counter()
    log.info("architecture_dependencies_query", service_name=service_name, max_depth=max_depth)

    engine = _build_query_engine()
    deps = engine.get_dependencies(service_name, max_depth)

    if not deps and not engine.has_service(service_name):
        return APIResponse[List[str]](
            success=False,
            data=None,
            error=f"Service '{service_name}' not found in architecture map.",
            meta=build_endpoint_meta(
                pillar="architecture",
                started_at=started_at,
                extra={"service_name": service_name},
            ),
        )

    return APIResponse[List[str]](
        success=True,
        data=deps,
        error=None,
        meta=build_endpoint_meta(
            pillar="architecture",
            started_at=started_at,
            extra={"service_name": service_name},
        ),
    )
