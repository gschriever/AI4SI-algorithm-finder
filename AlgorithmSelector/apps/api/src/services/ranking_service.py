from __future__ import annotations

from adapters.prompt_executor import PromptExecutor
from models.method_card import MethodEvidenceCard, RankedMethods
from models.problem_spec import ProblemSpec


class RankingService:
    def __init__(self) -> None:
        self.prompts = PromptExecutor()

    def rank_methods(self, problem_spec: ProblemSpec, evidence_cards: list[MethodEvidenceCard]) -> RankedMethods:
        return self.prompts.run_ranking(problem_spec, evidence_cards)
