from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict

from models.governance import GovernanceDecision, RecommendationPackage
from models.method_card import RankedMethods, ResearchEvidenceResult
from models.problem_spec import ProblemSpec


class IntakeDiagnosisResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    
    version: str = "1.0"
    social_goal: str
    decision_to_be_made: str
    action_under_consideration: str
    target_of_interest: str
    key_constraints: list[str] = Field(default_factory=list)
    optimisability_status: str
    candidate_optimisation_subproblem: str
    rationale: list[str] = Field(default_factory=list)
    archetype_hypotheses: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    confidence: str = "medium"
    assumptions: list[str] = Field(default_factory=list)


class ClarifyingQuestion(BaseModel):
    question_id: str
    field: str
    question: str
    why_it_matters: str


class ClarificationAnswer(BaseModel):
    question_id: str
    answer: str


class StartSessionRequest(BaseModel):
    session_id: str
    narrative: str
    prior_state: dict = Field(default_factory=dict)


class AnswerClarificationsRequest(BaseModel):
    session_id: str
    answers: list[ClarificationAnswer] = Field(default_factory=list)


class PipelineArtifacts(BaseModel):
    intake_diagnosis: IntakeDiagnosisResult
    problem_spec: ProblemSpec | None = None
    research: ResearchEvidenceResult | None = None
    ranking: RankedMethods | None = None
    governance: GovernanceDecision | None = None
    recommendation: RecommendationPackage | None = None


class PipelineResponse(BaseModel):
    session_id: str
    status: str
    artifacts: PipelineArtifacts
    pending_questions: list[ClarifyingQuestion] = Field(default_factory=list)
    clarification_rounds: int = 0


class SessionState(BaseModel):
    session_id: str
    narrative: str
    prior_state: dict = Field(default_factory=dict)
    status: str
    clarification_rounds: int = 0
    pending_questions: list[ClarifyingQuestion] = Field(default_factory=list)
    answered_questions: list[ClarificationAnswer] = Field(default_factory=list)
    artifacts: PipelineArtifacts
