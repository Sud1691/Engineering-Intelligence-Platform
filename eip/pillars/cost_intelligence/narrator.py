"""
Cost Intelligence Engine: Narrator

Turns AWS billing data into a plain English narrative.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import structlog

from eip.core.llm import LLMClient


log = structlog.get_logger()

SYSTEM_PROMPT = """
You are the Cost Intelligence Narrator for the Engineering Intelligence Platform.
Your job is to read AWS billing data, cost anomalies, and optimization opportunities
and synthesize them into a clear, actionable narrative for an engineering leader.

Input: JSON containing spend anomalies and current optimization opportunities.

Output format:
Return ONLY a JSON object. No markdown fences.
{
  "executive_summary": "1-2 sentence TL;DR of what changed and why.",
  "top_anomalies": ["Bullet string describing the anomaly and attributing it if possible"],
  "optimization_recommendations": ["Bullet string describing what to do to save money"]
}

Rules:
1. Explain *why* costs changed if apparent from the data (attribute to services/teams).
2. Produce a readable story, not just a regurgitation of numbers.
3. Keep the tone professional but direct.
4. If attribution is uncertain, explicitly say confidence is low for that attribution.
"""


class CostNarrator:
    """
    Generates plain-English cost narratives using Claude.
    """

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm or LLMClient()

    async def generate_narrative(
        self, anomalies: List[Dict[str, Any]], opportunities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a narrative explaining cost anomalies and opportunities.
        """
        payload = {
            "detected_anomalies": anomalies,
            "identified_opportunities": opportunities
        }
        
        prompt = (
            f"Review the following cost data:\n"
            f"{json.dumps(payload, indent=2)}\n\n"
            "Generate the cost narrative."
        )

        try:
            raw_response = await self._llm.complete(
                prompt=prompt,
                system=SYSTEM_PROMPT,
                max_tokens=1024,
                expect_json=True
            )
            return json.loads(raw_response)
        except Exception as e:
            log.error("cost_narrative_generation_failed", error=str(e))
            return {
                "executive_summary": "Failed to generate narrative.",
                "top_anomalies": [],
                "optimization_recommendations": []
            }
