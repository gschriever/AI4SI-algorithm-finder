"""Create a deterministic train/test split for AI4SI method-label evaluation.

Create this split before tuning prompts, mappings, or judge settings. Use the
train split for iteration and keep the test split untouched for the final match
rate.

Usage:
    python scripts/split_gold_labels.py
    python scripts/split_gold_labels.py --test-size 0.3 --seed 42
"""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from typing import Any

from eval_split_utils import DEFAULT_SPLIT_FILE, normalize_case_id, sorted_case_ids


DEFAULT_GOLD = Path("project_context/gold_method_labels.jsonl")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def test_count_for_size(n: int, test_size: float) -> int:
    if n <= 1:
        return n
    if 0 < test_size < 1:
        count = math.ceil(n * test_size)
    else:
        count = int(test_size)
    return max(1, min(n - 1, count))


def build_split(records: list[dict[str, Any]], test_size: float, seed: int) -> dict[str, Any]:
    case_ids = {
        normalize_case_id(record.get("case_id") or record.get("paper_number"))
        for record in records
    }
    case_ids.discard("")
    if len(case_ids) != len(records):
        raise ValueError("Gold labels must have one unique non-empty case_id per record.")

    shuffled = sorted_case_ids(case_ids)
    random.Random(seed).shuffle(shuffled)

    test_count = test_count_for_size(len(shuffled), test_size)
    test_case_ids = set(shuffled[:test_count])
    train_case_ids = set(shuffled[test_count:])

    return {
        "seed": seed,
        "test_size": test_size,
        "n_total": len(shuffled),
        "n_train": len(train_case_ids),
        "n_test": len(test_case_ids),
        "train_case_ids": sorted_case_ids(train_case_ids),
        "test_case_ids": sorted_case_ids(test_case_ids),
        "protocol": "Tune prompts, mappings, and judge settings on train only; report final match rate on test.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a deterministic AI4SI train/test split.")
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD, help="Gold-label JSONL input.")
    parser.add_argument("--output", "-o", type=Path, default=DEFAULT_SPLIT_FILE, help="Split JSON output.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed used for deterministic shuffling.")
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.3,
        help="Held-out size as a fraction in (0, 1) or an absolute case count.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = load_jsonl(args.gold)
    split = build_split(records, test_size=args.test_size, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(split, indent=2) + "\n", encoding="utf-8")
    print(
        f"Wrote split to {args.output}: "
        f"{split['n_train']} train / {split['n_test']} test cases"
    )


if __name__ == "__main__":
    main()
