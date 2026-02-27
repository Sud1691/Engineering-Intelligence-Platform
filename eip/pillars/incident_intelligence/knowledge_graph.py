"""
Incident Intelligence: Knowledge Graph

Connects incidents to root causes and services using a localized Graph representation.
"""

from __future__ import annotations

import networkx as nx
import structlog

from eip.core.models import Incident


log = structlog.get_logger()


class IncidentKnowledgeGraph:
    """
    Builds a localized graph linking Incidents → Root Causes → Services.
    """

    def __init__(self) -> None:
        self._graph = nx.Graph()

    def add_incident(self, incident: Incident) -> None:
        """
        Add an incident to the knowledge graph.
        """
        # Node for the incident itself
        self._graph.add_node(
            incident.id, 
            type="incident", 
            severity=incident.severity,
            started_at=incident.started_at.isoformat()
        )

        # Node for the service
        service_node_id = f"SERVICE:{incident.service_name}"
        if service_node_id not in self._graph:
            self._graph.add_node(service_node_id, type="service", name=incident.service_name)
            
        self._graph.add_edge(incident.id, service_node_id, relation="impacts")

        # Node for the root cause
        if incident.root_cause:
            cause_node_id = f"CAUSE:{incident.root_cause.lower().strip()}"
            if cause_node_id not in self._graph:
                self._graph.add_node(cause_node_id, type="root_cause", description=incident.root_cause)
            self._graph.add_edge(incident.id, cause_node_id, relation="caused_by")

        # Node for the linked deployment
        if incident.linked_deploy:
            deploy_node_id = f"DEPLOY:{incident.linked_deploy}"
            if deploy_node_id not in self._graph:
                self._graph.add_node(deploy_node_id, type="deployment", commit_sha=incident.linked_deploy)
            self._graph.add_edge(incident.id, deploy_node_id, relation="traced_to")

    def get_related_incidents(self, root_cause: str) -> list[str]:
        """
        Find all incidents that share the same exact root cause string.
        """
        cause_node_id = f"CAUSE:{root_cause.lower().strip()}"
        if cause_node_id not in self._graph:
            return []
            
        return [
            neighbor for neighbor in self._graph.neighbors(cause_node_id)
            if self._graph.nodes[neighbor].get("type") == "incident"
        ]
