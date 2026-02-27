from __future__ import annotations

import asyncio
import json

from eip.intelligence.nlq_engine import NLQEngine


class FakeCostIntentLLM:
    async def complete(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 1024,
        expect_json: bool = False,
    ) -> str:
        _ = (prompt, max_tokens)
        if expect_json:
            return json.dumps(
                {
                    "intent": "cost_query",
                    "entities": {
                        "service_name": "payments-api",
                        "team_name": None,
                        "aws_account": None,
                        "time_range": None,
                    },
                }
            )
        return "Cost answer synthesized."


def test_nlq_engine_returns_intent_and_sources() -> None:
    engine = NLQEngine(llm=FakeCostIntentLLM())  # type: ignore[arg-type]

    result = asyncio.run(engine.answer_question("Why did costs go up for payments?"))

    assert result["intent"] == "cost_query"
    assert "stub:cost_provider" in result["sources"]
    assert result["source_mode"] == "stub"
    assert isinstance(result["answer"], str)
