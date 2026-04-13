from __future__ import annotations

from pathlib import Path

import yaml


BASE_DIR = Path(__file__).resolve().parents[1]
POLICIES_DIR = BASE_DIR / "policies"


class PolicyLoader:
    def load(self, name: str) -> dict:
        path = POLICIES_DIR / name
        return yaml.safe_load(path.read_text())
