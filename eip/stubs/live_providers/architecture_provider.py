from __future__ import annotations

from eip.core.models import ServiceNode
from eip.stubs.providers import StubArchitectureDataProvider


class LiveArchitectureDataProvider:
    """
    Transitional architecture provider.

    It keeps the same interface while live extractors are wired to real sources.
    """

    def __init__(self) -> None:
        self._fallback = StubArchitectureDataProvider()

    def get_services(self) -> list[ServiceNode]:
        return self._fallback.get_services()

    def get_extra_dependencies(self) -> list[tuple[str, str]]:
        return self._fallback.get_extra_dependencies()
