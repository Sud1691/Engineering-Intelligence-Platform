from __future__ import annotations

from collections import deque
from typing import Iterable, List

import networkx as nx

from eip.core.models import ServiceNode


class ArchitectureQueryEngine:
    """
    Provides high-level queries over the architecture graph.

    The underlying graph is a `networkx.DiGraph` whose nodes are keyed by
    service name and may carry `ServiceNode` metadata.
    """

    def __init__(self, graph: nx.DiGraph) -> None:
        self._graph = graph

    def get_service(self, name: str) -> ServiceNode | None:
        node = self._graph.nodes.get(name)
        if not node:
            return None
        return node.get("service")

    def has_service(self, name: str) -> bool:
        return name in self._graph

    def get_dependencies(self, name: str, max_depth: int = 3) -> List[str]:
        """
        Return the set of services that `name` depends on, up to `max_depth`
        hops away (downstream).
        """

        return self._bfs(name, direction="out", max_depth=max_depth)

    def get_dependents(self, name: str, max_depth: int = 3) -> List[str]:
        """
        Return the set of services that depend on `name`, up to `max_depth`
        hops away (upstream).
        """

        return self._bfs(name, direction="in", max_depth=max_depth)

    def get_blast_radius(self, name: str, max_depth: int = 3) -> List[str]:
        """
        Convenience method for blast radius queries: which services are
        downstream of `name` and would be impacted if it degraded.
        """

        return self.get_dependents(name, max_depth=max_depth)

    def services_by_team(self, team: str) -> List[str]:
        return [
            n
            for n, data in self._graph.nodes(data=True)
            if data.get("team") == team
        ]

    def services_by_environment(self, env: str) -> List[str]:
        """
        Placeholder for future environment-aware queries; currently uses
        the `ServiceNode.health` field as a simple proxy and can be
        adapted once environment metadata is added.
        """

        _ = env
        return list(self._graph.nodes())

    def _bfs(self, name: str, direction: str, max_depth: int) -> List[str]:
        if name not in self._graph:
            return []

        visited: set[str] = set()
        queue: deque[tuple[str, int]] = deque()
        queue.append((name, 0))

        while queue:
            current, depth = queue.popleft()
            if depth >= max_depth:
                continue

            if direction == "out":
                neighbours: Iterable[str] = self._graph.successors(current)
            else:
                neighbours = self._graph.predecessors(current)

            for neighbour in neighbours:
                if neighbour in visited or neighbour == name:
                    continue
                visited.add(neighbour)
                queue.append((neighbour, depth + 1))

        return sorted(visited)
