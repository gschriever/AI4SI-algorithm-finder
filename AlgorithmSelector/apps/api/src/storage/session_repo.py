from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from models.session import SessionState


class SessionRepository:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or Path(__file__).resolve().parents[4] / "data" / "sessions"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_stage(self, session_id: str, stage: str, model: BaseModel) -> None:
        session_dir = self._session_dir(session_id)
        (session_dir / f"{stage}.json").write_text(model.model_dump_json(indent=2))

    def save_state(self, state: SessionState) -> None:
        session_dir = self._session_dir(state.session_id)
        (session_dir / "session_state.json").write_text(state.model_dump_json(indent=2))

    def load_state(self, session_id: str) -> SessionState:
        session_dir = self._session_dir(session_id)
        path = session_dir / "session_state.json"
        return SessionState.model_validate(json.loads(path.read_text()))

    def has_state(self, session_id: str) -> bool:
        return (self._session_dir(session_id) / "session_state.json").exists()

    def _session_dir(self, session_id: str) -> Path:
        session_dir = self.base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir
