"""Shared helpers for train/test split filtering in evaluation scripts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


DEFAULT_SPLIT_FILE = Path("project_context/eval_split.json")
SPLIT_CHOICES = ("all", "train", "test")


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


def case_sort_key(case_id: str) -> tuple[int, str]:
    number_match = re.search(r"(\d+)", case_id)
    if number_match:
        return int(number_match.group(1)), case_id
    return 10**9, case_id


def record_case_id(record: dict[str, Any]) -> str:
    return normalize_case_id(record.get("case_id") or record.get("paper_number"))


def load_split_case_ids(split_file: Path, split: str) -> set[str] | None:
    if split == "all":
        return None
    if split not in SPLIT_CHOICES:
        raise ValueError(f"Unsupported split {split!r}; expected one of {SPLIT_CHOICES}.")
    if not split_file.exists():
        raise FileNotFoundError(f"Split file does not exist: {split_file}")

    data = json.loads(split_file.read_text(encoding="utf-8"))
    key = f"{split}_case_ids"
    case_ids = {normalize_case_id(value) for value in data.get(key, [])}
    case_ids.discard("")
    if not case_ids:
        raise ValueError(f"Split file {split_file} has no {key}.")
    return case_ids


def filter_records_by_case_ids(records: list[dict[str, Any]], case_ids: set[str] | None) -> list[dict[str, Any]]:
    if case_ids is None:
        return records
    return [record for record in records if record_case_id(record) in case_ids]


def sorted_case_ids(case_ids: set[str] | list[str]) -> list[str]:
    return sorted(case_ids, key=case_sort_key)
