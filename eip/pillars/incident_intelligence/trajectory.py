"""
Incident Intelligence: Trajectory Predictor

Predicts incident trajectories by recognizing early warning signals.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import structlog

from eip.core.llm import LLMClient
from eip.core.models import Incident


log = structlog.get_logger()


SYSTEM_PROMPT = """
You are the Incident Trajectory Predictor for the Engineering Intelligence Platform.
Your job is to read a team's recent incident and deployment history and predict if they are heading toward a major escalation (e.g. SEV-1).

Input: JSON containing recent deployments (with high risk factors), recent low-sev incidents, and open action items.

Output format:
Return ONLY a JSON object. No markdown fences.
{
  "escalation_risk": "HIGH" | "MEDIUM" | "LOW",
  "confidence": "HIGH" | "MEDIUM" | "LOW",
  "reasoning": "Explanation based on the data",
  "early_warning_signals": ["bullet points"],
  "recommended_intervention": "What management should do"
}
If confidence is MEDIUM or LOW, explain why uncertainty exists.
"""


class IncidentTrajectoryPredictor:
    """
    Predicts if a team or service is heading toward a major incident based on early signals.
    """

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm or LLMClient()

    async def predict_trajectory(self, service_name: str, recent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze recent telemetry for a service and predict escalation risk.
        Requires data from Risk Engine, Incident DB, and Action Item DB.
        """
        prompt = (
            f"Service: {service_name}\n"
            f"Telemetry:\n{json.dumps(recent_data, indent=2)}\n\n"
            "Predict trajectory."
        )

        try:
            raw_response = await self._llm.complete(
                prompt=prompt,
                system=SYSTEM_PROMPT,
                max_tokens=512,
                expect_json=True
            )
            return json.loads(raw_response)
        except Exception as e:
            log.error("incident_trajectory_prediction_failed", error=str(e), service=service_name)
            return {
                "escalation_risk": "UNKNOWN",
                "confidence": "LOW",
                "reasoning": f"Prediction failed: {e}",
                "early_warning_signals": [],
                "recommended_intervention": "None"
            }
