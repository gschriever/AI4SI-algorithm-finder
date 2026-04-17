"""Run the current project pipeline over AI4SI paper contexts.

This script uses only the social-problem context from the gold-label file.
It does not pass gold method labels into the project pipeline.

Usage:
    python scripts/run_project_predictions.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
API_SRC = REPO_ROOT / "AlgorithmSelector" / "apps" / "api" / "src"
sys.path.insert(0, str(API_SRC))

from config import settings  # noqa: E402
from eval_split_utils import (  # noqa: E402
    DEFAULT_SPLIT_FILE,
    SPLIT_CHOICES,
    filter_records_by_case_ids,
    load_split_case_ids,
)
from models.session import AnswerClarificationsRequest, ClarificationAnswer, StartSessionRequest  # noqa: E402
from services.coordinator_service import CoordinatorService  # noqa: E402
from storage.session_repo import SessionRepository  # noqa: E402


DEFAULT_GOLD = Path("project_context/gold_method_labels.jsonl")
DEFAULT_OUTPUT = Path("project_context/project_predictions.jsonl")
LLM_PROVIDERS = ("fixture", "openai_compatible")
RESEARCH_MODES = ("fixture", "live")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def answer_for_field(field: str, record: dict[str, Any]) -> str:
    normalized = field.strip().lower()
    social_problem = record.get("social_problem", "")
    defaults = {
        "utility scoring weights": "Use the main social outcome first, then fairness or service coverage, then operational workload.",
        "label quality": "Historical outcome labels are available but noisy, incomplete, and should be checked for subgroup bias.",
        "intervention effect": "A limited intervention is available, and it is expected to improve outcomes when targeted to the right people or places.",
        "service floor policy": "Maintain minimum service levels for underserved or high-need groups even when predicted demand is lower.",
        "decision variable": f"Choose which limited resources, interventions, or actions to assign for this problem: {social_problem}",
        "objective function": "Maximize the target social benefit while minimizing unmet need, wasted resources, and avoidable harm.",
        "constraints": "Respect limited budget, staff capacity, timing, eligibility, fairness, and operational feasibility constraints.",
        "narrower operational decision": f"Prioritize, allocate, or schedule limited resources for the affected population in this setting: {social_problem}",
    }
    return defaults.get(normalized, f"Use the operational detail available in the paper context: {social_problem}")


def run_case(service: CoordinatorService, record: dict[str, Any], max_rounds: int) -> dict[str, Any]:
    case_id = record["case_id"]
    response = service.start_session(
        StartSessionRequest(
            session_id=f"eval_{case_id}",
            narrative=record.get("social_problem", ""),
            prior_state={},
        )
    )

    rounds = 0
    while response.status == "needs_clarification" and rounds < max_rounds:
        answers = [
            ClarificationAnswer(
                question_id=question.question_id,
                answer=answer_for_field(question.field, record),
            )
            for question in response.pending_questions
        ]
        response = service.answer_clarifications(
            AnswerClarificationsRequest(session_id=f"eval_{case_id}", answers=answers)
        )
        rounds += 1

    artifacts = response.artifacts
    problem_type = artifacts.problem_spec.problem_type.value if artifacts.problem_spec else ""
    project_classification = ""
    alternatives: list[str] = []
    rationale: Any = ""

    if artifacts.recommendation and artifacts.recommendation.recommended_method_family:
        project_classification = artifacts.recommendation.recommended_method_family
    if not project_classification and artifacts.ranking and artifacts.ranking.ranked_methods:
        project_classification = artifacts.ranking.ranked_methods[0].method_family
    if artifacts.ranking and artifacts.ranking.ranked_methods:
        alternatives = [item.method_family for item in artifacts.ranking.ranked_methods[1:3]]
        rationale = artifacts.ranking.ranked_methods[0].rationale
    if not project_classification:
        project_classification = problem_type

    research = artifacts.research
    research_assumptions = research.assumptions if research else []
    used_fixture_research_fallback = any(
        "Fell back to fixture research evidence" in assumption
        for assumption in research_assumptions
    )
    research_citations: list[dict[str, Any]] = []
    if research:
        for card in research.evidence_cards:
            for citation in card.citations:
                research_citations.append(
                    {
                        "method_family": card.method_family,
                        "title": citation.title,
                        "url": citation.url,
                        "source_type": citation.source_type,
                    }
                )

    return {
        "case_id": case_id,
        "paper_number": record.get("paper_number"),
        "title": record.get("title", ""),
        "status": response.status,
        "project_problem_type": problem_type,
        "project_classification": project_classification,
        "project_alternatives": alternatives,
        "project_rationale": rationale,
        "clarification_rounds": response.clarification_rounds,
        "research_mode": settings.research_mode,
        "llm_provider": settings.llm_provider,
        "research_candidate_methods": research.candidate_method_families if research else [],
        "research_assumptions": research_assumptions,
        "used_fixture_research_fallback": used_fixture_research_fallback,
        "research_citations": research_citations[:10],
    }


def write_jsonl(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run project predictions for the paper-context benchmark.")
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD, help="Gold-label JSONL used only for case ids and social-problem text.")
    parser.add_argument("--output", "-o", type=Path, default=DEFAULT_OUTPUT, help="Prediction JSONL output path.")
    parser.add_argument("--split-file", type=Path, default=DEFAULT_SPLIT_FILE, help="Train/test split JSON file.")
    parser.add_argument("--split", choices=SPLIT_CHOICES, default="all", help="Which split to run.")
    parser.add_argument("--research-mode", choices=RESEARCH_MODES, default="fixture", help="Research provider mode.")
    parser.add_argument("--require-live-research", action="store_true", help="Fail if live research falls back to fixture evidence.")
    parser.add_argument("--llm-provider", choices=LLM_PROVIDERS, default="fixture", help="Prompt-executor provider.")
    parser.add_argument("--llm-api-key-env", default="LLM_API_KEY", help="Environment variable containing the live LLM API key.")
    parser.add_argument("--llm-model", default=None, help="OpenAI-compatible model name for live prompting.")
    parser.add_argument("--llm-base-url", default=None, help="OpenAI-compatible base URL for live prompting.")
    parser.add_argument("--llm-timeout-seconds", type=float, default=None, help="Live LLM HTTP timeout.")
    parser.add_argument("--research-timeout-seconds", type=float, default=None, help="Live research HTTP timeout.")
    parser.add_argument("--max-rounds", type=int, default=3, help="Maximum auto-clarification rounds per case.")
    return parser.parse_args()


def configure_settings(args: argparse.Namespace) -> None:
    settings.research_mode = args.research_mode
    settings.llm_provider = args.llm_provider

    if args.llm_provider == "fixture":
        settings.llm_api_key = ""
    else:
        settings.llm_api_key = os.environ.get(args.llm_api_key_env, "")
        if not settings.llm_api_key:
            raise RuntimeError(
                f"{args.llm_api_key_env} is not set. "
                "Set it or use --llm-provider fixture for a smoke run."
            )

    if args.llm_model:
        settings.llm_model = args.llm_model
    if args.llm_base_url:
        settings.llm_base_url = args.llm_base_url
    if args.llm_timeout_seconds is not None:
        settings.llm_timeout_seconds = args.llm_timeout_seconds
    if args.research_timeout_seconds is not None:
        settings.research_timeout_seconds = args.research_timeout_seconds


def main() -> None:
    args = parse_args()
    configure_settings(args)

    split_case_ids = load_split_case_ids(args.split_file, args.split)
    records = filter_records_by_case_ids(load_jsonl(args.gold), split_case_ids)
    with tempfile.TemporaryDirectory(prefix="ai4si_eval_sessions_") as temp_dir:
        service = CoordinatorService()
        service.repo = SessionRepository(base_dir=Path(temp_dir))
        predictions = [run_case(service, record, args.max_rounds) for record in records]

    if args.require_live_research:
        fallback_case_ids = [
            prediction["case_id"]
            for prediction in predictions
            if prediction["used_fixture_research_fallback"]
        ]
        if fallback_case_ids:
            raise RuntimeError(
                "Live research fell back to fixture evidence for: "
                + ", ".join(fallback_case_ids)
            )

    write_jsonl(predictions, args.output)
    print(f"Wrote {len(predictions)} {args.split} project predictions to {args.output}")


if __name__ == "__main__":
    main()
