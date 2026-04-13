from __future__ import annotations

from models.problem_spec import OptimisabilityStatus, ProblemSpec
from models.session import ClarifyingQuestion, IntakeDiagnosisResult


class ClarificationService:
    def __init__(self, max_rounds: int = 3, max_questions_per_round: int = 3) -> None:
        self.max_rounds = max_rounds
        self.max_questions_per_round = max_questions_per_round

    def should_ask_questions(self, diagnosis: IntakeDiagnosisResult, problem_spec: ProblemSpec, clarification_rounds: int) -> bool:
        if clarification_rounds >= self.max_rounds:
            return False
        return bool(self._collect_missing_fields(diagnosis, problem_spec))

    def build_questions(self, diagnosis: IntakeDiagnosisResult, problem_spec: ProblemSpec) -> list[ClarifyingQuestion]:
        fields = self._collect_missing_fields(diagnosis, problem_spec)[: self.max_questions_per_round]
        return [self._question_for_field(index, field, diagnosis, problem_spec) for index, field in enumerate(fields, start=1)]

    def _collect_missing_fields(self, diagnosis: IntakeDiagnosisResult, problem_spec: ProblemSpec) -> list[str]:
        fields: list[str] = []
        fields.extend(diagnosis.missing_information)
        fields.extend(problem_spec.missing_fields)
        if not problem_spec.constraints:
            fields.append("constraints")
        if not problem_spec.decision_variable.name or problem_spec.decision_variable.name == "undefined":
            fields.append("decision variable")
        if problem_spec.optimisability_status == OptimisabilityStatus.NOT_OPTIMISABLE:
            fields.append("narrower operational decision")
        deduped: list[str] = []
        seen: set[str] = set()
        for field in fields:
            normalized = field.strip().lower()
            if normalized and normalized not in seen:
                seen.add(normalized)
                deduped.append(field)
        return deduped

    def _question_for_field(
        self,
        index: int,
        field: str,
        diagnosis: IntakeDiagnosisResult,
        problem_spec: ProblemSpec,
    ) -> ClarifyingQuestion:
        normalized = field.strip().lower()
        prompts = {
            "decision variable": (
                "What exact decision would the system support or optimize, and who currently makes that decision?",
                "A usable optimization problem requires a controllable decision variable.",
            ),
            "objective function": (
                "What outcome should be improved first, and how would you judge whether the decision was better or worse?",
                "Method choice depends on the primary objective and how success is measured.",
            ),
            "constraints": (
                "What hard constraints must always be respected, such as capacity, policy, eligibility, fairness, or timing rules?",
                "Constraints determine whether the problem is actually operationalizable.",
            ),
            "utility scoring weights": (
                "How should tradeoffs be weighted when comparing options, for example match quality versus fairness or workload balance?",
                "The ranking of feasible actions depends on the utility function or weighting scheme.",
            ),
            "label quality": (
                "How reliable is the outcome label or historical outcome data, and where do you expect it to be incomplete or biased?",
                "Weak labels can make predictive recommendations unsafe or misleading.",
            ),
            "intervention effect": (
                "After a case is prioritized, what intervention is actually available and what evidence suggests it changes outcomes?",
                "Prediction alone is not enough if the intervention pathway is unclear or ineffective.",
            ),
            "service floor policy": (
                "Are there minimum service levels or protected groups that must receive support regardless of forecasted demand?",
                "Those policies affect both feasibility and fairness constraints.",
            ),
            "narrower operational decision": (
                "What narrower recurring operational decision sits inside this broader problem, such as prioritizing cases, allocating resources, or matching people to slots?",
                "The current narrative is still too broad to optimize directly.",
            ),
        }
        question, why_it_matters = prompts.get(
            normalized,
            (
                f"What can you tell me about {field} in concrete operational terms?",
                f"This information is still missing and may change the formal problem specification.",
            ),
        )
        return ClarifyingQuestion(
            question_id=f"q{index}_{normalized.replace(' ', '_').replace('-', '_')}",
            field=field,
            question=question,
            why_it_matters=why_it_matters,
        )
