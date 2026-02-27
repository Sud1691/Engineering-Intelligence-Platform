from __future__ import annotations

import json
from typing import Sequence

from eip.core.llm import LLMClient
from eip.core.models import DeploymentEvent, RiskFactor, RiskScore


SYSTEM_PROMPT = """
You are the Deployment Risk Engine explainer for a large-scale engineering platform.

Your job is to explain, in clear and concise language, why a particular deployment
has been assigned a given deterministic risk score.

Constraints:
- Audience: senior engineers and engineering managers.
- Be specific about which factors increased or decreased risk.
- Prefer short paragraphs and bullet lists.
- Do NOT invent data that is not present in the input.
- Always call out environment, change size, risky files, timing, and test coverage.
- If confidence is low, explicitly state that uncertainty and why.

Output format:
- Return a single JSON object with the following shape.
- No markdown fences, no additional commentary.

{
  "explanation": "plain-text explanation in 2-4 paragraphs",
  "summary": "one-sentence TL;DR",
  "key_risks": ["bullet", "points"],
  "mitigations": ["bullet", "points"]
}
""".strip()


class RiskExplanationService:
    """
    Uses the central LLMClient to generate a natural language explanation
    for a RiskScore produced by the deterministic RiskScorer.
    """

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm or LLMClient()

    async def explain(
        self,
        event: DeploymentEvent,
        score: RiskScore,
        factors: Sequence[RiskFactor] | None = None,
    ) -> RiskScore:
        """
        Generate an LLM-based explanation and return an updated RiskScore.
        """

        factors = list(factors or score.factors)
        prompt = self._build_prompt(event, score, factors)

        raw = await self._llm.complete(
            prompt=prompt,
            system=SYSTEM_PROMPT,
            max_tokens=512,
            expect_json=True,
        )

        explanation, summary, key_risks, mitigations = self._parse_response(raw)

        # For now we only store the long-form explanation on the RiskScore.
        # Other fields can be wired into Slack / UI layers later.
        return score.copy(
            update={
                "explanation": explanation,
            }
        )

    def _build_prompt(
        self,
        event: DeploymentEvent,
        score: RiskScore,
        factors: Sequence[RiskFactor],
    ) -> str:
        factors_block = "\n".join(
            f"- {f.name}: score={f.score}, weight={f.weight}, evidence={f.evidence}"
            for f in factors
        )

        return (
            "You are given a deployment event, its deterministic risk score, and the\n"
            "list of contributing risk factors. Explain the risk in JSON.\n\n"
            "Deployment event:\n"
            f"{event.model_dump_json(indent=2)}\n\n"
            "Risk score:\n"
            f"{score.model_dump_json(indent=2, exclude={'explanation'})}\n\n"
            "Risk factors:\n"
            f"{factors_block}\n\n"
            "Remember: respond with JSON only, no markdown fences."
        )

    def _parse_response(
        self, raw: str
    ) -> tuple[str, str, list[str], list[str]]:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Fall back to treating the raw text as the explanation
            return raw, "", [], []

        explanation = str(data.get("explanation", "")).strip()
        summary = str(data.get("summary", "")).strip()
        key_risks = [str(x) for x in data.get("key_risks", [])]
        mitigations = [str(x) for x in data.get("mitigations", [])]
        return explanation, summary, key_risks, mitigations
