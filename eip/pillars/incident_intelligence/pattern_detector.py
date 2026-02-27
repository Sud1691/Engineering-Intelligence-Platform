"""
Incident Intelligence: Pattern Detector

Uses Claude to detect recurring root causes across time and services.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import structlog

from eip.core.llm import LLMClient
from eip.core.models import Incident


log = structlog.get_logger()

SYSTEM_PROMPT = """
You are the Incident Pattern Detector for the Engineering Intelligence Platform.
Your job is to read a list of recent incidents across all services and detect recurring root causes or patterns.

Input format:
JSON array of incident objects containing service name, symptom, and root cause (if known).

Output format:
Return ONLY a JSON array, no markdown fences.
Each object must represent a distinct pattern:
[
  {
    "pattern_name": "Short descriptive name",
    "description": "Why this is happening across services",
    "affected_services": ["service-a", "service-b"],
    "incident_ids": ["INC-123", "INC-456"],
    "recommended_remediation": "How to fix this organizationally"
  }
]
If no patterns exist, return an empty array: []
If confidence in a detected pattern is low, mention "low confidence" in the description.
"""


class IncidentPatternDetector:
    """
    Detects cross-team recurring root causes using LLM synthesis of recent incidents.
    """

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm or LLMClient()

    async def detect_patterns(self, incidents: List[Incident]) -> List[Dict[str, Any]]:
        """
        Analyze a batch of recent incidents and return identified patterns.
        """
        if not incidents or len(incidents) < 2:
            return []

        # Summarize incidents to save tokens
        payload = [
            {
                "id": inc.id,
                "service": inc.service_name,
                "severity": inc.severity,
                "root_cause": inc.root_cause or "unknown"
            }
            for inc in incidents
        ]
        
        prompt = f"Recent incidents:\n{json.dumps(payload, indent=2)}\n\nIdentify patterns if any."
        
        try:
            raw_response = await self._llm.complete(
                prompt=prompt,
                system=SYSTEM_PROMPT,
                max_tokens=1024,
                expect_json=True
            )
            data = json.loads(raw_response)
            if isinstance(data, list):
                return data
            return []
        except Exception as e:
            log.error("incident_pattern_detection_failed", error=str(e))
            return []
