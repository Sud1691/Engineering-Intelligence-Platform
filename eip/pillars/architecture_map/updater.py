from __future__ import annotations

from typing import Iterable, Tuple

import networkx as nx

from eip.core.event_bus import emit
from eip.core.models import ServiceNode
from eip.pillars.architecture_map.graph_builder import ArchitectureGraphBuilder


class ArchitectureGraphUpdater:
    """
    Handles real-time updates to the architecture graph from various sources.

    In the MVP this is a simple in-memory updater that rebuilds the graph
    from a snapshot. In production this would apply incremental updates and
    persist them to Neptune.
    """

    def __init__(self) -> None:
        self._builder = ArchitectureGraphBuilder()
        self._graph: nx.DiGraph | None = None

    @property
    def graph(self) -> nx.DiGraph | None:
        return self._graph

    async def apply_snapshot(
        self,
        services: Iterable[ServiceNode],
        extra_dependencies: Iterable[Tuple[str, str]] = (),
    ) -> nx.DiGraph:
        """
        Rebuild the architecture graph from a snapshot of known services
        plus any extra dependency edges discovered from telemetry sources.
        """

        graph = self._builder.build(services)

        for caller, callee in extra_dependencies:
            if caller not in graph:
                graph.add_node(caller)
            if callee not in graph:
                graph.add_node(callee)
            graph.add_edge(caller, callee)

        self._graph = graph

        await emit(
            "eip.architecture.graph_updated",
            {
                "service_count": graph.number_of_nodes(),
                "dependency_count": graph.number_of_edges(),
            },
        )

        return graph

