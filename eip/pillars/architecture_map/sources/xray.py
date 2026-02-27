"""
AWS X-Ray ingestor for the Living Architecture Map.

X-Ray service maps are a rich source of runtime service → service
dependencies. For the MVP we accept an already-parsed representation of
the X-Ray service graph and convert it into simple (caller, callee)
pairs.
"""

from __future__ import annotations

from typing import Iterable, List, Tuple


def extract_service_dependencies_from_xray(
    edges: Iterable[tuple[str, str]],
) -> List[Tuple[str, str]]:
    """
    Normalise an iterable of (caller, callee) tuples into a list.
    """

    return [(caller, callee) for caller, callee in edges if caller != callee]

