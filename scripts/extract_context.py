"""
Reads one or more AI4SI paper PDFs and extracts structured problem context
WITHOUT revealing the gold-label AI/ML technique used.

Setup:
    pip install pdfplumber google-generativeai
    Get a free API key at: https://aistudio.google.com/app/apikey
    export GEMINI_API_KEY=your_key_here

Usage:
    python extract_context.py sources/2408.12112v6.pdf
    python extract_context.py sources/*.pdf --output outputs/
    python extract_context.py sources/*.pdf --output outputs/ --format json
"""

import os
import sys
import json
import argparse
import textwrap
from pathlib import Path

import pdfplumber
import google.generativeai as genai

DEFAULT_MODEL = "gemini-1.5-flash"   # fast + free tier
MAX_PDF_CHARS = 30_000               # Gemini has a large context window

# Prompt

SYSTEM_PROMPT = """\
You are an expert in AI for Social Impact (AI4SI). You are given text extracted from a research paper.

Your task: extract the PROBLEM CONTEXT as a structured summary.

CRITICAL RULE: Do NOT reveal, name, or hint at the specific AI/ML model, algorithm, or technique used as the solution. The output feeds a second LLM that must independently identify the right approach. You must NOT include:
- Any algorithm or method name (e.g. Whittle index, RMAB, DFL, PPO, bandit, MILP, POMDP, Nash equilibrium, diffusion model, transformer, GNN, etc.)
- References to the solution technique, even obliquely
- Metrics or framing that would reveal the approach

DO include these sections with these exact headers:

## 1. Social Problem
Real-world problem, domain, affected population, geographic context.

## 2. Decision Structure
What decisions are made, by whom, how often, at what scale. Describe the action space in plain terms without naming algorithms.

## 3. Key Variables
Decision variables, outcome variables, measurable quantities. Use plain names, not algorithm-specific notation.

## 4. Objective
What to maximize or minimize, in plain terms.

## 5. Constraints
Resource limits, budget constraints, fairness requirements, operational rules.

## 6. Uncertainty and Information Structure
What is known vs unknown at decision time. How information is revealed. Whether outcomes are stochastic or states are hidden.

## 7. Stakeholders and Agents
Who the agents are, conflicting interests, adversaries, strategic interaction.

## 8. Scale and Complexity
Number of individuals/units/nodes, time horizon, decision frequency, computational constraints.

## 9. Data Availability
What data exists, what must be estimated, data quality challenges.

## 10. Why Simple Approaches Fall Short
Why naive approaches (random selection, rule-based heuristics) are insufficient. Do not name the solution — only describe the gap.

Write in neutral language. Do not presuppose a solution approach.
"""

# PDF text extraction 

SECTION_KEYWORDS = [
    "abstract", "introduction", "problem", "formulation", "setting",
    "motivation", "background", "challenge", "related work", "overview",
    "model", "setup", "framework", "preliminaries"
]

def extract_pdf_text(pdf_path: Path, max_chars: int = MAX_PDF_CHARS) -> str:
    """
    Extract text from PDF. Prioritises abstract, intro, and problem
    formulation sections — the parts most useful for context extraction.
    """
    all_pages = []
    priority_pages = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            all_pages.append(text)
            # Flag pages that look like intro/problem sections
            lower = text.lower()
            if any(kw in lower for kw in SECTION_KEYWORDS):
                priority_pages.append(text)

    # Use priority pages first, then fill remaining budget with the rest
    chosen = priority_pages if priority_pages else all_pages
    full_text = "\n\n".join(chosen)

    if len(full_text) > max_chars:
        head = int(max_chars * 0.85)
        tail = max_chars - head
        full_text = (
            full_text[:head]
            + "\n\n[... truncated for length ...]\n\n"
            + full_text[-tail:]
        )

    return full_text

# Gemini call

def call_gemini(pdf_text: str, model_name: str) -> str:
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"---\nPAPER TEXT:\n{pdf_text}\n---\n\n"
        "Now extract the problem context following the instructions above. "
        "Remember: do NOT name the algorithm or model used in the solution."
    )
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    return response.text.strip()

# Core extraction

def extract_context(pdf_path: Path, model_name: str, max_chars: int) -> dict:
    result = {
        "paper": pdf_path.name,
        "path": str(pdf_path),
        "model": model_name,
        "context": None,
        "error": None,
    }

    try:
        pdf_text = extract_pdf_text(pdf_path, max_chars=max_chars)
    except Exception as e:
        result["error"] = f"PDF read error: {e}"
        return result

    try:
        result["context"] = call_gemini(pdf_text, model_name)
    except Exception as e:
        result["error"] = f"Gemini API error: {e}"

    return result

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def write_markdown(result: dict, output_dir: Path) -> Path:
    stem = Path(result["path"]).stem
    out_path = output_dir / f"{stem}_context.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Context Extraction: {result['paper']}\n\n")
        f.write(f"*Model: {result['model']}*\n\n")
        if result["error"]:
            f.write(f"> **Error:** {result['error']}\n")
        else:
            f.write(result["context"])
            f.write("\n\n---\n")
            f.write("*Generated by extract_context.py — gold-label technique withheld.*\n")
    return out_path


def write_json(results: list, output_dir: Path) -> Path:
    out_path = output_dir / "contexts.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    return out_path


def print_result(result: dict):
    sep = "─" * 60
    print(f"\n{sep}")
    print(f"Paper: {result['paper']}")
    print(sep)
    if result["error"]:
        print(f"ERROR: {result['error']}")
    else:
        print(result["context"])

# CLI

def parse_args():
    parser = argparse.ArgumentParser(
        description="AI4SI Stage 1: Extract problem context using Google Gemini (free).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            setup:
              pip install pdfplumber google-generativeai
              Get a free API key: https://aistudio.google.com/app/apikey
              export GEMINI_API_KEY=your_key_here

            examples:
              python extract_context.py sources/2408.12112v6.pdf
              python extract_context.py sources/*.pdf --output outputs/
              python extract_context.py sources/*.pdf --output outputs/ --format json
        """),
    )
    parser.add_argument(
        "pdfs", nargs="+", type=Path,
        help="One or more PDF file paths.",
    )
    parser.add_argument(
        "--output", "-o", type=Path, default=None,
        help="Directory to write output files. Omit to print to stdout only.",
    )
    parser.add_argument(
        "--format", "-f", choices=["markdown", "json", "both"], default="markdown",
        help="Output format (default: markdown).",
    )
    parser.add_argument(
        "--model", "-m", default=DEFAULT_MODEL,
        help=f"Gemini model name (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--max-chars", type=int, default=MAX_PDF_CHARS,
        help=f"Max PDF characters sent to the model (default: {MAX_PDF_CHARS}).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not set.", file=sys.stderr)
        print("Get a free key at: https://aistudio.google.com/app/apikey", file=sys.stderr)
        print("Then run: export GEMINI_API_KEY=your_key_here", file=sys.stderr)
        sys.exit(1)

    genai.configure(api_key=api_key)

    pdfs = [p for p in args.pdfs if p.suffix.lower() == ".pdf"]
    missing = [p for p in pdfs if not p.exists()]
    for m in missing:
        print(f"Warning: file not found: {m}", file=sys.stderr)
    pdfs = [p for p in pdfs if p.exists()]

    if not pdfs:
        print("Error: no valid PDF files found.", file=sys.stderr)
        sys.exit(1)

    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)

    results = []
    for i, pdf_path in enumerate(pdfs):
        print(f"[{i+1}/{len(pdfs)}] {pdf_path.name} ...", file=sys.stderr)
        result = extract_context(pdf_path, model_name=args.model, max_chars=args.max_chars)
        results.append(result)
        print_result(result)

        if args.output and args.format in ("markdown", "both"):
            out = write_markdown(result, args.output)
            print(f"  → {out}", file=sys.stderr)

    if args.output and args.format in ("json", "both"):
        out = write_json(results, args.output)
        print(f"  → {out}", file=sys.stderr)

    n_ok = sum(1 for r in results if not r["error"])
    n_err = len(results) - n_ok
    print(f"\nDone: {n_ok} extracted, {n_err} errors.", file=sys.stderr)


if __name__ == "__main__":
    main()