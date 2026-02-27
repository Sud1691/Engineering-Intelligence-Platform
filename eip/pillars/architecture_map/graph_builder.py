from __future__ import annotations

from typing import Iterable

import networkx as nx

from eip.core.models import ServiceNode


class ArchitectureGraphBuilder:
    """
    Builds an in-memory directed graph of services and their dependencies.

    Nodes are `ServiceNode` instances keyed by service name.
    Edges represent "A depends on B" (A → B).
    """

    def build(
        self,
        services: Iterable[ServiceNode],
    ) -> nx.DiGraph:
        graph = nx.DiGraph()

        # Add all services as nodes first
        for service in services:
            graph.add_node(
                service.name,
                service=service,
                team=service.team,
                tier=service.tier.value,
                aws_account=service.aws_account,
                monthly_cost=service.monthly_cost,
                health=service.health,
            )

        # Add dependency edges
        for service in services:
            for dependency in service.dependencies:
                if dependency not in graph:
                    # Allow edges to services not yet modelled as nodes
                    graph.add_node(dependency)
                graph.add_edge(service.name, dependency)

        # Add reverse consumer links for convenience
        for service in services:
            for consumer in service.consumers:
                if consumer not in graph:
                    graph.add_node(consumer)
                graph.add_edge(consumer, service.name)

        return graph

