from __future__ import annotations

from pydantic import BaseModel, Field


class GovernanceDecision(BaseModel):
    version: str = "1.0"
    decision: str
    reasons: list[str] = Field(default_factory=list)
    required_safeguards: list[str] = Field(default_factory=list)
    required_reviews: list[str] = Field(default_factory=list)
    monitoring_requirements: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)


class RecommendationPackage(BaseModel):
    version: str = "1.0"
    summary: str
    recommended_method_family: str | None = None
    alternatives_considered: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    safeguards: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
