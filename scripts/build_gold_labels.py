"""Build gold method-label data from sources/sources_index.md.

The output is intended for evaluation only. Do not feed these gold labels
into the project classifier; they contain the paper's method/algorithm.

Usage:
    python scripts/build_gold_labels.py
    python scripts/build_gold_labels.py --output project_context/gold_method_labels.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_SOURCE_INDEX = Path("sources/sources_index.md")
DEFAULT_OUTPUT = Path("project_context/gold_method_labels.jsonl")


PAPER_HEADING_RE = re.compile(r"^## Paper\s+(\d+):\s+(.+?)\s*$", re.MULTILINE)
FIELD_RE = re.compile(r"^-\s+\*\*(.+?):\*\*\s*(.*)$")


def parse_sources_index(path: Path) -> list[dict[str, Any]]:
    content = path.read_text(encoding="utf-8")
    matches = list(PAPER_HEADING_RE.finditer(content))
    records: list[dict[str, Any]] = []

    for index, match in enumerate(matches):
        paper_number = int(match.group(1))
        title = _clean_markdown(match.group(2))
        block_start = match.end()
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        block = content[block_start:block_end]
        fields = _parse_fields(block)

        optimization_type = fields.get("Optimization Type", "")
        key_method = fields.get("Key Method", "")
        gold_classification = " --- ".join(part for part in [optimization_type, key_method] if part)

        records.append(
            {
                "case_id": f"paper_{paper_number:02d}",
                "paper_number": paper_number,
                "title": title,
                "authors": fields.get("Authors", ""),
                "venue": fields.get("Venue", ""),
                "local_file": fields.get("Local File", ""),
                "social_problem": fields.get("Social Problem(s)", ""),
                "gold_optimization_type": optimization_type,
                "gold_key_method": key_method,
                "gold_classification": gold_classification,
            }
        )

    return records


def _parse_fields(block: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in block.splitlines():
        match = FIELD_RE.match(line.strip())
        if not match:
            continue
        key = match.group(1).strip()
        value = _clean_markdown(match.group(2).strip())
        fields[key] = value
    return fields


def _clean_markdown(value: str) -> str:
    value = value.replace("⚠️", "").replace("✅", "")
    value = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", value)
    value = value.replace("**", "").replace("`", "")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def write_records(records: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix == ".json":
        output_path.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return

    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build gold method labels from the AI4SI sources index.")
    parser.add_argument("--source-index", type=Path, default=DEFAULT_SOURCE_INDEX, help="Path to sources_index.md.")
    parser.add_argument("--output", "-o", type=Path, default=DEFAULT_OUTPUT, help="Output .jsonl or .json path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = parse_sources_index(args.source_index)
    write_records(records, args.output)
    print(f"Wrote {len(records)} gold labels to {args.output}")


if __name__ == "__main__":
    main()
