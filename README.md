# AI4SI Algorithm Finder

A centralized repository containing a curated research library and problem space mapping framework for Artificial Intelligence for Social Impact (AI4SI).

## Repository Structure

- `sources/`: The raw PDF papers that comprise our rigorously verified, optimization-focused research library (31 curated sources) and the master `sources_index.md`.
- `project_context/`: Extracted texts, framework notes, and planning documents outlining the socio-technical layers.
- `scripts/`: Automation scripts used to systematically process library data.
  - `extract_context.py`: Uses Gemini LLM to extract structured problem context directly from paper PDFs.
  - `generate_context_extraction.py`: Generates the master Markdown extraction table from `sources/sources_index.md`.

## Evaluation: LLM-As-Judge Match Rate

The evaluation setup keeps paper methods hidden during project prediction, then compares the project classification against gold method labels from `sources/sources_index.md`.

Build the gold-label file:

```bash
python scripts/build_gold_labels.py
```

Create the train/test split before prompt or mapping work:

```bash
python scripts/split_gold_labels.py --test-size 0.3 --seed 42
```

Use the train split while iterating. Keep the test split untouched for the final reported match rate.

Prepare a project prediction file as JSONL. The minimum shape is:

```json
{"case_id": "paper_05", "project_classification": "restless_multi_armed_bandit"}
```

The judge script also understands API-shaped records that include `artifacts.recommendation.recommended_method_family` or `artifacts.ranking.ranked_methods[0].method_family`.

To generate fixture-mode predictions for the held-out test contexts:

```bash
python scripts/run_project_predictions.py \
  --split-file project_context/eval_split.json \
  --split test \
  --output project_context/project_predictions_test_fixture.jsonl
```

Run the judge with Gemini:

```bash
export GEMINI_API_KEY=your_key_here
python scripts/judge_method_predictions.py \
  --predictions project_context/project_predictions_test_fixture.jsonl \
  --split-file project_context/eval_split.json \
  --split test \
  --provider gemini \
  --output project_context/judge_results_test_gemini.jsonl \
  --summary-output project_context/judge_summary_test_gemini.json
```

Or with an OpenAI-compatible chat-completions endpoint:

```bash
export OPENAI_API_KEY=your_key_here
python scripts/judge_method_predictions.py \
  --predictions project_context/project_predictions_test_fixture.jsonl \
  --split-file project_context/eval_split.json \
  --split test \
  --provider openai_compatible \
  --output project_context/judge_results_test_openai.jsonl \
  --summary-output project_context/judge_summary_test_openai.json
```

For an offline smoke test without an LLM, use the deterministic fixture judge. This validates the data plumbing only; it is not a real LLM-as-judge score.

```bash
python scripts/judge_method_predictions.py \
  --predictions project_context/project_predictions_test_fixture.jsonl \
  --split-file project_context/eval_split.json \
  --split test \
  --provider fixture \
  --output project_context/judge_results_test_fixture.jsonl \
  --summary-output project_context/judge_summary_test_fixture.json
```

Outputs:

- `project_context/eval_split.json`: frozen train/test case IDs.
- `project_context/judge_results_*.jsonl`: per-paper score, match boolean, and short reason.
- `project_context/judge_summary_*.json`: average semantic match score and binary match rate at the default `0.75` threshold.
