"""
Incident Intelligence: Postmortem Generator

Auto-generates draft post-mortems using incident chat transcripts and telemetry.
"""

from __future__ import annotations

import json
from typing import Any, Dict

import structlog

from eip.core.llm import LLMClient
from eip.core.models import Incident


log = structlog.get_logger()


SYSTEM_PROMPT = """
You are the Post-mortem Generator for the Engineering Intelligence Platform.
Your job is to write a draft blameless post-mortem document based on an incident's telemetry and an internal chat transcript.

Output format:
Return ONLY a JSON object containing the markdown sections of the post-mortem. No markdown fences.
{
  "summary": "1-paragraph executive summary",
  "timeline": "Bullet point timeline of what happened based on the transcript",
  "root_cause": "The specific technical root cause",
  "action_items": ["Suggested action item 1", "Suggested action item 2"]
}

Rules:
1. Always remain blameless. Focus on the system, never individuals.
2. If the root cause is unclear from the transcript, state "Investigation ongoing" under root_cause.
3. If key timeline details are uncertain, state that uncertainty explicitly.
"""


class PostmortemGenerator:
    """
    Auto-generates draft post-mortems based on incident data.
    """

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm or LLMClient()

    async def generate_draft(self, incident: Incident, chat_transcript: str) -> Dict[str, Any]:
        """
        Generate a draft post-mortem from incident details and Slack/chat transcripts.
        """
        prompt = (
            f"Incident Metadata: {incident.model_dump_json(exclude={'action_items'})}\n\n"
            f"Chat Transcript:\n{chat_transcript}\n\n"
            "Generate draft post-mortem."
        )

        try:
            raw_response = await self._llm.complete(
                prompt=prompt,
                system=SYSTEM_PROMPT,
                max_tokens=4096,
                expect_json=True
            )
            return json.loads(raw_response)
        except Exception as e:
            log.error("postmortem_generation_failed", error=str(e), incident_id=incident.id)
            return {
                "summary": f"Failed to generate post-mortem: {e}",
                "timeline": "",
                "root_cause": "Unknown",
                "action_items": []
            }
