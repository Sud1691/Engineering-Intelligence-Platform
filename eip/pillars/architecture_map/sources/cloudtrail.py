"""
CloudTrail ingestor for the Living Architecture Map.

For the MVP we model this as a pure function that accepts already-parsed
CloudTrail events and returns pairs of (caller_service, callee_service)
representing observed dependencies.
"""

from __future__ import annotations

from typing import Iterable, List, Tuple


def extract_service_dependencies_from_cloudtrail(
    events: Iterable[dict],
) -> List[Tuple[str, str]]:
    """
    Very small heuristic extractor that looks for service → service calls
    encoded in CloudTrail event tags or resource ARNs.

    In real deployments this would understand your tagging strategy
    (e.g. `service=<name>` tags) and map AWS resources back to logical
    services. Here we keep the logic simple so it can be extended later.
    """

    dependencies: list[tuple[str, str]] = []

    for event in events:
        detail = event.get("detail", {})
        source = detail.get("source_service")
        target = detail.get("target_service")
        if source and target and source != target:
            dependencies.append((source, target))

    return dependencies

