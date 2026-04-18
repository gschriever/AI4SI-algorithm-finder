from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, TypeVar

import anthropic
import google.generativeai as genai
from google.api_core import exceptions
import httpx
import openai
from pydantic import BaseModel

from adapters.prompt_library import PromptLibrary
from config import settings
from models.governance import RecommendationPackage
from models.method_card import Citation, MethodEvidenceCard, RankedMethod, RankedMethods, ResearchEvidenceResult
from models.session import IntakeDiagnosisResult
from models.problem_spec import (
    ActionSpace,
    ConfidenceMissingInformation,
    Constraint,
    DecisionVariable,
    EvaluationMetric,
    FairnessConstraint,
    GovernanceNotes,
    HumanReviewRequirement,
    InterventionCostCapacity,
    ObjectiveFunction,
    OptimisabilityStatus,
    ProblemSpec,
    ProblemType,
    RequiredData,
    TargetVariable,
    TimeHorizon,
    UncertaintyStructure,
)

ModelT = TypeVar("ModelT", bound=BaseModel)

logger = logging.getLogger(__name__)

class PromptExecutor:
    def __init__(self) -> None:
        self._timeout = settings.llm_timeout_seconds
        self._prompt_library = PromptLibrary()
        
        # Initialize Gemini
        if settings.llm_api_key:
            genai.configure(api_key=settings.llm_api_key)
        
        # Initialize Anthropic
        self._anthropic_client = None
        if settings.anthropic_api_key:
            self._anthropic_client = anthropic.Anthropic(
                api_key=settings.anthropic_api_key,
                timeout=120.0
            )
        
        # Initialize OpenAI
        self._openai_client = None
        if settings.openai_api_key:
            self._openai_client = openai.OpenAI(api_key=settings.openai_api_key)

    def _should_call_llm(self) -> bool:
        if settings.llm_provider == "fixture":
            return False
        
        if settings.llm_provider == "anthropic":
            return bool(settings.anthropic_api_key)
        if settings.llm_provider == "openai":
            return bool(settings.openai_api_key)
        return bool(settings.llm_api_key)

    def run_intake_diagnosis(self, narrative: str, prior_state: dict | None = None) -> IntakeDiagnosisResult:
        if not self._should_call_llm():
            return self._fixture_intake_diagnosis(narrative, prior_state)
        system_prompt = self._prompt_library.get("intake_diagnosis")
        user_prompt = json.dumps({"narrative": narrative, "prior_state": prior_state or {}}, indent=2)
        return self._call_json_model(system_prompt, user_prompt, IntakeDiagnosisResult)

    def run_formalization(self, diagnosis: IntakeDiagnosisResult) -> ProblemSpec:
        if not self._should_call_llm():
            return self._fixture_formalization(diagnosis)
        system_prompt = self._prompt_library.get("problem_formalizer")
        user_prompt = diagnosis.model_dump_json(indent=2)
        return self._call_json_model(system_prompt, user_prompt, ProblemSpec)

    def run_research_evidence(self, problem_spec: ProblemSpec, search_queries: list[str], retrieved_sources: list[dict[str, Any]]) -> ResearchEvidenceResult:
        if not self._should_call_llm():
            return self._fixture_research_evidence(problem_spec, search_queries, retrieved_sources)
        system_prompt = self._prompt_library.get("research_evidence")
        user_prompt = json.dumps(
            {
                "problem_spec": problem_spec.model_dump(mode="json"),
                "search_queries": search_queries,
                "retrieved_sources": retrieved_sources,
            },
            indent=2,
        )
        return self._call_json_model(system_prompt, user_prompt, ResearchEvidenceResult)

    def run_ranking(self, problem_spec: ProblemSpec, evidence_cards: list[MethodEvidenceCard]) -> RankedMethods:
        if not self._should_call_llm():
            return self._fixture_ranking(problem_spec, evidence_cards)
        system_prompt = self._prompt_library.get("method_ranking")
        user_prompt = json.dumps(
            {
                "problem_spec": problem_spec.model_dump(mode="json"),
                "evidence_cards": [card.model_dump(mode="json") for card in evidence_cards],
            },
            indent=2,
        )
        result = self._call_json_model(system_prompt, user_prompt, RankedMethods)
        return self._normalize_ranking_result(result, evidence_cards)

    def run_explanation(
        self,
        summary: str,
        recommended_method: str | None,
        alternatives: list[str],
        risks: list[str],
        safeguards: list[str],
        next_steps: list[str],
        assumptions: list[str],
        missing_fields: list[str],
    ) -> RecommendationPackage:
        if not self._should_call_llm():
            return self._fixture_explanation(summary, recommended_method, alternatives, risks, safeguards, next_steps, assumptions, missing_fields)
        system_prompt = self._prompt_library.get("explanation")
        user_prompt = json.dumps(
            {
                "summary": summary,
                "recommended_method_family": recommended_method,
                "alternatives_considered": alternatives,
                "risks": risks,
                "safeguards": safeguards,
                "next_steps": next_steps,
                "assumptions": assumptions,
                "missing_fields": missing_fields,
            },
            indent=2,
        )
        return self._call_json_model(system_prompt, user_prompt, RecommendationPackage)

    def _call_json_model(self, system_prompt: str, user_prompt: str, model_type: type[ModelT]) -> ModelT:
        provider = settings.llm_provider.lower()
        
        if provider == "anthropic" and self._anthropic_client:
            return self._call_anthropic(system_prompt, user_prompt, model_type)
        if provider == "openai" and self._openai_client:
            return self._call_openai(system_prompt, user_prompt, model_type)
        return self._call_gemini(system_prompt, user_prompt, model_type)

    def _call_gemini(self, system_prompt: str, user_prompt: str, model_type: type[ModelT]) -> ModelT:
        model_name = settings.llm_model if "gemini" in settings.llm_model else "gemini-1.5-flash"
        model = genai.GenerativeModel(model_name=model_name, system_instruction=system_prompt)
        
        max_retries = 5
        base_delay = 2.0
        for i in range(max_retries):
            try:
                config = genai.types.GenerationConfig(temperature=0.2, response_mime_type="application/json")
                response = model.generate_content(user_prompt, generation_config=config)
                return model_type.model_validate_json(response.text)
            except exceptions.ResourceExhausted:
                if i < max_retries - 1:
                    time.sleep(base_delay * (2**i))
                    continue
                raise
            except Exception as e:
                if i < max_retries-1:
                    time.sleep(base_delay * (2**i))
                    continue
                raise
        raise RuntimeError("Max retries exceeded for Gemini")

    def _call_anthropic(self, system_prompt: str, user_prompt: str, model_type: type[ModelT]) -> ModelT:
        max_retries = 5
        base_delay = 2.0
        
        # Force JSON for Claude
        json_instr = "\n\nCRITICAL: Respond ONLY with valid JSON. Do not include markdown fences or explanation."
        
        for i in range(max_retries):
            try:
                response = self._anthropic_client.messages.create(
                    model=settings.llm_model,
                    max_tokens=4096,
                    temperature=0.2,
                    system=system_prompt + json_instr,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                content = response.content[0].text.strip()
                
                # Robust JSON extraction
                json_str = content
                if "```json" in content:
                    match = re.search(r"```json\s*\n?(.*?)\n?```", content, re.DOTALL)
                    if match:
                        json_str = match.group(1).strip()
                elif "```" in content:
                    match = re.search(r"```\s*\n?(.*?)\n?```", content, re.DOTALL)
                    if match:
                        json_str = match.group(1).strip()
                else:
                    # Fallback: Find anything between first '{' and last '}'
                    match = re.search(r"(\{.*\})", content, re.DOTALL)
                    if match:
                        json_str = match.group(1).strip()

                return model_type.model_validate_json(json_str)
            except anthropic.RateLimitError:
                if i < max_retries - 1:
                    time.sleep(base_delay * (2**i))
                    continue
                raise
            except Exception:
                if i < max_retries - 1:
                    time.sleep(base_delay * (2**i))
                    continue
                raise
        raise RuntimeError("Max retries exceeded for Anthropic")

    def _call_openai(self, system_prompt: str, user_prompt: str, model_type: type[ModelT]) -> ModelT:
        max_retries = 3
        base_delay = 2.0
        
        for i in range(max_retries):
            try:
                response = self._openai_client.chat.completions.create(
                    model=settings.llm_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
                return model_type.model_validate_json(response.choices[0].message.content)
            except openai.RateLimitError:
                if i < max_retries - 1:
                    time.sleep(base_delay * (2**i))
                    continue
                raise
            except Exception:
                if i < max_retries - 1:
                    time.sleep(base_delay * (2**i))
                    continue
                raise
        raise RuntimeError("Max retries exceeded for OpenAI")

    def _build_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        prefix = settings.llm_api_key_prefix.strip()
        if settings.llm_api_key:
            headers[settings.llm_api_key_header] = f"{prefix} {settings.llm_api_key}".strip() if prefix else settings.llm_api_key
        extra_headers = json.loads(settings.llm_extra_headers_json or "{}")
        for key, value in extra_headers.items():
            headers[str(key)] = str(value)
        return headers

    def _extract_content(self, response_json: dict[str, Any]) -> str:
        try:
            return response_json["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("LLM response did not match expected OpenAI-compatible chat completions shape") from exc

    def _fixture_intake_diagnosis(self, narrative: str, prior_state: dict | None = None) -> IntakeDiagnosisResult:
        clarifications = self._normalized_clarifications(prior_state)
        assumptions = [f"{field}: {value}" for field, value in clarifications.items()]
        text = narrative.lower()
        if any(word in text for word in ["mentor", "match", "assign"]):
            missing = [] if clarifications.get("utility scoring weights") else ["utility scoring weights"]
            return IntakeDiagnosisResult(
                social_goal="Improve beneficiary support outcomes",
                decision_to_be_made="Which beneficiary should be paired with which mentor",
                action_under_consideration="Assign beneficiaries to mentors under capacity limits",
                target_of_interest="match quality and fair access",
                key_constraints=["mentor capacity", "compatibility constraints"],
                optimisability_status="optimisable",
                candidate_optimisation_subproblem="Beneficiary matching under capacity and compatibility constraints",
                rationale=["Clear assignment decision", "Explicit operational constraints"],
                archetype_hypotheses=["matching"],
                missing_information=missing,
                confidence="high",
                assumptions=assumptions,
            )
        if any(word in text for word in ["forecast", "demand", "inventory", "delivery"]):
            missing = [] if clarifications.get("service floor policy") else ["service floor policy"]
            return IntakeDiagnosisResult(
                social_goal="Meet service demand reliably",
                decision_to_be_made="How much to deliver and where",
                action_under_consideration="Forecast demand and allocate deliveries",
                target_of_interest="weekly demand and shortage reduction",
                key_constraints=["vehicle capacity", "storage limits"],
                optimisability_status="optimisable",
                candidate_optimisation_subproblem="Forecast demand and optimise constrained delivery planning",
                rationale=["Demand signal drives planning", "Operational constraints are explicit"],
                archetype_hypotheses=["forecasting", "allocation"],
                missing_information=missing,
                confidence="medium",
                assumptions=assumptions,
            )
        if any(word in text for word in ["risk", "eviction", "triage", "priorit"]):
            missing = []
            if not clarifications.get("label quality"):
                missing.append("label quality")
            if not clarifications.get("intervention effect"):
                missing.append("intervention effect")
            return IntakeDiagnosisResult(
                social_goal="Target limited support to households most likely to need it",
                decision_to_be_made="Who should receive outreach first",
                action_under_consideration="Rank cases for intervention under capacity limits",
                target_of_interest="risk of adverse outcome",
                key_constraints=["weekly outreach capacity", "fairness constraints"],
                optimisability_status="partially_optimisable",
                candidate_optimisation_subproblem="Prioritise limited outreach capacity using risk-informed ranking",
                rationale=["A narrow operational prioritisation problem exists", "The broader social problem is not fully optimisable"],
                archetype_hypotheses=["prediction"],
                missing_information=missing,
                confidence="medium",
                assumptions=assumptions,
            )
        missing = []
        if not clarifications.get("decision variable"):
            missing.append("decision variable")
        if not clarifications.get("objective function"):
            missing.append("objective function")
        if not clarifications.get("constraints"):
            missing.append("constraints")
        candidate_subproblem = clarifications.get("narrower operational decision", "")
        status = "not_optimisable" if missing else "partially_optimisable"
        rationale = ["No clear controllable action or measurable objective was identified"] if missing else ["A narrower operational decision was supplied through clarification"]
        return IntakeDiagnosisResult(
            social_goal="Address a broad social problem",
            decision_to_be_made=clarifications.get("decision variable", "Unclear"),
            action_under_consideration=clarifications.get("narrower operational decision", "Unclear"),
            target_of_interest=clarifications.get("objective function", "Unclear"),
            key_constraints=[clarifications["constraints"]] if clarifications.get("constraints") else [],
            optimisability_status=status,
            candidate_optimisation_subproblem=candidate_subproblem,
            rationale=rationale,
            archetype_hypotheses=["mixed"] if candidate_subproblem else [],
            missing_information=missing,
            confidence="low" if missing else "medium",
            assumptions=assumptions,
        )

    def _fixture_formalization(self, diagnosis: IntakeDiagnosisResult) -> ProblemSpec:
        archetype = diagnosis.archetype_hypotheses[0] if diagnosis.archetype_hypotheses else "prediction"
        if archetype == "matching":
            return ProblemSpec(
                problem_summary=diagnosis.candidate_optimisation_subproblem,
                optimisability_status=OptimisabilityStatus.OPTIMISABLE,
                optimisability_rationale=diagnosis.rationale,
                problem_type=ProblemType.MATCHING,
                optimisation_subproblem=diagnosis.candidate_optimisation_subproblem,
                decision_variable=DecisionVariable(name="assignment", type="assignment"),
                action_space=ActionSpace(description="Assign beneficiaries to mentors", size="combinatorial", feasibility_rules=diagnosis.key_constraints),
                target_variable=TargetVariable(name="match_quality", type="utility_score", label_quality="medium"),
                objective_function=ObjectiveFunction(primary_objective="Maximise match quality with fair access", direction="maximize"),
                constraints=[Constraint(name="capacity", type="hard", description="Mentor capacity")],
                fairness_harm_constraints=[FairnessConstraint(name="access_floor", description="Avoid excluding language minorities", protected_or_impacted_group="underserved groups", constraint_type="allocation_floor")],
                time_horizon=TimeHorizon(decision_frequency="monthly", planning_horizon="6 months"),
                uncertainty_structure=UncertaintyStructure(environment_stability="stable", aleatoric_uncertainty="medium", distribution_shift_risk="low", counterfactual_uncertainty="not_applicable"),
                required_data=[RequiredData(name="beneficiary profiles", type="tabular", availability="available", quality="medium")],
                feedback_loop_type="resource_allocation",
                intervention_cost_capacity_assumptions=InterventionCostCapacity(capacity_constraints=["mentor caseload"]),
                evaluation_metric=[EvaluationMetric(name="match_quality", type="optimisation"), EvaluationMetric(name="unmatched_rate_by_group", type="fairness")],
                baseline_options=["rules_based", "manual_triage", "optimisation_solver"],
                human_in_the_loop_requirements=[HumanReviewRequirement(stage="approval", requirement="Coordinator can override assignments")],
                governance_notes=GovernanceNotes(high_stakes=False, automation_recommendation="human_approval_required"),
                confidence_missing_information=ConfidenceMissingInformation(overall_confidence="high", critical_unknowns=diagnosis.missing_information, assumptions_made=diagnosis.assumptions),
                assumptions=diagnosis.assumptions,
                missing_fields=diagnosis.missing_information,
            )
        if archetype == "forecasting":
            return ProblemSpec(
                problem_summary=diagnosis.candidate_optimisation_subproblem,
                optimisability_status=OptimisabilityStatus.OPTIMISABLE,
                optimisability_rationale=diagnosis.rationale,
                problem_type=ProblemType.FORECASTING,
                optimisation_subproblem=diagnosis.candidate_optimisation_subproblem,
                decision_variable=DecisionVariable(name="delivery_plan", type="route"),
                action_space=ActionSpace(description="Allocate deliveries by site", size="combinatorial", feasibility_rules=diagnosis.key_constraints),
                target_variable=TargetVariable(name="weekly_demand", type="forecast_quantity", label_quality="medium"),
                objective_function=ObjectiveFunction(primary_objective="Minimise shortage and waste", direction="minimize"),
                constraints=[Constraint(name="vehicle_capacity", type="hard", description="Vehicle capacity limit")],
                fairness_harm_constraints=[FairnessConstraint(name="service_floor", description="Minimum service level for underserved areas", protected_or_impacted_group="underserved neighbourhoods", constraint_type="allocation_floor")],
                time_horizon=TimeHorizon(decision_frequency="weekly", planning_horizon="8 weeks"),
                uncertainty_structure=UncertaintyStructure(environment_stability="moderately_variable", aleatoric_uncertainty="high", distribution_shift_risk="medium", counterfactual_uncertainty="not_applicable"),
                required_data=[RequiredData(name="historical demand", type="time_series", availability="available", quality="medium")],
                feedback_loop_type="resource_allocation",
                intervention_cost_capacity_assumptions=InterventionCostCapacity(capacity_constraints=["fleet size", "storage"]),
                evaluation_metric=[EvaluationMetric(name="weighted_shortage_rate", type="user_outcome")],
                baseline_options=["dashboard_only", "simple_scoring", "optimisation_solver"],
                human_in_the_loop_requirements=[HumanReviewRequirement(stage="approval", requirement="Operations manager reviews weekly plan")],
                governance_notes=GovernanceNotes(high_stakes=True, automation_recommendation="human_approval_required"),
                confidence_missing_information=ConfidenceMissingInformation(overall_confidence="medium", critical_unknowns=diagnosis.missing_information, assumptions_made=diagnosis.assumptions),
                assumptions=diagnosis.assumptions,
                missing_fields=diagnosis.missing_information,
            )
        if diagnosis.optimisability_status == "not_optimisable":
            return ProblemSpec(
                problem_summary="Problem is not yet optimisable",
                optimisability_status=OptimisabilityStatus.NOT_OPTIMISABLE,
                optimisability_rationale=diagnosis.rationale,
                problem_type=ProblemType.MIXED,
                optimisation_subproblem="Clarify a narrower operational problem before proceeding",
                decision_variable=DecisionVariable(name="undefined", type="none"),
                action_space=ActionSpace(description="No valid action space yet", size="small"),
                target_variable=TargetVariable(name="undefined", type="proxy_label"),
                objective_function=ObjectiveFunction(primary_objective="Do not optimise yet", direction="satisfy"),
                time_horizon=TimeHorizon(decision_frequency="one_off"),
                uncertainty_structure=UncertaintyStructure(environment_stability="unstable", aleatoric_uncertainty="high", distribution_shift_risk="high", counterfactual_uncertainty="high"),
                feedback_loop_type="none",
                confidence_missing_information=ConfidenceMissingInformation(overall_confidence="low", critical_unknowns=diagnosis.missing_information, assumptions_made=diagnosis.assumptions),
                assumptions=diagnosis.assumptions,
                missing_fields=diagnosis.missing_information,
            )
        return ProblemSpec(
            problem_summary=diagnosis.candidate_optimisation_subproblem,
            optimisability_status=OptimisabilityStatus.PARTIALLY_OPTIMISABLE,
            optimisability_rationale=diagnosis.rationale,
            problem_type=ProblemType.PREDICTION,
            optimisation_subproblem=diagnosis.candidate_optimisation_subproblem,
            decision_variable=DecisionVariable(name="priority_rank", type="assignment"),
            action_space=ActionSpace(description="Select cases for intervention", size="large", feasibility_rules=diagnosis.key_constraints),
            target_variable=TargetVariable(name="risk_outcome", type="proxy_label", label_quality="medium", proxy_risk_notes=["Outcome labels may be incomplete or biased"]),
            objective_function=ObjectiveFunction(primary_objective="Improve targeting of limited interventions", direction="maximize"),
            constraints=[Constraint(name="capacity", type="hard", description="Intervention capacity")],
            fairness_harm_constraints=[FairnessConstraint(name="equal_error_review", description="Review subgroup error disparities", protected_or_impacted_group="protected groups", constraint_type="equal_error")],
            time_horizon=TimeHorizon(decision_frequency="weekly", planning_horizon="12 weeks"),
            uncertainty_structure=UncertaintyStructure(environment_stability="moderately_variable", aleatoric_uncertainty="medium", distribution_shift_risk="high", counterfactual_uncertainty="high"),
            required_data=[RequiredData(name="case history", type="administrative", availability="partial", quality="medium")],
            feedback_loop_type="prediction_to_intervention",
            intervention_cost_capacity_assumptions=InterventionCostCapacity(capacity_constraints=["weekly outreach capacity"]),
            evaluation_metric=[EvaluationMetric(name="precision_at_k", type="predictive")],
            baseline_options=["rules_based", "manual_triage", "simple_scoring"],
            human_in_the_loop_requirements=[HumanReviewRequirement(stage="recommendation_review", requirement="Case worker reviews ranked list")],
            governance_notes=GovernanceNotes(high_stakes=True, automation_recommendation="decision_support_only"),
            confidence_missing_information=ConfidenceMissingInformation(overall_confidence="medium", critical_unknowns=diagnosis.missing_information, assumptions_made=diagnosis.assumptions),
            assumptions=diagnosis.assumptions,
            missing_fields=diagnosis.missing_information,
        )

    def _fixture_ranking(self, problem_spec: ProblemSpec, evidence_cards: list[MethodEvidenceCard]) -> RankedMethods:
        ranked: list[RankedMethod] = []
        supporting = self._fixture_supporting_methods(problem_spec)
        for card in evidence_cards:
            scores = self._fixture_dimension_scores(problem_spec, card)
            weighted = round(sum(scores.values()) / len(scores), 3)
            ranked.append(
                RankedMethod(
                    method_family=card.method_family,
                    weighted_score=weighted,
                    dimension_scores=scores,
                    rationale=self._fixture_rationale(problem_spec, card, scores),
                    rejected=weighted < 2.0,
                    rejection_reason="Poor overall fit for the current problem formulation." if weighted < 2.0 else None,
                    baseline=card.baseline,
                )
            )
        ranked.sort(key=lambda item: item.weighted_score, reverse=True)
        return RankedMethods(ranked_methods=ranked, supporting_methods=supporting)

    def _fixture_dimension_scores(self, problem_spec: ProblemSpec, card: MethodEvidenceCard) -> dict[str, float]:
        structural_fit = 5.0 if problem_spec.problem_type.value in card.archetypes_supported else 3.0
        if problem_spec.problem_type == ProblemType.MATCHING and "integer" in card.method_family:
            structural_fit = 5.0
        if problem_spec.problem_type == ProblemType.FORECASTING and "deep" in card.method_family:
            structural_fit = 2.0
        return {
            "structural_fit": structural_fit,
            "constraint_handling": 5.0 if card.constraint_support == "native" else 3.0 if card.constraint_support == "external solver" else 2.0,
            "data_fit": 2.0 if any("large" in req for req in card.data_requirements) else 4.0,
            "interpretability": 5.0 if card.interpretability == "high" else 3.0 if card.interpretability == "medium" else 1.5,
            "robustness": 4.0 if card.confidence == "high" else 2.5,
            "fairness": 4.0 if any("fair" in item.lower() or "floor" in item.lower() for item in card.fairness_implications) else 3.0,
            "implementation_complexity": 4.5 if card.implementation_burden == "low" else 3.0 if card.implementation_burden == "medium" else 1.5,
            "monitoring_burden": 4.0 if card.interpretability == "high" else 2.5,
        }

    def _fixture_rationale(self, problem_spec: ProblemSpec, card: MethodEvidenceCard, scores: dict[str, float]) -> list[str]:
        rationale = [
            f"Overall structural fit for {problem_spec.problem_type.value}: {scores['structural_fit']}",
            f"Constraint handling score: {scores['constraint_handling']}",
        ]
        rationale.extend(card.failure_modes[:1])
        return rationale

    def _fixture_supporting_methods(self, problem_spec: ProblemSpec) -> list[str]:
        if problem_spec.problem_type == ProblemType.MATCHING:
            return ["scenario_analysis", "human_override_workflow"]
        if problem_spec.problem_type == ProblemType.FORECASTING:
            return ["uncertainty_intervals", "scenario_planning", "drift_monitoring"]
        return ["calibration", "threshold_analysis", "fairness_audit"]

    def _normalize_ranking_result(self, result: RankedMethods, evidence_cards: list[MethodEvidenceCard]) -> RankedMethods:
        card_lookup = {card.method_family: card for card in evidence_cards}
        normalized_methods: list[RankedMethod] = []
        for item in result.ranked_methods:
            card = card_lookup.get(item.method_family)
            if card is None:
                continue
            normalized_methods.append(
                RankedMethod(
                    method_family=item.method_family,
                    weighted_score=item.weighted_score,
                    dimension_scores=item.dimension_scores,
                    rationale=item.rationale,
                    rejected=item.rejected,
                    rejection_reason=item.rejection_reason,
                    baseline=card.baseline,
                )
            )
        existing = {item.method_family for item in normalized_methods}
        for card in evidence_cards:
            if card.method_family not in existing:
                normalized_methods.append(
                    RankedMethod(
                        method_family=card.method_family,
                        weighted_score=1.0,
                        dimension_scores={
                            "structural_fit": 1.0,
                            "constraint_handling": 1.0,
                            "data_fit": 1.0,
                            "interpretability": 1.0,
                            "robustness": 1.0,
                            "fairness": 1.0,
                            "implementation_complexity": 1.0,
                            "monitoring_burden": 1.0,
                        },
                        rationale=["The ranking model did not score this candidate, so it was retained at the bottom for completeness."],
                        rejected=True,
                        rejection_reason="Candidate omitted by ranking model output.",
                        baseline=card.baseline,
                    )
                )
        normalized_methods.sort(key=lambda item: item.weighted_score, reverse=True)
        return RankedMethods(
            ranked_methods=normalized_methods,
            supporting_methods=result.supporting_methods,
            assumptions=result.assumptions,
            missing_fields=result.missing_fields,
        )

    def _fixture_research_evidence(
        self,
        problem_spec: ProblemSpec,
        search_queries: list[str],
        retrieved_sources: list[dict[str, Any]],
    ) -> ResearchEvidenceResult:
        citations = [self._citation_from_source(source, index) for index, source in enumerate(retrieved_sources, start=1)]
        citations = [citation for citation in citations if citation is not None]
        if not citations:
            return ResearchEvidenceResult(
                search_queries=search_queries,
                candidate_method_families=[],
                evidence_cards=[],
                assumptions=["No retrieved sources were available for heuristic evidence extraction."],
                missing_fields=["live research evidence"],
            )
        if problem_spec.problem_type == ProblemType.MATCHING:
            cards = [
                MethodEvidenceCard(
                    method_family="integer_programming",
                    archetypes_supported=["matching"],
                    assumptions=["A reliable utility or compatibility score can be constructed."],
                    data_requirements=["beneficiary and mentor features"],
                    constraint_support="native",
                    fairness_implications=["Can encode allocation floors and explicit fairness constraints."],
                    implementation_burden="medium",
                    interpretability="high",
                    failure_modes=["Poor utility design can produce poor matches."],
                    confidence="medium",
                    citations=citations[:2] or citations,
                ),
                MethodEvidenceCard(
                    method_family="rules_based_scoring",
                    archetypes_supported=["matching"],
                    assumptions=["Simple compatibility heuristics are operationally acceptable."],
                    data_requirements=["basic profile fields"],
                    constraint_support="approximate",
                    fairness_implications=["Requires review of subjective rule choices."],
                    implementation_burden="low",
                    interpretability="high",
                    failure_modes=["May miss globally feasible high-quality assignments."],
                    baseline=True,
                    non_ml_alternative=True,
                    confidence="medium",
                    citations=citations[:1],
                ),
            ]
        elif problem_spec.problem_type == ProblemType.FORECASTING:
            cards = [
                MethodEvidenceCard(
                    method_family="time_series_forecasting",
                    archetypes_supported=["forecasting"],
                    assumptions=["Historical demand is informative for near-term planning."],
                    data_requirements=["historical demand time series"],
                    constraint_support="external solver",
                    fairness_implications=["Needs explicit downstream fairness and service-floor checks."],
                    implementation_burden="medium",
                    interpretability="medium",
                    failure_modes=["Past shortages may distort observed demand."],
                    confidence="medium",
                    citations=citations[:2] or citations,
                ),
                MethodEvidenceCard(
                    method_family="linear_programming",
                    archetypes_supported=["allocation"],
                    assumptions=["Capacity and service objectives can be formalised."],
                    data_requirements=["forecast outputs and operational constraints"],
                    constraint_support="native",
                    fairness_implications=["Can encode explicit service floors."],
                    implementation_burden="medium",
                    interpretability="high",
                    failure_modes=["Bad objective design can skew allocation."],
                    baseline=True,
                    non_ml_alternative=True,
                    confidence="medium",
                    citations=citations[:1],
                ),
            ]
        else:
            cards = [
                MethodEvidenceCard(
                    method_family="logistic_regression",
                    archetypes_supported=["prediction"],
                    assumptions=["Predictive signal exists in the available case-level data."],
                    data_requirements=["case-level historical data"],
                    constraint_support="external thresholding",
                    fairness_implications=["Requires calibration and subgroup review."],
                    implementation_burden="low",
                    interpretability="high",
                    failure_modes=["Can optimize a biased proxy target."],
                    baseline=True,
                    confidence="medium",
                    citations=citations[:2] or citations,
                ),
                MethodEvidenceCard(
                    method_family="manual_triage",
                    archetypes_supported=["prediction"],
                    assumptions=["Manual rules remain operationally viable."],
                    data_requirements=["basic administrative fields"],
                    constraint_support="manual",
                    fairness_implications=["Human inconsistency can introduce bias."],
                    implementation_burden="low",
                    interpretability="high",
                    failure_modes=["Manual review may not scale consistently."],
                    baseline=True,
                    non_ml_alternative=True,
                    confidence="medium",
                    citations=citations[:1],
                ),
            ]
        return ResearchEvidenceResult(
            search_queries=search_queries,
            candidate_method_families=[card.method_family for card in cards],
            evidence_cards=cards,
            assumptions=["Heuristic evidence extraction was used because live LLM research extraction was unavailable."],
        )

    def _citation_from_source(self, source: dict[str, Any], index: int) -> Citation | None:
        url = str(source.get("url", "")).strip()
        title = str(source.get("title", "")).strip()
        if not url or not title:
            return None
        source_id = str(source.get("source_id") or f"retrieved-{index}")
        source_type = str(source.get("source_type") or "web")
        return Citation(source_id=source_id, url=url, title=title, source_type=source_type)

    def _fixture_explanation(
        self,
        summary: str,
        recommended_method: str | None,
        alternatives: list[str],
        risks: list[str],
        safeguards: list[str],
        next_steps: list[str],
        assumptions: list[str],
        missing_fields: list[str],
    ) -> RecommendationPackage:
        return RecommendationPackage(
            summary=summary,
            recommended_method_family=recommended_method,
            alternatives_considered=alternatives,
            risks=risks,
            safeguards=safeguards,
            next_steps=next_steps,
            assumptions=assumptions,
            missing_fields=missing_fields,
        )

    def _normalized_clarifications(self, prior_state: dict | None) -> dict[str, str]:
        clarifications = (prior_state or {}).get("clarifications", {})
        return {str(key).strip().lower(): str(value).strip() for key, value in clarifications.items() if str(value).strip()}
