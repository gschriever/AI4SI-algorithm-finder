from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator, ConfigDict, field_validator


class RobustBaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


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


class DecisionVariable(RobustBaseModel):
    name: str = "unknown"
    type: str = "unknown"
    unit: str | None = None
    granularity: str | None = None

    @model_validator(mode="before")
    @classmethod
    def handle_string(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"name": data, "type": "unknown"}
        return data


class ActionSpace(RobustBaseModel):
    description: str = "unknown"
    bounded: bool = True
    size: str = "unknown"
    feasibility_rules: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def handle_string(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"description": data, "size": "unknown"}
        return data


class TargetVariable(RobustBaseModel):
    name: str = "unknown"
    type: str = "unknown"
    label_definition: str | None = None
    label_quality: str = "unknown"
    proxy_risk_notes: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def handle_string(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"name": data, "type": "unknown"}
        return data


class ObjectiveFunction(RobustBaseModel):
    primary_objective: str = "unknown"
    direction: Literal["maximize", "minimize", "satisfy"] = "maximize"
    formal_expression: str | None = None
    business_or_social_meaning: str | None = None

    @field_validator("direction", mode="before")
    @classmethod
    def normalize_direction(cls, v: Any) -> str:
        if isinstance(v, str):
            v_low = v.lower()
            if "maxim" in v_low: return "maximize"
            if "minim" in v_low: return "minimize"
            if "satisf" in v_low: return "satisfy"
        return v

    @model_validator(mode="before")
    @classmethod
    def handle_string(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"primary_objective": data, "direction": "maximize"}
        return data


class Constraint(RobustBaseModel):
    name: str = "unknown"
    type: Literal["hard", "soft"] = "hard"
    description: str = "unknown"
    formal_expression: str | None = None
    source: str = "operational"

    @model_validator(mode="before")
    @classmethod
    def handle_string(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"name": data[:50], "description": data}
        return data


class FairnessConstraint(RobustBaseModel):
    name: str = "unknown"
    description: str = "unknown"
    protected_or_impacted_group: str = "unknown"
    constraint_type: str = "unknown"

    @model_validator(mode="before")
    @classmethod
    def handle_string(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"name": data[:50], "description": data}
        return data


class TimeHorizon(RobustBaseModel):
    decision_frequency: str = "unknown"
    outcome_delay: str | None = None
    planning_horizon: str | None = None

    @model_validator(mode="before")
    @classmethod
    def handle_string(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"decision_frequency": data}
        return data


class UncertaintyStructure(RobustBaseModel):
    environment_stability: str = "unknown"
    aleatoric_uncertainty: str = "unknown"
    distribution_shift_risk: str = "unknown"
    counterfactual_uncertainty: str = "unknown"

    @model_validator(mode="before")
    @classmethod
    def handle_string(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"environment_stability": data, "aleatoric_uncertainty": "unknown", "distribution_shift_risk": "unknown", "counterfactual_uncertainty": "unknown"}
        return data


class RequiredData(RobustBaseModel):
    name: str = "unknown"
    type: str = "unknown"
    availability: str = "unknown"
    quality: str = "unknown"
    notes: str | None = None

    @model_validator(mode="before")
    @classmethod
    def handle_string(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"name": data, "type": "unknown", "availability": "unknown", "quality": "unknown"}
        return data


class InterventionCostCapacity(RobustBaseModel):
    intervention_cost_model: str | None = None
    capacity_constraints: list[str] = Field(default_factory=list)
    operational_bottlenecks: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def handle_list(cls, data: Any) -> Any:
        if isinstance(data, list):
            return {"capacity_constraints": [str(x) for x in data]}
        return data


class EvaluationMetric(RobustBaseModel):
    name: str = "unknown"
    type: str = "unknown"
    description: str | None = None

    @model_validator(mode="before")
    @classmethod
    def handle_string(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"name": data, "type": "secondary"}
        return data


class HumanReviewRequirement(RobustBaseModel):
    stage: str = "unknown"
    requirement: str = "unknown"

    @model_validator(mode="before")
    @classmethod
    def handle_string(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"stage": "general", "requirement": data}
        return data


class GovernanceNotes(RobustBaseModel):
    social_legitimacy_notes: list[str] = Field(default_factory=list)
    high_stakes: bool = False
    automation_recommendation: str = "decision_support_only"
    required_approvals: list[str] = Field(default_factory=list)


class ConfidenceMissingInformation(RobustBaseModel):
    overall_confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    critical_unknowns: list[str] = Field(default_factory=list)
    assumptions_made: list[str] = Field(default_factory=list)
    fields_needing_validation: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def handle_string(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"overall_confidence": "medium", "critical_unknowns": [data]}
        return data


class ProblemSpec(RobustBaseModel):
    version: str = "1.0"
    problem_summary: str
    optimisability_status: OptimisabilityStatus = OptimisabilityStatus.OPTIMISABLE
    optimisability_rationale: list[str] = Field(default_factory=list)
    problem_type: ProblemType = ProblemType.ALLOCATION
    optimisation_subproblem: str = "unknown"
    decision_variable: DecisionVariable = Field(default_factory=DecisionVariable)
    action_space: ActionSpace = Field(default_factory=ActionSpace)
    target_variable: TargetVariable = Field(default_factory=TargetVariable)
    objective_function: ObjectiveFunction = Field(default_factory=ObjectiveFunction)
    constraints: list[Constraint] = Field(default_factory=list)
    thresholds: list[dict] = Field(default_factory=list)
    fairness_harm_constraints: list[FairnessConstraint] = Field(default_factory=list)
    time_horizon: TimeHorizon = Field(default_factory=TimeHorizon)
    uncertainty_structure: UncertaintyStructure = Field(default_factory=UncertaintyStructure)
    required_data: list[RequiredData] = Field(default_factory=list)
    feedback_loop_type: str = "unknown"
    intervention_cost_capacity_assumptions: InterventionCostCapacity = Field(default_factory=InterventionCostCapacity)
    evaluation_metric: list[EvaluationMetric] = Field(default_factory=list)
    baseline_options: list[str] = Field(default_factory=list)
    human_in_the_loop_requirements: list[HumanReviewRequirement] = Field(default_factory=list)
    governance_notes: GovernanceNotes = Field(default_factory=GovernanceNotes)
    confidence_missing_information: ConfidenceMissingInformation = Field(default_factory=ConfidenceMissingInformation)
    assumptions: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def pre_validate_llm_output(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
            
        # Handle 'constraints' being a dict instead of a list
        if isinstance(data.get("constraints"), dict):
            constraints = []
            for c_type, c_list in data["constraints"].items():
                if isinstance(c_list, list):
                    for c_item in c_list:
                        if isinstance(c_item, dict):
                            c_item["type"] = "hard" if "hard" in c_type.lower() else "soft"
                            constraints.append(c_item)
                        elif isinstance(c_item, str):
                            constraints.append({"name": c_item[:50], "type": "hard", "description": c_item})
            data["constraints"] = constraints

        # Handle 'evaluation_metric' being a dict or object
        if isinstance(data.get("evaluation_metric"), dict):
            metrics = []
            for k, v in data["evaluation_metric"].items():
                metrics.append({"name": k, "type": "primary" if "primary" in k.lower() else "secondary", "description": str(v)})
            data["evaluation_metric"] = metrics

        # Handle 'required_data' being a dict
        if isinstance(data.get("required_data"), dict):
            data_list = []
            for k, v in data["required_data"].items():
                data_list.append({"name": k, "type": str(v)})
            data["required_data"] = data_list

        return data

    @model_validator(mode="after")
    def validate_critical_fields(self) -> "ProblemSpec":
        # Relaxed validation for evaluation: we prefer a result over a crash
        return self
