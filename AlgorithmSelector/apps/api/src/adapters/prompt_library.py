from __future__ import annotations

from pathlib import Path

import yaml


PROMPTS_FILE = Path(__file__).resolve().parents[1] / "prompt_library.yaml"


class PromptLibrary:
    def __init__(self, prompt_file: Path = PROMPTS_FILE) -> None:
        self._templates = yaml.safe_load(prompt_file.read_text())

    def get(self, name: str) -> str:
        return self._templates[name]
