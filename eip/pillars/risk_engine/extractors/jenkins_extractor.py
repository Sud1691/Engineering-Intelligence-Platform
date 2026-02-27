"""
Jenkins extractor for the Deployment Risk Engine.
"""

from __future__ import annotations

from typing import Any, Dict

import structlog


log = structlog.get_logger()


class JenkinsExtractor:
    """
    Extracts risk signals from Jenkins build payloads.
    
    This includes build history, flakiness signals, and test execution times.
    """

    def extract_flakiness_signal(self, build_payload: Dict[str, Any]) -> str:
        """
        Analyze a Jenkins build payload to detect flakiness.
        For MVP, we use naive indicators present in the payload.
        """
        # E.g., if tests passed on a retry, it's a flaky build
        retries = build_payload.get("test_retries", 0)
        if retries > 3:
            return "high"
        elif retries > 0:
            return "medium"
        return "low"

    def analyze_build_duration(self, current_duration_s: int, baseline_duration_s: int | None) -> float:
        """
        Compare current build duration against a baseline to detect anomalies.
        Returns the percentage change.
        """
        if not baseline_duration_s or baseline_duration_s == 0:
            return 0.0
            
        return ((current_duration_s - baseline_duration_s) / baseline_duration_s) * 100.0
