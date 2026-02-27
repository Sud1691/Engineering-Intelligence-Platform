"""
Natural Language Query Engine — the crown jewel of the EIP.

This engine receives plain English questions from users, classifies
their intent, extracts relevant context, parallel-fetches data from
the appropriate pillars, and uses Claude to synthesize the final answer.
"""

from __future__ import annotations

import json
from typing import Any, Dict

import structlog

from eip.core.llm import LLMClient
from eip.core.provider_registry import get_provider_registry
from eip.core.settings import get_settings


log = structlog.get_logger()


INTENT_TYPES = [
    "deployment_risk_query",      # "Is it safe to deploy X?"
    "blast_radius_query",         # "What breaks if Y goes down?"
    "incident_pattern_query",     # "Why does X keep having incidents?"
    "cost_query",                 # "Why did costs go up?"
    "compliance_query",           # "Are we compliant with X?"
    "team_health_query",          # "Which teams need attention?"
    "architecture_query",         # "What does service X depend on?"
    "general_platform_query",     # catch-all
]

CLASSIFIER_PROMPT = """
You are the intent classifier for the Engineering Intelligence Platform (EIP).
Your job is to read an engineering-related question and determine which of our data pillars should answer it.

Available intents:
{intents}

Rules:
1. Return ONLY a JSON object. No markdown, no explanations.
2. The JSON must have exactly this shape:
   {{
     "intent": "<one of the available intents>",
     "entities": {{
       "service_name": null,
       "team_name": null,
       "aws_account": null,
       "time_range": null
     }}
   }}
3. If you can identify any entities (e.g., service="payments-api", time_range="last week"), populate them. Otherwise leave null.
4. If you aren't sure, use "general_platform_query".
"""

SYNTHESIS_PROMPT = """
You are the Natural Language Query synthesizer for the Engineering Intelligence Platform (EIP).
You have been asked a question by an engineer or manager.
You have been provided with raw data fetched from our internal intelligence pillars.

Your job is to read the raw data and write a clear, concise, direct response answering the user's question.

Rules:
1. Be direct, actionable, and blameless.
2. Quote exact numbers and errors if they appear in the data.
3. If the data provided does not contain the answer, say "I don't have enough data to answer that" and explain what data is missing.
4. Keep the response to 2-4 paragraphs maximum, using formatting like bullet points where appropriate.
5. If assessing risk, provide your confidence level if you feel uncertain.
"""


class NLQEngine:
    """
    Cross-pillar Natural Language Query Engine.
    """

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm or LLMClient()

    async def answer_question(
        self,
        question: str,
        context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Process a question end-to-end.
        """
        context = context or {}

        # 1. Classify intent and extract entities
        classification = await self._classify_intent(question)
        intent = classification.get("intent", "general_platform_query")
        entities = classification.get("entities", {})

        # Merge extracted entities with explicit context passed by caller
        merged_context = {**entities, **context}

        log.info(
            "nlq_question_classified",
            question=question,
            intent=intent,
            context=merged_context,
        )

        # 2. Fetch data from pillars based on intent
        raw_data, sources = await self._fetch_pillar_data(intent, merged_context)

        # 3. Synthesize the final answer
        answer = await self._synthesize_answer(question, raw_data, merged_context)

        return {
            "intent": intent,
            "answer": answer,
            "sources": sources,
            "source_mode": get_settings().runtime_mode,
        }

    async def _classify_intent(self, question: str) -> Dict[str, Any]:
        """Use Claude to classify the user's question into an intent and extract entities."""
        
        system = CLASSIFIER_PROMPT.format(intents=", ".join(INTENT_TYPES))
        
        try:
            raw_response = await self._llm.complete(
                prompt=f"Question: {question}",
                system=system,
                max_tokens=256,
                expect_json=True
            )
            data = json.loads(raw_response)
            if data.get("intent") not in INTENT_TYPES:
                data["intent"] = "general_platform_query"
            return data
        except Exception as e:
            log.warning("nlq_intent_classification_failed", error=str(e), fallback="general_platform_query")
            return {"intent": "general_platform_query", "entities": {}}

    async def _fetch_pillar_data(
        self,
        intent: str,
        context: Dict[str, Any],
    ) -> tuple[str, list[str]]:
        """
        Route the request to the appropriate adapter-backed provider(s) and return
        raw data plus source attribution.
        """
        providers = get_provider_registry()
        try:
            return await providers.nlq.fetch_for_intent(intent, context)
        except Exception as e:
            log.error("nlq_data_fetch_failed", error=str(e), intent=intent)
            return (
                "No source data available due to provider failure.",
                ["provider_error"],
            )

    async def _synthesize_answer(self, question: str, raw_data: str, context: Dict[str, Any]) -> str:
        """
        Use Claude to write the final response.
        """
        prompt = (
            f"User Question: {question}\n\n"
            f"Context Extracted: {json.dumps(context)}\n\n"
            f"Raw Data from Pillars:\n{raw_data}\n\n"
            "Synthesize a helpful answer based ONLY on the data above."
        )

        try:
            return await self._llm.complete(
                prompt=prompt,
                system=SYNTHESIS_PROMPT,
                max_tokens=1024,
            )
        except Exception as e:
            log.error("nlq_synthesis_failed", error=str(e))
            return "I'm sorry, I was unable to process your query at this time."
