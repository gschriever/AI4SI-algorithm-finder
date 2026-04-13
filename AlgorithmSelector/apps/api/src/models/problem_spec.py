from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class OptimisabilityStatus(str, Enum):
    NOT_OPTIMISABLE = "not_optimisable"
    PARTIALLY_OPTIMISABLE = "partially_optimisable"
    OPTIMISABLE = "optimisable"


class ProblemType(str, Enum):
    PREDICTION = "prediction"
    MATCHING = "matching"
    ALLOCATION = "allocation"
    FORECASTING = "forecasting"
    MIXED = "mixed"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DecisionVariable(BaseModel):
    name: str
    type: str
    unit: str | None = None
    granularity: str | None = None


class ActionSpace(BaseModel):
    description: str
    bounded: bool = True
    size: str
    feasibility_rules: list[str] = Field(default_factory=list)


class TargetVariable(BaseModel):
    name: str
    type: str
    label_definition: str | None = None
    label_quality: str = "unknown"
    proxy_risk_notes: list[str] = Field(default_factory=list)


class ObjectiveFunction(BaseModel):
    primary_objective: str
    direction: Literal["maximize", "minimize", "satisfy"]
    formal_expression: str | None = None
    business_or_social_meaning: str | None = None


class Constraint(BaseModel):
    name: str
    type: Literal["hard", "soft"]
    description: str
    formal_expression: str | None = None
    source: str = "operational"


class FairnessConstraint(BaseModel):
    name: str
    description: str
    protected_or_impacted_group: str
    constraint_type: str


class TimeHorizon(BaseModel):
    decision_frequency: str
    outcome_delay: str | None = None
    planning_horizon: str | None = None


class UncertaintyStructure(BaseModel):
    environment_stability: str
    aleatoric_uncertainty: str
    distribution_shift_risk: str
    counterfactual_uncertainty: str


class RequiredData(BaseModel):
    name: str
    type: str
    availability: str
    quality: str
    notes: str | None = None


class InterventionCostCapacity(BaseModel):
    intervention_cost_model: str | None = None
    capacity_constraints: list[str] = Field(default_factory=list)
    operational_bottlenecks: list[str] = Field(default_factory=list)


class EvaluationMetric(BaseModel):
    name: str
    type: str
    description: str | None = None


class HumanReviewRequirement(BaseModel):
    stage: str
    requirement: str


class GovernanceNotes(BaseModel):
    social_legitimacy_notes: list[str] = Field(default_factory=list)
    high_stakes: bool = False
    automation_recommendation: str = "decision_support_only"
    required_approvals: list[str] = Field(default_factory=list)


class ConfidenceMissingInformation(BaseModel):
    overall_confidence: ConfidenceLevel
    critical_unknowns: list[str] = Field(default_factory=list)
    assumptions_made: list[str] = Field(default_factory=list)
    fields_needing_validation: list[str] = Field(default_factory=list)


class ProblemSpec(BaseModel):
    version: str = "1.0"
    problem_summary: str
    optimisability_status: OptimisabilityStatus
    optimisability_rationale: list[str] = Field(default_factory=list)
    problem_type: ProblemType
    optimisation_subproblem: str
    decision_variable: DecisionVariable
    action_space: ActionSpace
    target_variable: TargetVariable
    objective_function: ObjectiveFunction
    constraints: list[Constraint] = Field(default_factory=list)
    thresholds: list[dict] = Field(default_factory=list)
    fairness_harm_constraints: list[FairnessConstraint] = Field(default_factory=list)
    time_horizon: TimeHorizon
    uncertainty_structure: UncertaintyStructure
    required_data: list[RequiredData] = Field(default_factory=list)
    feedback_loop_type: str
    intervention_cost_capacity_assumptions: InterventionCostCapacity = Field(default_factory=InterventionCostCapacity)
    evaluation_metric: list[EvaluationMetric] = Field(default_factory=list)
    baseline_options: list[str] = Field(default_factory=list)
    human_in_the_loop_requirements: list[HumanReviewRequirement] = Field(default_factory=list)
    governance_notes: GovernanceNotes = Field(default_factory=GovernanceNotes)
    confidence_missing_information: ConfidenceMissingInformation
    assumptions: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_critical_fields(self) -> "ProblemSpec":
        if self.optimisability_status != OptimisabilityStatus.NOT_OPTIMISABLE and not self.optimisation_subproblem:
            raise ValueError("optimisation_subproblem is required")
        if self.governance_notes.high_stakes and not self.human_in_the_loop_requirements:
            raise ValueError("high-stakes cases require human review requirements")
        return self
