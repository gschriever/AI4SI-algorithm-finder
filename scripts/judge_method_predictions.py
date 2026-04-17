"""Score project method predictions against paper gold labels.

Input predictions may be JSONL or JSON. Each record should include a case_id
such as "paper_05" plus one of:
    project_classification
    predicted_method_family
    recommended_method_family
    classification

The script also understands API-shaped records with:
    artifacts.recommendation.recommended_method_family
    artifacts.ranking.ranked_methods[0].method_family

Examples:
    python scripts/build_gold_labels.py
    python scripts/judge_method_predictions.py --predictions outputs/project_predictions.jsonl --provider gemini
    python scripts/judge_method_predictions.py --predictions outputs/project_predictions.jsonl --provider openai_compatible
    python scripts/judge_method_predictions.py --predictions outputs/project_predictions.jsonl --provider fixture
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from build_gold_labels import parse_sources_index
from eval_split_utils import (
    DEFAULT_SPLIT_FILE,
    SPLIT_CHOICES,
    filter_records_by_case_ids,
    load_split_case_ids,
    sorted_case_ids,
)


DEFAULT_SOURCE_INDEX = Path("sources/sources_index.md")
DEFAULT_OUTPUT = Path("project_context/judge_results.jsonl")
DEFAULT_SUMMARY_OUTPUT = Path("project_context/judge_summary.json")

SCORE_PROMPT = """\
You are grading an AI4SI algorithm-classification system.

Compare the gold classification from the paper with the classification predicted by the project.
Score semantic agreement from 0 to 1:
- 1.0 = exact or near-exact method-family match.
- 0.75 = compatible but less specific.
- 0.5 = same broad optimization family, but too generic or missing key specificity.
- 0.25 = weakly related but mostly wrong.
- 0.0 = wrong method family.

Do not require exact wording. Treat synonyms as matches, such as RMAB and restless multi-armed bandit.
If the project prediction is only a broad problem type like allocation, prediction, forecasting, or mixed, it should not receive more than 0.5 unless the gold label is also that broad.
Set match to true only when score is at least the supplied match threshold.

Return JSON only with:
case_id, score, match, reason.
"""


def load_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("predictions", "results", "records", "items"):
            if isinstance(data.get(key), list):
                return data[key]
        return [dict({"case_id": key}, **value) for key, value in data.items() if isinstance(value, dict)]
    raise ValueError(f"Unsupported prediction file shape in {path}")


def load_gold(path: Path | None, source_index: Path) -> list[dict[str, Any]]:
    if path is None:
        return parse_sources_index(source_index)
    return load_records(path)


def index_gold(records: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_case_id: dict[str, dict[str, Any]] = {}
    by_title: dict[str, dict[str, Any]] = {}
    for record in records:
        case_id = normalize_case_id(record.get("case_id") or record.get("paper_number"))
        if case_id:
            by_case_id[case_id] = record
        title = normalize_text(record.get("title", ""))
        if title:
            by_title[title] = record
    return by_case_id, by_title


def normalize_case_id(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, int):
        return f"paper_{value:02d}"
    text = str(value).strip().lower()
    if not text:
        return ""
    number_match = re.search(r"(\d+)", text)
    if text.startswith("paper") and number_match:
        return f"paper_{int(number_match.group(1)):02d}"
    if text.isdigit():
        return f"paper_{int(text):02d}"
    return text


def normalize_text(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def extract_project_classification(record: dict[str, Any]) -> str:
    direct_keys = (
        "project_classification",
        "predicted_classification",
        "predicted_method_family",
        "recommended_method_family",
        "method_family",
        "classification",
        "prediction",
    )
    for key in direct_keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    artifacts = record.get("artifacts")
    if isinstance(artifacts, dict):
        recommendation = artifacts.get("recommendation")
        if isinstance(recommendation, dict):
            value = recommendation.get("recommended_method_family")
            if isinstance(value, str) and value.strip():
                return value.strip()

        ranking = artifacts.get("ranking")
        if isinstance(ranking, dict):
            ranked_methods = ranking.get("ranked_methods")
            if isinstance(ranked_methods, list) and ranked_methods:
                first = ranked_methods[0]
                if isinstance(first, dict):
                    value = first.get("method_family")
                    if isinstance(value, str) and value.strip():
                        return value.strip()

    return ""


def extract_project_rationale(record: dict[str, Any]) -> Any:
    for key in ("project_rationale", "rationale", "reason", "summary"):
        if record.get(key):
            return record[key]
    artifacts = record.get("artifacts")
    if isinstance(artifacts, dict):
        recommendation = artifacts.get("recommendation")
        if isinstance(recommendation, dict):
            return recommendation.get("summary") or recommendation.get("risks") or ""
        ranking = artifacts.get("ranking")
        if isinstance(ranking, dict):
            ranked_methods = ranking.get("ranked_methods")
            if isinstance(ranked_methods, list) and ranked_methods:
                first = ranked_methods[0]
                if isinstance(first, dict):
                    return first.get("rationale", "")
    return ""


def find_gold_record(
    prediction: dict[str, Any],
    by_case_id: dict[str, dict[str, Any]],
    by_title: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    case_id = normalize_case_id(prediction.get("case_id") or prediction.get("paper_number"))
    if case_id and case_id in by_case_id:
        return by_case_id[case_id]
    title = normalize_text(str(prediction.get("title") or prediction.get("paper_title") or ""))
    if title and title in by_title:
        return by_title[title]
    raise KeyError(f"Could not match prediction to a gold label: {prediction}")


def build_judge_payload(gold: dict[str, Any], prediction: dict[str, Any], threshold: float) -> dict[str, Any]:
    return {
        "case_id": normalize_case_id(gold.get("case_id") or gold.get("paper_number")),
        "paper_title": gold.get("title", ""),
        "paper_social_problem": gold.get("social_problem", ""),
        "gold_classification": gold.get("gold_classification", ""),
        "gold_optimization_type": gold.get("gold_optimization_type", ""),
        "gold_key_method": gold.get("gold_key_method", ""),
        "project_classification": extract_project_classification(prediction),
        "project_rationale": extract_project_rationale(prediction),
        "match_threshold": threshold,
    }


def judge_with_openai_compatible(payload: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    api_key = os.environ.get(args.api_key_env, "")
    if not api_key:
        raise RuntimeError(f"{args.api_key_env} is not set")

    body = {
        "model": args.model,
        "messages": [
            {"role": "system", "content": SCORE_PROMPT},
            {"role": "user", "content": json.dumps(payload, indent=2, ensure_ascii=False)},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        args.base_url.rstrip("/") + args.chat_completions_path,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            args.api_key_header: f"{args.api_key_prefix} {api_key}".strip(),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=args.timeout_seconds) as response:
            response_json = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Judge API request failed with {exc.code}: {detail}") from exc

    content = response_json["choices"][0]["message"]["content"]
    return json.loads(content)


def judge_with_gemini(payload: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    api_key = os.environ.get(args.gemini_api_key_env, "")
    if not api_key:
        raise RuntimeError(f"{args.gemini_api_key_env} is not set")
    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise RuntimeError("google-generativeai is not installed. Install it or use --provider openai_compatible.") from exc

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(args.model)
    prompt = SCORE_PROMPT + "\n\nINPUT:\n" + json.dumps(payload, indent=2, ensure_ascii=False)
    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0, "response_mime_type": "application/json"},
    )
    return json.loads(response.text)


def judge_with_fixture(payload: dict[str, Any], threshold: float) -> dict[str, Any]:
    gold = payload.get("gold_classification", "")
    project = payload.get("project_classification", "")
    score, reason = heuristic_score(gold, project)
    return {
        "case_id": payload["case_id"],
        "score": score,
        "match": score >= threshold,
        "reason": reason,
    }


def heuristic_score(gold: str, project: str) -> tuple[float, str]:
    if not project.strip():
        return 0.0, "No project classification was provided."

    gold_family = canonical_family(gold)
    project_family = canonical_family(project)
    if gold_family and project_family and gold_family == project_family:
        return 1.0, f"Both labels normalize to {gold_family}."
    if gold_family and project_family and family_parent(gold_family) == family_parent(project_family):
        return 0.75, f"Labels are compatible within {family_parent(gold_family)}."

    gold_words = set(normalize_text(gold).split())
    project_words = set(normalize_text(project).split())
    overlap = gold_words & project_words
    if len(overlap) >= 2:
        return 0.5, "The labels share some method language but the match is not specific."
    if overlap:
        return 0.25, "The labels have a weak lexical relationship."
    return 0.0, "The labels do not appear to match."


FAMILIES = {
    "restless_multi_armed_bandit": (
        "rmab",
        "restless multi armed bandit",
        "restless bandit",
        "whittle",
        "sprmab",
        "cormab",
        "non markovian rmab",
    ),
    "multi_objective_reinforcement_learning": (
        "multi objective rl",
        "multi objective reinforcement learning",
        "generalized p means",
        "portfolio of policies",
    ),
    "multi_armed_bandit": (
        "multi armed bandit",
        "mab",
        "bandit",
        "thompson sampling",
        "ucb",
        "collaborative bandit",
        "stochastic bandit",
    ),
    "graph_frontier_exploration": (
        "graph frontier exploration",
        "policy embedded graph expansion",
        "pege",
        "frontier exploration",
        "gittins index",
        "sequential node selection",
        "incrementally revealed networks",
    ),
    "mixed_integer_programming": (
        "mixed integer",
        "milp",
        "mip",
        "integer programming",
        "mixed integer linear programming",
    ),
    "pomdp": ("pomdp", "partially observable markov decision process"),
    "influence_maximization": ("influence maximization", "seed set", "network diffusion"),
    "stackelberg_security_game": ("stackelberg", "security game", "patrol scheduling"),
    "decision_focused_learning": ("decision focused learning", "dfl"),
    "inverse_reinforcement_learning": ("inverse reinforcement learning", "irl", "whirl"),
    "distributionally_robust_optimization": ("distributionally robust", "dro", "dpo pro"),
    "llm_aggregation_weighting": ("llm aggregation weighting", "optimal weight", "inverse surprising popularity", "majority voting", "higher order information"),
    "multi_objective_pareto_optimization": ("multi objective pareto", "pareto", "reward shaping", "vortex"),
    "decision_language_model": ("decision language model", "dlm", "decision language", "reward function specification"),
    "reinforcement_learning": ("reinforcement learning", "deep reinforcement learning", "ppo", "rl"),
    "robust_optimization": ("robust optimization",),
    "graph_optimization": (
        "graph optimization",
        "combinatorial graph optimization",
        "facility location",
        "facility planning",
        "coverage optimization",
        "coverage maximization",
        "population coverage",
        "clusternet",
        "extended greedy",
        "health access resource planner",
        "harp",
    ),
    "game_theoretic_optimization": ("game theoretic", "nash equilibrium", "escape sensing"),
}

PARENTS = {
    "restless_multi_armed_bandit": "sequential_decision_optimization",
    "multi_objective_reinforcement_learning": "sequential_decision_optimization",
    "multi_armed_bandit": "sequential_decision_optimization",
    "graph_frontier_exploration": "sequential_decision_optimization",
    "pomdp": "sequential_decision_optimization",
    "reinforcement_learning": "sequential_decision_optimization",
    "inverse_reinforcement_learning": "sequential_decision_optimization",
    "decision_language_model": "sequential_decision_optimization",
    "decision_focused_learning": "learning_to_optimize",
    "mixed_integer_programming": "constrained_optimization",
    "robust_optimization": "robust_optimization",
    "distributionally_robust_optimization": "robust_optimization",
    "multi_objective_pareto_optimization": "multi_objective_optimization",
    "llm_aggregation_weighting": "aggregation_optimization",
    "influence_maximization": "graph_optimization",
    "graph_optimization": "graph_optimization",
    "stackelberg_security_game": "game_theoretic_optimization",
    "game_theoretic_optimization": "game_theoretic_optimization",
}


def canonical_family(value: str) -> str:
    normalized = normalize_text(value)
    if "stackelberg" in normalized or "escape sensing" in normalized:
        return "stackelberg_security_game" if "stackelberg" in normalized else "game_theoretic_optimization"
    for family, aliases in FAMILIES.items():
        if any(alias_matches(normalized, alias) for alias in aliases):
            return family
    return ""


def alias_matches(normalized_value: str, alias: str) -> bool:
    normalized_alias = normalize_text(alias)
    if len(normalized_alias) <= 3:
        return re.search(rf"\b{re.escape(normalized_alias)}\b", normalized_value) is not None
    return normalized_alias in normalized_value


def family_parent(family: str) -> str:
    return PARENTS.get(family, family)


def clean_judgment(raw: dict[str, Any], payload: dict[str, Any], threshold: float) -> dict[str, Any]:
    score = float(raw.get("score", 0.0))
    score = max(0.0, min(1.0, score))
    return {
        "case_id": str(raw.get("case_id") or payload["case_id"]),
        "score": score,
        "match": parse_bool(raw.get("match"), default=score >= threshold),
        "reason": str(raw.get("reason", "")),
        "paper_title": payload.get("paper_title", ""),
        "gold_classification": payload.get("gold_classification", ""),
        "project_classification": payload.get("project_classification", ""),
    }


def parse_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "1"}:
            return True
        if normalized in {"false", "no", "0"}:
            return False
    return default


def judge_one(payload: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    if args.provider == "fixture":
        raw = judge_with_fixture(payload, args.match_threshold)
    elif args.provider == "gemini":
        raw = judge_with_gemini(payload, args)
    else:
        raw = judge_with_openai_compatible(payload, args)
    return clean_judgment(raw, payload, args.match_threshold)


def summarize(judgments: list[dict[str, Any]], threshold: float, args: argparse.Namespace) -> dict[str, Any]:
    n = len(judgments)
    average_score = sum(item["score"] for item in judgments) / n if n else 0.0
    binary_match_rate = sum(item["score"] >= threshold for item in judgments) / n if n else 0.0
    return {
        "n": n,
        "split": args.split,
        "split_file": str(args.split_file) if args.split != "all" else None,
        "case_ids": sorted_case_ids([str(item["case_id"]) for item in judgments]),
        "average_semantic_match_score": round(average_score, 4),
        "binary_match_threshold": threshold,
        "binary_match_rate": round(binary_match_rate, 4),
        "matches": sum(item["score"] >= threshold for item in judgments),
    }


def write_jsonl(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Use an LLM judge to score project method predictions.")
    parser.add_argument("--predictions", required=True, type=Path, help="Project prediction .jsonl or .json file.")
    parser.add_argument("--gold", type=Path, default=None, help="Optional gold-label .jsonl or .json file.")
    parser.add_argument("--source-index", type=Path, default=DEFAULT_SOURCE_INDEX, help="Used when --gold is omitted.")
    parser.add_argument("--output", "-o", type=Path, default=DEFAULT_OUTPUT, help="Judgment JSONL output path.")
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT, help="Summary JSON output path.")
    parser.add_argument("--split-file", type=Path, default=DEFAULT_SPLIT_FILE, help="Train/test split JSON file.")
    parser.add_argument("--split", choices=SPLIT_CHOICES, default="all", help="Which split to judge.")
    parser.add_argument("--match-threshold", type=float, default=0.75, help="Score threshold counted as a binary match.")
    parser.add_argument(
        "--provider",
        choices=["openai_compatible", "gemini", "fixture"],
        default="openai_compatible",
        help="Judge provider. Use fixture for offline smoke tests only.",
    )
    parser.add_argument("--model", default=None, help="Judge model name.")
    parser.add_argument("--base-url", default="https://api.openai.com/v1", help="OpenAI-compatible base URL.")
    parser.add_argument("--chat-completions-path", default="/chat/completions", help="OpenAI-compatible chat path.")
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY", help="Env var for OpenAI-compatible API key.")
    parser.add_argument("--api-key-header", default="Authorization", help="Header name for OpenAI-compatible API key.")
    parser.add_argument("--api-key-prefix", default="Bearer", help="Header prefix for OpenAI-compatible API key.")
    parser.add_argument("--gemini-api-key-env", default="GEMINI_API_KEY", help="Env var for Gemini API key.")
    parser.add_argument("--timeout-seconds", type=float, default=60.0, help="HTTP timeout for OpenAI-compatible judge.")
    parser.add_argument("--sleep-seconds", type=float, default=0.0, help="Delay between judge requests.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.model is None:
        args.model = "gemini-1.5-flash" if args.provider == "gemini" else "gpt-5-mini"

    split_case_ids = load_split_case_ids(args.split_file, args.split)
    gold_records = filter_records_by_case_ids(load_gold(args.gold, args.source_index), split_case_ids)
    by_case_id, by_title = index_gold(gold_records)
    predictions = filter_records_by_case_ids(load_records(args.predictions), split_case_ids)

    judgments: list[dict[str, Any]] = []
    for index, prediction in enumerate(predictions, start=1):
        gold = find_gold_record(prediction, by_case_id, by_title)
        payload = build_judge_payload(gold, prediction, args.match_threshold)
        judgment = judge_one(payload, args)
        judgments.append(judgment)
        print(
            f"[{index}/{len(predictions)}] {judgment['case_id']}: "
            f"score={judgment['score']:.2f} match={judgment['match']}",
            file=sys.stderr,
        )
        if args.sleep_seconds:
            time.sleep(args.sleep_seconds)

    summary = summarize(judgments, args.match_threshold, args)
    write_jsonl(judgments, args.output)
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"Wrote judgments to {args.output}", file=sys.stderr)
    print(f"Wrote summary to {args.summary_output}", file=sys.stderr)


if __name__ == "__main__":
    main()
