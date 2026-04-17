"""
AI4SI Algorithm Selector — Automated Evaluation Harness
========================================================

Feeds each paper's social-problem description into the AlgorithmSelector API,
auto-answers any clarification questions using a helper LLM, and compares the
predicted method family to the paper's actual method.

Setup:
    pip install httpx google-generativeai

    # Start the AlgorithmSelector API first:
    cd AlgorithmSelector
    uvicorn main:app --app-dir apps/api/src --reload

Usage:
    # Basic run (defaults to http://127.0.0.1:8000)
    python scripts/evaluate_pipeline.py

    # Custom API URL
    python scripts/evaluate_pipeline.py --api-url http://localhost:8080

    # Save results to a markdown file
    python scripts/evaluate_pipeline.py --output eval_results.md

    # Use fixture mode (no Gemini key needed for auto-answering)
    python scripts/evaluate_pipeline.py --no-auto-answer
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap
import time
from dataclasses import dataclass, field
from pathlib import Path

import anthropic
import httpx

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class PaperRecord:
    """One row from context_extraction.md."""
    title: str
    authors: str
    social_problem: str
    methods: str


@dataclass
class EvalResult:
    """Outcome of evaluating a single paper."""
    paper_title: str
    social_problem: str
    ground_truth_method: str
    predicted_method: str | None = None
    predicted_alternatives: list[str] = field(default_factory=list)
    status: str = ""           # completed | vetoed | needs_clarification | error
    clarification_rounds: int = 0
    match_verdict: str = ""    # exact | partial | miss | error
    error_message: str = ""
    raw_recommendation: str = ""


# ---------------------------------------------------------------------------
# 1. Parse the ground-truth table
# ---------------------------------------------------------------------------

def parse_context_extraction(path: Path) -> list[PaperRecord]:
    """Parse the markdown table in context_extraction.md into PaperRecords."""
    text = path.read_text(encoding="utf-8")
    lines = text.strip().splitlines()

    # Find the table rows (skip header + separator)
    table_rows: list[str] = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and "Article Title" in stripped:
            in_table = True
            continue
        if in_table and stripped.startswith("|---"):
            continue
        if in_table and stripped.startswith("|"):
            table_rows.append(stripped)
        elif in_table and not stripped.startswith("|"):
            break

    records: list[PaperRecord] = []
    for row in table_rows:
        # Split by | but ignore leading/trailing empty cells
        cells = [cell.strip() for cell in row.split("|")]
        cells = [c for c in cells if c != ""]  # remove empties from leading/trailing |
        if len(cells) < 4:
            continue
        records.append(PaperRecord(
            title=cells[0],
            authors=cells[1],
            social_problem=cells[2],
            methods=cells[3],
        ))
    return records


# ---------------------------------------------------------------------------
# 2. Gemini helper for auto-answering clarification questions
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 2. Gemini helper for auto-answering clarification questions
# ---------------------------------------------------------------------------

class RequestHelper:
    """Handles HTTP requests with retries and exponential backoff."""
    def __init__(self, max_retries: int = 5, base_delay: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def post(self, client: httpx.Client, url: str, **kwargs) -> httpx.Response:
        for i in range(self.max_retries):
            try:
                resp = client.post(url, **kwargs)
                if resp.status_code == 429:
                    delay = self.base_delay * (2 ** i)
                    print(f"    ⏳ Rate limited (429). Waiting {delay:.1f}s (retry {i+1}/{self.max_retries})...", file=sys.stderr)
                    time.sleep(delay)
                    continue
                resp.raise_for_status()
                return resp
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    delay = self.base_delay * (2 ** i)
                    print(f"    ⏳ Rate limited (429). Waiting {delay:.1f}s (retry {i+1}/{self.max_retries})...", file=sys.stderr)
                    time.sleep(delay)
                    continue
                raise
            except (httpx.RequestError, Exception) as e:
                if i == self.max_retries - 1:
                    raise
                delay = self.base_delay * (2 ** i)
                print(f"    ⏳ Request failed ({e}). Retrying in {delay:.1f}s...", file=sys.stderr)
                time.sleep(delay)
        raise RuntimeError(f"Max retries exceeded for {url}")

request_helper = RequestHelper()

def auto_answer_questions(
    questions: list[dict],
    social_problem: str,
    methods_hint: str,
) -> list[dict]:
    """
    Use an LLM (Claude or Gemini) to role-play as a domain expert and answer the API's
    clarification questions, given the paper's social problem context.
    """
    asked_fields = {q.get("field", "").strip().lower() for q in questions}
    answers: list[dict] = []

    # Choose provider
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    q_block = "\n".join(
        f"  Q{i+1} (id={q['question_id']}, field={q['field']}): {q['question']}"
        for i, q in enumerate(questions)
    )

    prompt = textwrap.dedent(f"""\
        You are a domain expert describing a social-impact optimization problem.

        PROBLEM CONTEXT:
        {social_problem}

        The system is asking you clarification questions before it can recommend
        an algorithmic approach. Answer each question concisely (1-3 sentences)
        using only the information above. If the context doesn't provide enough
        detail, make a reasonable assumption and state it.

        Do NOT reveal or hint at the actual solution method. Focus only on
        describing the problem's operational details.

        QUESTIONS:
        {q_block}

        Respond in JSON — a list of objects with "question_id" and "answer" keys.
        IMPORTANT: Use US English spelling (e.g. "maximize", not "maximise") in your descriptions.
        Example: [{"question_id": "q1_field", "answer": "..."}]
    """)

    try:
        content = ""
        if anthropic_key:
            client = anthropic.Anthropic(
                api_key=anthropic_key,
                timeout=120.0
            )
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.content[0].text
        elif gemini_key:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-1.5-pro-latest")
            response = model.generate_content(prompt)
            content = response.text
        else:
            raise RuntimeError("No API key available for simulation")

        # Robust JSON extraction
        json_str = content.strip()
        if "```json" in content:
            match = re.search(r"```json\s*\n?(.*?)\n?```", content, re.DOTALL)
            if match:
                json_str = match.group(1).strip()
        elif "```" in content:
            match = re.search(r"```\s*\n?(.*?)\n?```", content, re.DOTALL)
            if match:
                json_str = match.group(1).strip()
        else:
            # Fallback: Find anything between first '[' and last ']'
            match = re.search(r"(\[.*\])", content, re.DOTALL)
            if match:
                json_str = match.group(1).strip()

        answers = [{"question_id": a["question_id"], "answer": a["answer"]} for a in json.loads(json_str)]

    except Exception as e:
        print(f"    ⚠ Simulation failed ({e}), using heuristic", file=sys.stderr)
        answers = _heuristic_answers(questions)

    # Always inject critical fields that the fixture diagnosis code requires,
    # even if they weren't in the clarification questions this round.
    # The API stores extra answers under their question_id as key.
    _CRITICAL_EXTRAS = {
        "narrower operational decision": (
            f"Sequentially deciding which subset of beneficiaries to allocate "
            f"a scarce resource to in each decision period, under capacity and "
            f"fairness constraints. Specifically: {social_problem[:120]}"
        ),
        "decision variable": (
            "Which individuals or groups should receive the limited intervention "
            "resource in each decision period."
        ),
        "objective function": (
            "Maximize long-term positive outcomes across the target population."
        ),
        "constraints": (
            "Limited budget and staff capacity; fairness constraints require "
            "equitable coverage across subgroups."
        ),
    }
    answered_ids = {a["question_id"] for a in answers}
    for field, default_answer in _CRITICAL_EXTRAS.items():
        if field not in asked_fields and field not in answered_ids:
            answers.append({"question_id": field, "answer": default_answer})

    return answers


def _heuristic_answers(questions: list[dict]) -> list[dict]:
    """Simple fallback answers when Gemini is not available."""
    defaults = {
        "decision variable": "Which individuals or groups should receive the limited intervention resource in each decision period.",
        "objective function": "Maximize long-term positive outcomes (e.g., engagement, health metric improvement) across the entire target population.",
        "constraints": "Limited budget and staff capacity; each intervention round can only reach a fraction of the population. Fairness constraints require equitable coverage across subgroups.",
        "utility scoring weights": "70% outcome improvement, 20% equity across subgroups, 10% operational cost efficiency.",
        "label quality": "Historical outcome data is available but may be incomplete for some subgroups. Labels are based on observed engagement which is a reasonable but imperfect proxy.",
        "intervention effect": "The intervention (e.g., outreach call, resource allocation) has demonstrated positive effects in prior studies and field trials.",
        "service floor policy": "Yes — minimum service levels must be maintained for all geographic regions and demographic subgroups.",
        "narrower operational decision": "Sequentially deciding which subset of beneficiaries to allocate a scarce resource to in each decision period, under capacity and fairness constraints.",
    }
    answers = []
    for q in questions:
        field_key = q.get("field", "").strip().lower()
        answer = defaults.get(field_key, "This should be determined based on the specific operational context. The decision involves resource allocation under constraints.")
        answers.append({"question_id": q["question_id"], "answer": answer})
    return answers


# ---------------------------------------------------------------------------
# 3. Evaluate one paper against the API
# ---------------------------------------------------------------------------

MAX_CLARIFICATION_ROUNDS = 5

def evaluate_paper(
    paper: PaperRecord,
    api_url: str,
    session_id: str,
    auto_answer: bool = True,
) -> EvalResult:
    """Run a single paper through the AlgorithmSelector pipeline."""
    result = EvalResult(
        paper_title=paper.title,
        social_problem=paper.social_problem,
        ground_truth_method=paper.methods,
    )

    try:
        with httpx.Client(timeout=600.0) as client:
            # Start session
            resp = request_helper.post(
                client,
                f"{api_url}/api/pipeline/start",
                json={
                    "session_id": session_id,
                    "narrative": paper.social_problem,
                },
            )
            data = resp.json()

            rounds = 0
            while data.get("status") == "needs_clarification" and rounds < MAX_CLARIFICATION_ROUNDS:
                rounds += 1
                questions = data.get("pending_questions", [])
                if not questions or not auto_answer:
                    break

                answers = auto_answer_questions(questions, paper.social_problem, paper.methods)

                resp = request_helper.post(
                    client,
                    f"{api_url}/api/pipeline/answer",
                    json={
                        "session_id": session_id,
                        "answers": answers,
                    },
                )
                data = resp.json()

            result.status = data.get("status", "unknown")
            result.clarification_rounds = rounds

            # Extract prediction
            artifacts = data.get("artifacts", {})

            recommendation = artifacts.get("recommendation")
            if recommendation:
                result.predicted_method = recommendation.get("recommended_method_family")
                result.predicted_alternatives = recommendation.get("alternatives_considered", [])
                result.raw_recommendation = recommendation.get("summary", "")

            # Fallback: use ranking if recommendation didn't populate
            if not result.predicted_method:
                ranking = artifacts.get("ranking")
                if ranking and ranking.get("ranked_methods"):
                    top = ranking["ranked_methods"][0]
                    result.predicted_method = top.get("method_family")
                    result.predicted_alternatives = [
                        m.get("method_family", "") for m in ranking["ranked_methods"][1:4]
                    ]

    except Exception as e:
        result.status = "error"
        result.error_message = str(e)

    # Compute match verdict
    result.match_verdict = compute_match(result.ground_truth_method, result.predicted_method)
    return result


# ---------------------------------------------------------------------------
# 4. Match scoring
# ---------------------------------------------------------------------------

def normalize_method(text: str) -> set[str]:
    """Extract key method-related tokens from a method description."""
    text = text.lower()
    # Remove common filler
    for noise in ["---", "—", "⚠️", "**", "*"]:
        text = text.replace(noise, " ")
    tokens = set(re.findall(r"[a-z][a-z0-9_]+", text))
    return tokens


# Method family aliases — map various terms to canonical families
METHOD_ALIASES: dict[str, list[str]] = {
    "rmab":             ["restless", "bandit", "rmab", "whittle", "index"],
    "reinforcement_learning": ["reinforcement", "rl", "ppo", "drl", "deep_rl", "q_network"],
    "integer_programming":    ["integer", "milp", "ilp", "mip", "linear_programming", "combinatorial", "solver"],
    "decision_focused": ["decision_focused", "dfl", "predict_then_optimize", "end_to_end"],
    "game_theory":      ["game", "stackelberg", "nash", "equilibrium", "security"],
    "influence_max":    ["influence", "maximization", "seed", "spread", "network"],
    "bandit":           ["bandit", "mab", "ucb", "thompson", "gittins"],
    "pomdp":            ["pomdp", "partially_observable", "markov"],
    "coverage_optimization": ["coverage", "greedy", "facility", "location", "submodular"],
    "diffusion_model":  ["diffusion", "smc", "monte_carlo"],
    "inverse_rl":       ["inverse", "irl", "reward_learning"],
    "multi_objective":  ["multi_objective", "pareto", "welfare", "social_choice"],
    "llm_alignment":    ["llm", "alignment", "rlhf", "dpo", "preference"],
    "robust_optimization": ["robust", "distributionally", "dro"],
}


def compute_match(ground_truth: str, predicted: str | None) -> str:
    """
    Compare the ground truth method description to the predicted method family.
    Returns: 'exact', 'partial', 'miss', or 'error'.
    """
    if not predicted:
        return "error"

    gt_tokens = normalize_method(ground_truth)
    pred_lower = predicted.lower().replace("-", "_").replace(" ", "_")

    # Check if the predicted family directly appears in the ground truth
    if pred_lower in ground_truth.lower().replace("-", "_").replace(" ", "_"):
        return "exact"

    # Check alias families
    for family, keywords in METHOD_ALIASES.items():
        pred_hits = any(kw in pred_lower for kw in keywords)
        gt_hits = sum(1 for kw in keywords if kw in gt_tokens or kw in ground_truth.lower())
        if pred_hits and gt_hits >= 2:
            return "exact"
        if pred_hits and gt_hits >= 1:
            return "partial"

    # Token overlap check
    pred_tokens = normalize_method(predicted)
    overlap = gt_tokens & pred_tokens
    if len(overlap) >= 3:
        return "partial"

    return "miss"


# ---------------------------------------------------------------------------
# 5. Reporting
# ---------------------------------------------------------------------------

def print_results(results: list[EvalResult], output_path: Path | None = None):
    """Print a summary table and accuracy metrics."""
    lines: list[str] = []

    lines.append("# AI4SI Algorithm Selector — Evaluation Results")
    lines.append(f"\n**Evaluated**: {len(results)} papers")
    lines.append(f"**Date**: {time.strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # Summary stats
    verdicts = [r.match_verdict for r in results]
    n_exact = verdicts.count("exact")
    n_partial = verdicts.count("partial")
    n_miss = verdicts.count("miss")
    n_error = verdicts.count("error")
    n_total = len(results)

    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Metric | Count | Rate |")
    lines.append(f"|--------|-------|------|")
    lines.append(f"| ✅ Exact match | {n_exact} | {n_exact/n_total*100:.1f}% |")
    lines.append(f"| 🟡 Partial match | {n_partial} | {n_partial/n_total*100:.1f}% |")
    lines.append(f"| ❌ Miss | {n_miss} | {n_miss/n_total*100:.1f}% |")
    lines.append(f"| ⚠️ Error | {n_error} | {n_error/n_total*100:.1f}% |")
    lines.append(f"| **Exact + Partial** | **{n_exact + n_partial}** | **{(n_exact + n_partial)/n_total*100:.1f}%** |")
    lines.append("")

    # Detailed results
    lines.append("## Detailed Results")
    lines.append("")
    lines.append("| # | Verdict | Paper | Predicted | Ground Truth (abbrev.) | Rounds |")
    lines.append("|---|---------|-------|-----------|----------------------|--------|")

    verdict_icons = {"exact": "✅", "partial": "🟡", "miss": "❌", "error": "⚠️"}

    for i, r in enumerate(results, 1):
        icon = verdict_icons.get(r.match_verdict, "?")
        gt_short = r.ground_truth_method[:60] + "…" if len(r.ground_truth_method) > 60 else r.ground_truth_method
        title_short = r.paper_title[:50] + "…" if len(r.paper_title) > 50 else r.paper_title
        pred = r.predicted_method or "(none)"
        lines.append(f"| {i} | {icon} | {title_short} | {pred} | {gt_short} | {r.clarification_rounds} |")

    lines.append("")

    # Per-paper details for misses and errors
    problem_cases = [r for r in results if r.match_verdict in ("miss", "error")]
    if problem_cases:
        lines.append("## Misses and Errors — Detail")
        lines.append("")
        for r in problem_cases:
            lines.append(f"### {r.paper_title}")
            lines.append(f"- **Status**: {r.status}")
            lines.append(f"- **Predicted**: {r.predicted_method or '(none)'}")
            lines.append(f"- **Alternatives**: {', '.join(r.predicted_alternatives) if r.predicted_alternatives else '(none)'}")
            lines.append(f"- **Ground Truth**: {r.ground_truth_method}")
            if r.error_message:
                lines.append(f"- **Error**: {r.error_message}")
            if r.raw_recommendation:
                lines.append(f"- **Recommendation Summary**: {r.raw_recommendation[:200]}")
            lines.append("")

    report = "\n".join(lines)

    # Always print to stdout
    print(report)

    # Optionally write to file
    if output_path:
        output_path.write_text(report, encoding="utf-8")
        print(f"\n📄 Results saved to {output_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# 6. Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate the AI4SI Algorithm Selector against the curated paper library.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--api-url", default="http://127.0.0.1:8000",
        help="Base URL of the running AlgorithmSelector API (default: http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--context-file", type=Path,
        default=Path(__file__).resolve().parent.parent / "project_context" / "context_extraction.md",
        help="Path to context_extraction.md (default: project_context/context_extraction.md)",
    )
    parser.add_argument(
        "--output", "-o", type=Path, default=None,
        help="Save results to a markdown file.",
    )
    parser.add_argument(
        "--no-auto-answer", action="store_true",
        help="Do not auto-answer clarification questions (stop at first clarification).",
    )
    parser.add_argument(
        "--limit", "-n", type=int, default=None,
        help="Only evaluate the first N papers (useful for quick testing).",
    )
    parser.add_argument(
        "--delay", type=float, default=5.0,
        help="Delay in seconds between papers to avoid rate limiting (default: 5.0)",
    )
    args = parser.parse_args()

    # Parse ground truth
    if not args.context_file.exists():
        print(f"Error: {args.context_file} not found.", file=sys.stderr)
        sys.exit(1)

    papers = parse_context_extraction(args.context_file)
    if args.limit:
        papers = papers[: args.limit]

    print(f"📚 Loaded {len(papers)} papers from {args.context_file.name}", file=sys.stderr)
    print(f"🔗 API: {args.api_url}", file=sys.stderr)
    print(f"🤖 Auto-answer: {'OFF' if args.no_auto_answer else 'ON'}", file=sys.stderr)
    print(f"⌛ Inter-paper delay: {args.delay}s", file=sys.stderr)
    print("", file=sys.stderr)

    # Check API is reachable
    try:
        with httpx.Client(timeout=5.0) as client:
            client.get(f"{args.api_url}/docs")
    except Exception:
        print(f"⚠️  Cannot reach {args.api_url}. Is the AlgorithmSelector API running?", file=sys.stderr)
        print(f"   Start it with: cd AlgorithmSelector && uvicorn main:app --app-dir apps/api/src --reload", file=sys.stderr)
        sys.exit(1)

    # Run evaluations
    results: list[EvalResult] = []
    for i, paper in enumerate(papers, 1):
        session_id = f"eval-{i:03d}-{int(time.time())}"
        print(f"[{i}/{len(papers)}] {paper.title[:60]}...", file=sys.stderr)

        result = evaluate_paper(
            paper=paper,
            api_url=args.api_url,
            session_id=session_id,
            auto_answer=not args.no_auto_answer,
        )
        results.append(result)

        icon = {"exact": "✅", "partial": "🟡", "miss": "❌", "error": "⚠️"}.get(result.match_verdict, "?")
        print(f"  {icon} {result.match_verdict} → predicted: {result.predicted_method or '(none)'}", file=sys.stderr)
        
        # Save incremental results
        if args.output:
            print_results(results, args.output)

        if i < len(papers) and args.delay > 0:
            time.sleep(args.delay)

    # Print results
    print("\n" + "=" * 70, file=sys.stderr)
    print_results(results, args.output)


if __name__ == "__main__":
    main()
