from __future__ import annotations

from models.governance import GovernanceDecision
from models.method_card import RankedMethods
from models.problem_spec import OptimisabilityStatus, ProblemSpec
from services.policy_loader import PolicyLoader


class GovernanceService:
    def __init__(self) -> None:
        self.rules = PolicyLoader().load("governance_rules.yaml")

    def pre_check(self, problem_spec: ProblemSpec) -> GovernanceDecision:
        reasons: list[str] = []
        if problem_spec.optimisability_status == OptimisabilityStatus.NOT_OPTIMISABLE:
            reasons.append("Problem is not yet optimisable.")
            return GovernanceDecision(decision="veto", reasons=reasons, required_safeguards=["Narrow the problem before optimisation."])
        if problem_spec.governance_notes.high_stakes and not problem_spec.human_in_the_loop_requirements:
            reasons.append("High-stakes cases require human review.")
            return GovernanceDecision(decision="veto", reasons=reasons)
        return GovernanceDecision(decision="proceed", reasons=["Pre-check passed."])

    def final_check(self, problem_spec: ProblemSpec, ranking: RankedMethods) -> GovernanceDecision:
        reasons = []
        safeguards = ["Retain audit logs", "Review subgroup impacts before deployment"]
        decision = "proceed"
        if problem_spec.governance_notes.high_stakes:
            decision = "decision_support_only"
            reasons.append("High-stakes cases default to decision support.")
            safeguards.extend(["Human approval required", "Document override and appeal path"])
        if problem_spec.target_variable.type == "proxy_label" and problem_spec.target_variable.proxy_risk_notes:
            decision = "decision_support_only"
            reasons.append("Proxy-label risk requires conservative use.")
        if not reasons:
            reasons.append("No final governance blockers identified.")
        return GovernanceDecision(
            decision=decision,
            reasons=reasons,
            required_safeguards=safeguards,
            required_reviews=problem_spec.governance_notes.required_approvals,
            monitoring_requirements=["Monitor drift", "Monitor subgroup outcomes"],
        )
