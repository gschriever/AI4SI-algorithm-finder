from __future__ import annotations

from pydantic import BaseModel, Field


class Citation(BaseModel):
    source_id: str
    url: str
    title: str
    source_type: str


class MethodEvidenceCard(BaseModel):
    version: str = "1.0"
    method_family: str
    archetypes_supported: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    data_requirements: list[str] = Field(default_factory=list)
    constraint_support: str
    fairness_implications: list[str] = Field(default_factory=list)
    implementation_burden: str
    interpretability: str
    failure_modes: list[str] = Field(default_factory=list)
    non_ml_alternative: bool = False
    baseline: bool = False
    confidence: str = "medium"
    citations: list[Citation] = Field(default_factory=list)


class ResearchEvidenceResult(BaseModel):
    version: str = "1.0"
    search_queries: list[str]
    candidate_method_families: list[str]
    evidence_cards: list[MethodEvidenceCard]
    assumptions: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)


class RankedMethod(BaseModel):
    method_family: str
    weighted_score: float
    dimension_scores: dict[str, float]
    rationale: list[str] = Field(default_factory=list)
    rejected: bool = False
    rejection_reason: str | None = None
    baseline: bool = False


class RankedMethods(BaseModel):
    version: str = "1.0"
    ranked_methods: list[RankedMethod]
    supporting_methods: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
