from __future__ import annotations

from models.problem_spec import ProblemSpec


class FormalizationService:
    def validate(self, problem_spec: ProblemSpec) -> ProblemSpec:
        return problem_spec
