from __future__ import annotations

from adapters.prompt_executor import PromptExecutor
from adapters.research_broker import ResearchBroker
from models.session import (
    AnswerClarificationsRequest,
    ClarificationAnswer,
    PipelineArtifacts,
    PipelineResponse,
    SessionState,
    StartSessionRequest,
)
from services.clarification_service import ClarificationService
from services.diagnosis_service import DiagnosisService
from services.explanation_service import ExplanationService
from services.formalization_service import FormalizationService
from services.governance_service import GovernanceService
from services.ranking_service import RankingService
from storage.session_repo import SessionRepository


class CoordinatorService:
    def __init__(self) -> None:
        self.prompts = PromptExecutor()
        self.research_broker = ResearchBroker()
        self.diagnosis_service = DiagnosisService()
        self.formalization_service = FormalizationService()
        self.clarification_service = ClarificationService()
        self.governance_service = GovernanceService()
        self.ranking_service = RankingService()
        self.explanation_service = ExplanationService()
        self.repo = SessionRepository()

    def start_session(self, request: StartSessionRequest) -> PipelineResponse:
        return self._run_pipeline(
            session_id=request.session_id,
            narrative=request.narrative,
            prior_state=request.prior_state,
            answered_questions=[],
            clarification_rounds=0,
        )

    def answer_clarifications(self, request: AnswerClarificationsRequest) -> PipelineResponse:
        if not self.repo.has_state(request.session_id):
            raise ValueError("Session not found")
        state = self.repo.load_state(request.session_id)
        prior_state = dict(state.prior_state)
        question_lookup = {question.question_id: question for question in state.pending_questions}
        merged_clarifications = dict(prior_state.get("clarifications", {}))
        for answer in request.answers:
            question = question_lookup.get(answer.question_id)
            key = question.field if question else answer.question_id
            merged_clarifications[key] = answer.answer
        prior_state["clarifications"] = merged_clarifications
        answered_questions = state.answered_questions + request.answers
        clarification_rounds = state.clarification_rounds + 1
        return self._run_pipeline(
            session_id=state.session_id,
            narrative=state.narrative,
            prior_state=prior_state,
            answered_questions=answered_questions,
            clarification_rounds=clarification_rounds,
        )

    def get_session(self, session_id: str) -> SessionState:
        if not self.repo.has_state(session_id):
            raise ValueError("Session not found")
        return self.repo.load_state(session_id)

    def run(self, request: StartSessionRequest) -> PipelineResponse:
        return self.start_session(request)

    def _run_pipeline(
        self,
        session_id: str,
        narrative: str,
        prior_state: dict,
        answered_questions: list[ClarificationAnswer],
        clarification_rounds: int,
    ) -> PipelineResponse:
        enriched_narrative = self._build_enriched_narrative(narrative, prior_state)
        diagnosis = self.diagnosis_service.validate(self.prompts.run_intake_diagnosis(enriched_narrative, prior_state))
        self.repo.save_stage(session_id, "01_intake_diagnosis", diagnosis)

        problem_spec = self.formalization_service.validate(self.prompts.run_formalization(diagnosis))
        self.repo.save_stage(session_id, "02_problem_spec", problem_spec)

        artifacts = PipelineArtifacts(intake_diagnosis=diagnosis, problem_spec=problem_spec)

        if self.clarification_service.should_ask_questions(diagnosis, problem_spec, clarification_rounds):
            questions = self.clarification_service.build_questions(diagnosis, problem_spec)
            state = SessionState(
                session_id=session_id,
                narrative=narrative,
                prior_state=prior_state,
                status="needs_clarification",
                clarification_rounds=clarification_rounds,
                pending_questions=questions,
                answered_questions=answered_questions,
                artifacts=artifacts,
            )
            self.repo.save_state(state)
            return PipelineResponse(
                session_id=session_id,
                status="needs_clarification",
                artifacts=artifacts,
                pending_questions=questions,
                clarification_rounds=clarification_rounds,
            )

        pre_check = self.governance_service.pre_check(problem_spec)
        self.repo.save_stage(session_id, "03_governance_precheck", pre_check)
        if pre_check.decision == "veto":
            summary = self.explanation_service.build_summary(problem_spec, None, pre_check)
            recommendation = self.prompts.run_explanation(
                summary,
                None,
                [],
                pre_check.reasons,
                pre_check.required_safeguards,
                ["Clarify a narrower operational problem"],
                problem_spec.assumptions,
                problem_spec.missing_fields,
            )
            self.repo.save_stage(session_id, "06_recommendation", recommendation)
            artifacts = PipelineArtifacts(
                intake_diagnosis=diagnosis,
                problem_spec=problem_spec,
                governance=pre_check,
                recommendation=recommendation,
            )
            state = SessionState(
                session_id=session_id,
                narrative=narrative,
                prior_state=prior_state,
                status="vetoed",
                clarification_rounds=clarification_rounds,
                pending_questions=[],
                answered_questions=answered_questions,
                artifacts=artifacts,
            )
            self.repo.save_state(state)
            return PipelineResponse(
                session_id=session_id,
                status="vetoed",
                artifacts=artifacts,
                clarification_rounds=clarification_rounds,
            )

        research = self.research_broker.run_research(problem_spec)
        self.repo.save_stage(session_id, "04_research", research)

        ranking = self.ranking_service.rank_methods(problem_spec, research.evidence_cards)
        self.repo.save_stage(session_id, "05_ranking", ranking)

        governance = self.governance_service.final_check(problem_spec, ranking)
        self.repo.save_stage(session_id, "06_governance_final", governance)

        summary = self.explanation_service.build_summary(problem_spec, ranking, governance)
        recommendation = self.prompts.run_explanation(
            summary,
            ranking.ranked_methods[0].method_family if ranking.ranked_methods else None,
            [item.method_family for item in ranking.ranked_methods[1:3]],
            governance.reasons,
            governance.required_safeguards,
            ["Validate with stakeholders", "Pilot the baseline first", "Instrument monitoring before rollout"],
            problem_spec.assumptions,
            problem_spec.missing_fields,
        )
        self.repo.save_stage(session_id, "07_recommendation", recommendation)

        artifacts = PipelineArtifacts(
            intake_diagnosis=diagnosis,
            problem_spec=problem_spec,
            research=research,
            ranking=ranking,
            governance=governance,
            recommendation=recommendation,
        )
        state = SessionState(
            session_id=session_id,
            narrative=narrative,
            prior_state=prior_state,
            status="completed",
            clarification_rounds=clarification_rounds,
            pending_questions=[],
            answered_questions=answered_questions,
            artifacts=artifacts,
        )
        self.repo.save_state(state)
        return PipelineResponse(
            session_id=session_id,
            status="completed",
            artifacts=artifacts,
            clarification_rounds=clarification_rounds,
        )

    def _build_enriched_narrative(self, narrative: str, prior_state: dict) -> str:
        clarifications = prior_state.get("clarifications", {})
        if not clarifications:
            return narrative
        lines = [narrative, "", "Clarifications:"]
        for key, value in clarifications.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)
