from __future__ import annotations

from typing import Any

from eip.pillars.risk_engine.store.incident_db import IncidentDB


class LiveIncidentDataProvider:
    """
    Live incident provider backed by IncidentDB query paths.
    """

    def __init__(self) -> None:
        self._db = IncidentDB()

    def get_recent_incidents(
        self,
        service_name: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        if not service_name:
            # Cross-service list would require a dedicated GSI/query model.
            return []
        return self._db.get_incidents_by_service(service_name, limit=limit)
