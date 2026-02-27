"""
Terraform state ingestor for the Living Architecture Map.

For the MVP we assume Terraform state has already been reduced into a
simple structure that maps service names to the list of services they
depend on (e.g. via module naming conventions or tags).
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Tuple


def extract_service_dependencies_from_terraform_state(
    state: Dict[str, Iterable[str]],
) -> List[Tuple[str, str]]:
    """
    Convert a mapping of service → iterable[dependency_service] into a flat
    list of (service, dependency_service) pairs.
    """

    dependencies: list[tuple[str, str]] = []

    for service, deps in state.items():
        for dep in deps:
            if service != dep:
                dependencies.append((service, dep))

    return dependencies

