import asyncio
import json

from eip.core.models import DeploymentEvent, RiskFactor, RiskScore
from eip.pillars.risk_engine.explainer import RiskExplanationService


class FakeLLMClient:
    async def complete(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 1024,
        expect_json: bool = False,
    ) -> str:
        _ = (prompt, system, max_tokens, expect_json)
        payload = {
            "explanation": "This is a test explanation.",
            "summary": "Test summary.",
            "key_risks": ["Risk A", "Risk B"],
            "mitigations": ["Mitigation X"],
        }
        return json.dumps(payload)


def test_explainer_populates_explanation_field() -> None:
    event = DeploymentEvent(
        service_name="test-service",
        environment="production",
        branch="main",
        commit_sha="deadbeef",
        commit_message="Test",
        commit_author="Tester",
        commit_author_email="tester@example.com",
        changed_files=["src/app.py"],
        lines_added=10,
        lines_deleted=0,
        deploy_hour=10,
        deploy_day=2,
        build_url="https://jenkins.example.com/job/test/1",
        coverage_delta=0.0,
    )
    factors = [
        RiskFactor(
            name="environment_production",
            score=25.0,
            weight=1.0,
            evidence="environment=production",
        )
    ]
    score = RiskScore(
        score=50,
        tier="MEDIUM",
        probability_score=50,
        impact_score=50,
        recommended_action="Proceed with caution.",
        explanation="",
        factors=factors,
        resulted_in_incident=False,
    )

    explainer = RiskExplanationService(llm=FakeLLMClient())  # type: ignore[arg-type]

    updated = asyncio.get_event_loop().run_until_complete(
        explainer.explain(event, score, factors)
    )

    assert updated.explanation == "This is a test explanation."

