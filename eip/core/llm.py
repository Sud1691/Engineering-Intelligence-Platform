from __future__ import annotations

import json
from typing import Any

try:
    import anthropic
except ImportError:  # pragma: no cover - only relevant when SDK is missing locally
    anthropic = None  # type: ignore[assignment]

from eip.core.settings import get_settings


class LLMClient:
    """
    Centralised wrapper around the Anthropic Claude client.

    This is the ONLY place that should instantiate the Anthropic client.
    All pillar code must depend on this class instead of using the SDK directly.
    """

    MODEL = "claude-3-5-sonnet-20241022"

    def __init__(self) -> None:
        self._runtime_mode = get_settings().runtime_mode
        if self._runtime_mode == "live":
            if anthropic is None:
                raise RuntimeError(
                    "anthropic SDK is required for live runtime mode but is not installed."
                )
            self._client = anthropic.Anthropic()
        else:
            self._client = None

    async def complete(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 1024,
        expect_json: bool = False,
    ) -> str:
        if self._runtime_mode == "stub":
            return self._stub_complete(prompt=prompt, system=system, expect_json=expect_json)

        response = self._client.messages.create(
            model=self.MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        if expect_json:
            return self._clean_json(raw)
        return raw

    def _clean_json(self, text: str) -> str:
        """
        Strip markdown fences that Claude may add around JSON output.
        """

        if text.startswith("```"):
            text = text.split("```", maxsplit=2)[1]
            if text.startswith("json"):
                text = text[4:]
        return text.strip()

    def _stub_complete(self, prompt: str, system: str, expect_json: bool) -> str:
        if not expect_json:
            return "Stub response generated in stub runtime mode."

        payload = self._stub_json_payload(prompt=prompt, system=system)
        return json.dumps(payload)

    def _stub_json_payload(self, prompt: str, system: str) -> Any:
        lowered_system = system.lower()
        lowered_prompt = prompt.lower()

        if '"intent"' in lowered_system and '"entities"' in lowered_system:
            intent = "general_platform_query"
            if "risk" in lowered_prompt or "deploy" in lowered_prompt:
                intent = "deployment_risk_query"
            elif "blast radius" in lowered_prompt or "depends" in lowered_prompt:
                intent = "blast_radius_query"
            elif "incident" in lowered_prompt:
                intent = "incident_pattern_query"
            elif "cost" in lowered_prompt or "spend" in lowered_prompt:
                intent = "cost_query"
            elif "compliance" in lowered_prompt or "audit" in lowered_prompt:
                intent = "compliance_query"

            return {
                "intent": intent,
                "entities": {
                    "service_name": "payments-api" if "payments" in lowered_prompt else None,
                    "team_name": None,
                    "aws_account": None,
                    "time_range": None,
                },
            }

        if '"explanation"' in lowered_system and '"key_risks"' in lowered_system:
            return {
                "explanation": "Stub explanation: risk factors indicate elevated deployment risk.",
                "summary": "Stub summary: review before production rollout.",
                "key_risks": ["Large code delta", "Infrastructure-affecting change"],
                "mitigations": ["Add rollout guardrails", "Monitor closely post-deploy"],
            }

        if '"executive_summary"' in lowered_system and '"top_anomalies"' in lowered_system:
            return {
                "executive_summary": "Stub narrative: cost increased due to one high-variance service.",
                "top_anomalies": ["payments-api spend increased 50% week-over-week"],
                "optimization_recommendations": [
                    "Rightsize low-utilization instances",
                    "Delete unattached storage volumes",
                ],
            }

        if '"escalation_risk"' in lowered_system and '"early_warning_signals"' in lowered_system:
            return {
                "escalation_risk": "MEDIUM",
                "reasoning": "Stub trajectory indicates recurring operational stress.",
                "early_warning_signals": ["Repeat alerts for dependent services"],
                "recommended_intervention": "Schedule focused reliability sprint.",
            }

        if '"pattern_name"' in lowered_system and '"affected_services"' in lowered_system:
            return []

        if '"summary"' in lowered_system and '"timeline"' in lowered_system and '"action_items"' in lowered_system:
            return {
                "summary": "Stub post-mortem summary.",
                "timeline": "- T0 issue detected\n- T+15 mitigation applied",
                "root_cause": "Investigation ongoing",
                "action_items": ["Add alert suppression controls", "Improve retry strategy"],
            }

        return {}
