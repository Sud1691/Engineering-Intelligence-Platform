"""
Git extractor for the Deployment Risk Engine.
"""

from __future__ import annotations

from typing import Any, Dict, List

import structlog

from eip.core.models import DeploymentEvent


log = structlog.get_logger()


class GitExtractor:
    """
    Extracts risk signals from Git repositories.
    
    For the MVP, this acts on parsed Git payload data rather than calling
    out to the GitHub API, though it could be extended to do so.
    """

    def extract_coverage_delta(self, payload: Dict[str, Any]) -> float | None:
        """
        Extract the change in test coverage from a CI payload.
        """
        return payload.get("coverage_delta")

    def analyze_complexity(self, changed_files: List[str]) -> str:
        """
        Analyze the complexity of a changeset based on the files touched.
        """
        core_files = sum(1 for f in changed_files if "src/" in f or "core/" in f)
        if core_files > 10:
            return "high"
        elif core_files > 3:
            return "medium"
        return "low"

    def analyze_diff(self, event: DeploymentEvent) -> Dict[str, Any]:
        """
        Analyze the git diff size and characteristics.
        """
        return {
            "lines_added": event.lines_added,
            "lines_deleted": event.lines_deleted,
            "total_delta": event.lines_added + event.lines_deleted,
            "files_changed_count": len(event.changed_files),
            "complexity_estimate": self.analyze_complexity(event.changed_files)
        }
