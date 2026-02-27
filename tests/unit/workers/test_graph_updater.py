from __future__ import annotations

import asyncio

from eip.workers.graph_updater import process_architecture_update, updater


def test_graph_updater_applies_payload_snapshot() -> None:
    payload = {
        "event_type": "snapshot.refresh",
        "correlation_id": "corr-1",
        "services": [
            {
                "name": "orders-api",
                "tier": "important",
                "team": "orders",
                "aws_account": "111111111111",
                "dependencies": ["payments-api"],
                "consumers": [],
                "health": "healthy",
                "monthly_cost": 200.0,
            },
            {
                "name": "payments-api",
                "tier": "critical",
                "team": "payments",
                "aws_account": "111111111111",
                "dependencies": [],
                "consumers": ["orders-api"],
                "health": "healthy",
                "monthly_cost": 800.0,
            },
        ],
        "extra_dependencies": [["orders-api", "fraud-service"]],
    }

    asyncio.run(process_architecture_update(payload))

    graph = updater.graph
    assert graph is not None
    assert "orders-api" in graph
    assert graph.has_edge("orders-api", "payments-api")
    assert graph.has_edge("orders-api", "fraud-service")


def test_graph_updater_falls_back_to_provider_snapshot() -> None:
    asyncio.run(process_architecture_update({"event_type": "snapshot.refresh"}))

    graph = updater.graph
    assert graph is not None
    assert "payments-api" in graph
