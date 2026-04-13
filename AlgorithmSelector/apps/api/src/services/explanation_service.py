from __future__ import annotations

from models.governance import GovernanceDecision, RecommendationPackage
from models.method_card import RankedMethods
from models.problem_spec import ProblemSpec


class ExplanationService:
    def build_summary(self, problem_spec: ProblemSpec, ranking: RankedMethods | None, governance: GovernanceDecision) -> str:
        if governance.decision == "veto":
            return f"Do not optimise yet. {problem_spec.optimisability_rationale[0] if problem_spec.optimisability_rationale else ''}".strip()
        top = ranking.ranked_methods[0].method_family if ranking and ranking.ranked_methods else None
        return f"Recommended family: {top}. This fits because the problem is structured as {problem_spec.problem_type.value} with explicit constraints and governance safeguards."

    def build_package(self, summary: str, ranking: RankedMethods | None, governance: GovernanceDecision, problem_spec: ProblemSpec) -> RecommendationPackage:
        top = ranking.ranked_methods[0].method_family if ranking and ranking.ranked_methods else None
        alternatives = [item.method_family for item in ranking.ranked_methods[1:3]] if ranking else []
        risks = governance.reasons + problem_spec.confidence_missing_information.critical_unknowns
        next_steps = ["Validate the formal problem spec with stakeholders", "Review baseline method performance", "Run governance review before any deployment"]
        return RecommendationPackage(summary=summary, recommended_method_family=top, alternatives_considered=alternatives, risks=risks, safeguards=governance.required_safeguards, next_steps=next_steps, assumptions=problem_spec.assumptions, missing_fields=problem_spec.missing_fields)
