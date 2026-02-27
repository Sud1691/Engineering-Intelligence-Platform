import json
from pathlib import Path

from eip.core.models import DeploymentEvent
from eip.pillars.risk_engine.scorer import RiskScorer


FIXTURES_DIR = Path(__file__).resolve().parents[3] / "fixtures" / "deployments"


def load_event(name: str) -> DeploymentEvent:
    payload = json.loads((FIXTURES_DIR / f"{name}.json").read_text())
    return DeploymentEvent.model_validate(payload)


def test_high_risk_deployment_scored_critical() -> None:
    scorer = RiskScorer()
    event = load_event("high_risk")

    result = scorer.score(event)

    assert result.tier == "CRITICAL"
    assert result.score >= 80
    # Deterministic: calling again yields same result
    result2 = scorer.score(event)
    assert result2.score == result.score
    assert result2.tier == result.tier


def test_medium_risk_deployment_scored_medium_or_high() -> None:
    scorer = RiskScorer()
    event = load_event("medium_risk")

    result = scorer.score(event)

    assert result.score >= 40
    assert result.tier in {"MEDIUM", "HIGH"}


def test_low_risk_deployment_scored_low() -> None:
    scorer = RiskScorer()
    event = load_event("low_risk")

    result = scorer.score(event)

    assert result.tier == "LOW"
    assert result.score < 40

