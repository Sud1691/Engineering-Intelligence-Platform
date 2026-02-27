from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Generic, Literal, Optional, TypeVar

from pydantic import BaseModel


class ServiceTier(str, Enum):
    CRITICAL = "critical"   # tier 1 — payments, auth, checkout
    IMPORTANT = "important"  # tier 2 — most product services
    STANDARD = "standard"   # tier 3 — internal tools, reporting


class DeploymentEvent(BaseModel):
    service_name: str
    environment: Literal["production", "staging", "dev"]
    branch: str
    commit_sha: str
    commit_message: str
    commit_author: str
    commit_author_email: str
    changed_files: list[str]
    lines_added: int
    lines_deleted: int
    deploy_hour: int  # 0–23
    deploy_day: int  # 1=Mon, 7=Sun
    build_url: str
    coverage_delta: Optional[float] = None  # % change in test coverage


@dataclass
class RiskFactor:
    name: str
    score: float
    weight: float
    evidence: str


class RiskScore(BaseModel):
    score: int  # 0-100
    tier: str  # LOW|MEDIUM|HIGH|CRITICAL
    probability_score: int
    impact_score: int
    recommended_action: str
    explanation: str
    factors: list[RiskFactor]
    resulted_in_incident: bool = False


class ActionItem(BaseModel):
    id: str
    description: str
    owner: Optional[str] = None
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class Incident(BaseModel):
    id: str
    service_name: str
    severity: str  # SEV-1 through SEV-4
    started_at: datetime
    resolved_at: Optional[datetime] = None
    root_cause: Optional[str] = None
    linked_deploy: Optional[str] = None  # commit_sha of likely cause
    action_items: list[ActionItem] = []
    recurrence_of: Optional[str] = None  # incident_id if this is a repeat


class ServiceNode(BaseModel):
    name: str
    tier: ServiceTier
    team: str
    aws_account: str
    dependencies: list[str]
    consumers: list[str]
    health: str  # healthy|degraded|down
    last_deploy: Optional[datetime] = None
    monthly_cost: Optional[float] = None


T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    meta: dict = {}

