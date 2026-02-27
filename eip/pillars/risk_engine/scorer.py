from __future__ import annotations

from dataclasses import dataclass
from typing import List

from eip.core.models import DeploymentEvent, RiskFactor, RiskScore


@dataclass
class RiskWeights:
    """
    Tunable weights for the deterministic risk model.

    These can later be recalibrated by the feedback loop using
    historical incident data.
    """

    env_production: float = 25.0
    env_staging: float = 5.0
    env_dev: float = 1.0

    large_change: float = 20.0
    medium_change: float = 10.0
    small_change: float = 3.0

    risky_files: float = 20.0
    safe_files: float = 0.0

    off_hours: float = 10.0
    friday_evening: float = 15.0

    negative_coverage: float = 15.0
    positive_coverage: float = -5.0

    hotfix_branch: float = 10.0


class RiskScorer:
    """
    Deterministic deployment risk scoring.

    Same input → same score, always.
    No LLM calls here; this is pure rules + weights.
    """

    def __init__(self, weights: RiskWeights | None = None) -> None:
        self._weights = weights or RiskWeights()

    def score(self, event: DeploymentEvent) -> RiskScore:
        factors: List[RiskFactor] = []

        probability_score = 0.0
        impact_score = 0.0

        # Environment factor
        env_factor = self._environment_factor(event)
        factors.append(env_factor)
        probability_score += env_factor.score
        impact_score += env_factor.score

        # Change size factor
        size_factor = self._change_size_factor(event)
        factors.append(size_factor)
        probability_score += size_factor.score

        # Risky files factor
        files_factor = self._risky_files_factor(event)
        factors.append(files_factor)
        probability_score += files_factor.score
        impact_score += files_factor.score * 0.5

        # Deployment timing factor
        timing_factor = self._timing_factor(event)
        factors.append(timing_factor)
        probability_score += timing_factor.score

        # Test coverage factor
        coverage_factor = self._coverage_factor(event)
        factors.append(coverage_factor)
        probability_score += coverage_factor.score

        # Branch naming factor
        branch_factor = self._branch_factor(event)
        factors.append(branch_factor)
        probability_score += branch_factor.score

        # Normalise scores to 0–100
        probability = max(0, min(int(round(probability_score)), 100))
        impact = max(0, min(int(round(impact_score or probability_score)), 100))

        combined = int(round(min(probability * 0.6 + impact * 0.4, 100)))
        tier = self._tier_for_score(combined)
        recommended_action = self._recommended_action_for_tier(tier)

        return RiskScore(
            score=combined,
            tier=tier,
            probability_score=probability,
            impact_score=impact,
            recommended_action=recommended_action,
            explanation="",  # to be populated by explainer
            factors=factors,
            resulted_in_incident=False,
        )

    def _environment_factor(self, event: DeploymentEvent) -> RiskFactor:
        if event.environment == "production":
            score = self._weights.env_production
            name = "environment_production"
        elif event.environment == "staging":
            score = self._weights.env_staging
            name = "environment_staging"
        else:
            score = self._weights.env_dev
            name = "environment_dev"

        return RiskFactor(
            name=name,
            score=score,
            weight=1.0,
            evidence=f"environment={event.environment}",
        )

    def _change_size_factor(self, event: DeploymentEvent) -> RiskFactor:
        delta = event.lines_added + event.lines_deleted
        if delta >= 1000:
            score = self._weights.large_change
            bucket = "large"
        elif delta >= 200:
            score = self._weights.medium_change
            bucket = "medium"
        else:
            score = self._weights.small_change
            bucket = "small"

        return RiskFactor(
            name=f"change_size_{bucket}",
            score=score,
            weight=1.0,
            evidence=f"lines_changed={delta}",
        )

    def _risky_files_factor(self, event: DeploymentEvent) -> RiskFactor:
        risky_prefixes = (
            "database/migrations",
            "migrations/",
            "infra/",
            "terraform/",
            "k8s/",
        )

        risky_files = [
            path for path in event.changed_files if path.startswith(risky_prefixes)
        ]

        if risky_files:
            score = self._weights.risky_files
            name = "risky_files_present"
            evidence = f"risky_files={len(risky_files)}"
        else:
            score = self._weights.safe_files
            name = "no_risky_files"
            evidence = "no known risky paths touched"

        return RiskFactor(
            name=name,
            score=score,
            weight=1.0,
            evidence=evidence,
        )

    def _timing_factor(self, event: DeploymentEvent) -> RiskFactor:
        # 1=Mon, 7=Sun
        is_friday = event.deploy_day == 5
        is_weekend = event.deploy_day in (6, 7)
        off_hours = event.deploy_hour < 9 or event.deploy_hour >= 18

        if is_friday and event.deploy_hour >= 16:
            score = self._weights.friday_evening
            name = "friday_evening_deploy"
        elif is_weekend or off_hours:
            score = self._weights.off_hours
            name = "off_hours_deploy"
        else:
            score = 0.0
            name = "business_hours_deploy"

        evidence = f"deploy_day={event.deploy_day}, deploy_hour={event.deploy_hour}"
        return RiskFactor(
            name=name,
            score=score,
            weight=1.0,
            evidence=evidence,
        )

    def _coverage_factor(self, event: DeploymentEvent) -> RiskFactor:
        if event.coverage_delta is None:
            score = 0.0
            name = "coverage_unknown"
            evidence = "coverage_delta=None"
        elif event.coverage_delta < 0:
            score = self._weights.negative_coverage
            name = "coverage_regressed"
            evidence = f"coverage_delta={event.coverage_delta}"
        elif event.coverage_delta > 0:
            score = self._weights.positive_coverage
            name = "coverage_improved"
            evidence = f"coverage_delta={event.coverage_delta}"
        else:
            score = 0.0
            name = "coverage_unchanged"
            evidence = "coverage_delta=0"

        return RiskFactor(
            name=name,
            score=score,
            weight=1.0,
            evidence=evidence,
        )

    def _branch_factor(self, event: DeploymentEvent) -> RiskFactor:
        if event.branch.startswith("hotfix/"):
            score = self._weights.hotfix_branch
            name = "hotfix_branch"
        else:
            score = 0.0
            name = "normal_branch"

        return RiskFactor(
            name=name,
            score=score,
            weight=1.0,
            evidence=f"branch={event.branch}",
        )

    def _tier_for_score(self, score: int) -> str:
        if score >= 80:
            return "CRITICAL"
        if score >= 65:
            return "HIGH"
        if score >= 40:
            return "MEDIUM"
        return "LOW"

    def _recommended_action_for_tier(self, tier: str) -> str:
        if tier == "CRITICAL":
            return "Block deployment and require senior engineer approval."
        if tier == "HIGH":
            return "Proceed only with explicit approval and on-call acknowledgment."
        if tier == "MEDIUM":
            return "Proceed with caution; monitor closely after deployment."
        return "Safe to deploy under normal change management process."

