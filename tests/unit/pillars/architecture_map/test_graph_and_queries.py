from datetime import datetime

import networkx as nx

from eip.core.models import ServiceNode, ServiceTier
from eip.pillars.architecture_map.graph_builder import ArchitectureGraphBuilder
from eip.pillars.architecture_map.query_engine import ArchitectureQueryEngine


def make_service(
    name: str,
    tier: ServiceTier,
    team: str,
    dependencies: list[str] | None = None,
    consumers: list[str] | None = None,
) -> ServiceNode:
    return ServiceNode(
        name=name,
        tier=tier,
        team=team,
        aws_account="111111111111",
        dependencies=dependencies or [],
        consumers=consumers or [],
        health="healthy",
        last_deploy=datetime.utcnow(),
        monthly_cost=100.0,
    )


def test_graph_builder_creates_edges_and_nodes() -> None:
    payments = make_service(
        "payments-api",
        ServiceTier.CRITICAL,
        "payments",
        dependencies=["users-api"],
    )
    users = make_service(
        "users-api",
        ServiceTier.IMPORTANT,
        "identity",
    )

    builder = ArchitectureGraphBuilder()
    graph = builder.build([payments, users])

    assert isinstance(graph, nx.DiGraph)
    assert "payments-api" in graph
    assert "users-api" in graph
    assert graph.has_edge("payments-api", "users-api")


def test_query_engine_blast_radius_and_dependencies() -> None:
    core_service = make_service(
        "core-api",
        ServiceTier.CRITICAL,
        "core",
        dependencies=["orders-api"],
    )
    orders = make_service(
        "orders-api",
        ServiceTier.IMPORTANT,
        "orders",
        dependencies=["payments-api"],
    )
    payments = make_service(
        "payments-api",
        ServiceTier.CRITICAL,
        "payments",
    )

    builder = ArchitectureGraphBuilder()
    graph = builder.build([core_service, orders, payments])

    engine = ArchitectureQueryEngine(graph)

    deps = engine.get_dependencies("core-api", max_depth=3)
    assert deps == ["orders-api", "payments-api"]

    dependents = engine.get_dependents("payments-api", max_depth=3)
    assert dependents == ["core-api", "orders-api"]

