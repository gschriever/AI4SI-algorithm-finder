from __future__ import annotations

from models.problem_spec import OptimisabilityStatus
from models.session import IntakeDiagnosisResult


class DiagnosisService:
    def validate(self, result: IntakeDiagnosisResult) -> IntakeDiagnosisResult:
        status = result.optimisability_status
        if status == OptimisabilityStatus.NOT_OPTIMISABLE.value and result.candidate_optimisation_subproblem:
            return result
        if status != OptimisabilityStatus.NOT_OPTIMISABLE.value and not result.candidate_optimisation_subproblem:
            raise ValueError("Optimisable cases must include a candidate optimisation subproblem")
        return result
