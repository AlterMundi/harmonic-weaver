"""Transactional presets and light session journal; never stores live observations."""
from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import threading
import time
from typing import Callable

from .contracts import Calibration, Preset, SessionEvent, SessionState


class RevisionConflict(ValueError):
    pass


def _json(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def _macro_field(data, path):
    """Walk numeric configuration fields, not Python expressions or object attributes."""
    parts = path.split(".")
    if parts[0] not in {"fundamental_hz", "master", "release_ms", "algorithm", "response", "voices", "routes", "visual"}:
        raise ValueError(f"macro path is not a configurable field: {path}")
    owner = data
    try:
        for part in parts[:-1]:
            owner = owner[int(part)] if isinstance(owner, list) else owner[part]
        key = int(parts[-1]) if isinstance(owner, list) else parts[-1]
        value = owner[key]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid macro path: {path}") from exc
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"macro target must be numeric: {path}")
    # IDs and schema versions are numeric but not continuously adjustable.
    if str(key) in {"id", "version", "schema_version", "voice"}:
        raise ValueError(f"macro target is an identifier: {path}")
    return owner, key


def validate_macros(preset: Preset):
    data = preset.model_dump()
    for macro in preset.macros:
        for target in macro.targets:
            owner, key = _macro_field(data, target.path)
            original = owner[key]
            for bound in (target.minimum, target.maximum):
                owner[key] = int(bound) if isinstance(original, int) and bound.is_integer() else bound
                Preset.model_validate(data)
            owner[key] = original


class SessionStore:
    def __init__(self, data_dir: Path, *, prepare: Callable | None = None):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._db = sqlite3.connect(self.data_dir / "laboratory.sqlite3", check_same_thread=False)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.executescript("""
            CREATE TABLE IF NOT EXISTS presets (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS settings (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS calibrations (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events (sequence INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL);
        """)
        self.prepare = prepare or (lambda preset: None)
        row = self._db.execute("SELECT payload FROM settings WHERE id='configuration'").fetchone()
        stored = json.loads(row[0]) if row else None
        self.preset = Preset.model_validate(stored["preset"]) if stored else Preset()
        self.prepared = self._prepare(self.preset)
        revision = stored["revision"] if stored else 0
        self.state = SessionState(desired_revision=revision)
        self._undo: list[Preset] = []
        self._redo: list[Preset] = []

    def _prepare(self, preset):
        validate_macros(preset)
        return self.prepare(preset.model_copy(deep=True))

    def close(self):
        with self._lock:
            self._db.close()

    def _event(self, kind, payload, revision=None):
        event = SessionEvent(session_id=self.state.session_id,
                             monotonic_s=time.monotonic(), source_time_s=self.state.position_s,
                             kind=kind, revision=self.state.desired_revision if revision is None else revision,
                             payload={"source_id": self.state.source_id, "person_id": self.state.person_id,
                                      "calibration_id": self.state.calibration_id, **payload})
        self._db.execute("INSERT INTO events(payload) VALUES (?)", (event.model_dump_json(),))

    def snapshot(self):
        with self._lock:
            return {"preset": self.preset.model_dump(), "session": self.state.model_dump(),
                    "can_undo": bool(self._undo), "can_redo": bool(self._redo)}

    def configuration(self):
        with self._lock:
            return self.preset.model_copy(deep=True), self.state.desired_revision, self.prepared

    def analysis_epoch(self):
        with self._lock:
            return self.state.analysis_epoch

    def edit(self, preset: Preset, expected_revision: int, *, reason="edit", history=True):
        prepared = self._prepare(preset)  # potentially costly compile outside producer lock
        with self._lock:
            if expected_revision != self.state.desired_revision:
                raise RevisionConflict(f"expected revision {expected_revision}, current {self.state.desired_revision}")
            revision = expected_revision + 1
            with self._db:
                self._db.execute("INSERT OR REPLACE INTO settings(id,payload) VALUES ('configuration',?)",
                                 (_json({"preset": preset.model_dump(), "revision": revision}),))
                self._event("configuration", {"reason": reason, "preset": preset.model_dump()}, revision)
            if history:
                self._undo.append(self.preset.model_copy(deep=True))
                self._undo = self._undo[-100:]
                self._redo.clear()
            self.preset = preset.model_copy(deep=True)
            self.prepared = prepared
            self.state.desired_revision = revision
            if reason == "preset_apply":
                self.state.analysis_epoch += 1
            return self.snapshot()

    def history(self, expected_revision: int, *, redo=False):
        with self._lock:
            if expected_revision != self.state.desired_revision:
                raise RevisionConflict("configuration changed in another client")
            source, target = (self._redo, self._undo) if redo else (self._undo, self._redo)
            if not source:
                raise ValueError("history is empty")
            current = self.preset.model_copy(deep=True)
            result = self.edit(source[-1], expected_revision, reason="redo" if redo else "undo", history=False)
            source.pop()
            target.append(current)
            return self.snapshot()

    def apply_macro(self, macro_id, value, expected_revision):
        with self._lock:
            if expected_revision != self.state.desired_revision:
                raise RevisionConflict("configuration changed in another client")
            data = self.preset.model_dump()
        macro = next((m for m in data["macros"] if m["id"] == macro_id), None)
        if macro is None:
            raise ValueError("unknown macro")
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not 0 <= value <= 1:
            raise ValueError("macro value must be 0..1")
        macro["value"] = value
        for target in macro["targets"]:
            owner, key = _macro_field(data, target["path"])
            result = target["minimum"] + value * (target["maximum"] - target["minimum"])
            owner[key] = round(result) if isinstance(owner[key], int) else result
        return self.edit(Preset.model_validate(data), expected_revision, reason=f"macro:{macro_id}")

    def set_runtime(self, **fields):
        with self._lock:
            # Revalidate updates: Pydantic model_copy(update=...) itself does not validate.
            self.state = SessionState.model_validate({**self.state.model_dump(), **fields})

    def remember_video(self, video):
        """Session-local source preference, deliberately outside portable presets."""
        with self._lock, self._db:
            self._db.execute("INSERT OR REPLACE INTO settings(id,payload) VALUES ('last_video',?)",
                             (_json(video),))

    def last_video(self):
        with self._lock:
            row = self._db.execute("SELECT payload FROM settings WHERE id='last_video'").fetchone()
            return json.loads(row[0]) if row else None

    def list_presets(self):
        with self._lock:
            presets = [Preset.model_validate_json(row[0]).model_dump()
                       for row in self._db.execute("SELECT payload FROM presets ORDER BY id")]
            return sorted(presets, key=lambda p: (not p["favorite"], p["name"].casefold()))

    def save(self, preset: Preset):
        self._prepare(preset)
        with self._lock, self._db:
            self._db.execute("INSERT OR REPLACE INTO presets(id,payload) VALUES (?,?)",
                             (preset.id, preset.model_dump_json()))
            self._event("preset_save", {"preset_id": preset.id, "name": preset.name})
        return preset.model_dump()

    def load(self, preset_id):
        with self._lock:
            row = self._db.execute("SELECT payload FROM presets WHERE id=?", (preset_id,)).fetchone()
        if row is None:
            raise KeyError(preset_id)
        return Preset.model_validate_json(row[0])

    def save_calibration(self, calibration: Calibration):
        with self._lock, self._db:
            self._db.execute("INSERT OR REPLACE INTO calibrations(id,payload) VALUES (?,?)",
                             (calibration.id, calibration.model_dump_json()))
            self._event("calibration", {"calibration_id": calibration.id, "source_id": calibration.source_id})

    def calibrations(self):
        with self._lock:
            return [Calibration.model_validate_json(r[0]).model_dump()
                    for r in self._db.execute("SELECT payload FROM calibrations ORDER BY id")]

    def mark(self, text):
        if not isinstance(text, str) or not 1 <= len(text) <= 500:
            raise ValueError("mark must have 1..500 characters")
        with self._lock, self._db:
            self._event("mark", {"text": text, "preset_id": self.preset.id})

    def events(self, limit=100):
        with self._lock:
            return [json.loads(r[0]) for r in self._db.execute(
                "SELECT payload FROM events ORDER BY sequence DESC LIMIT ?", (min(max(limit, 1), 1000),))]
