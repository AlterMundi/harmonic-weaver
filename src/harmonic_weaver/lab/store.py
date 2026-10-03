"""Transactional presets and light session journal; never stores live observations."""
from __future__ import annotations

import json
import math
from hashlib import sha256
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
    if parts[0] not in {"fundamental_hz", "master", "expression", "expression_window_s", "transient_mix", "transient_decay_s", "release_ms", "algorithm", "response", "voices", "routes", "visual"}:
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

    def record_event(self, kind, payload):
        with self._lock, self._db:
            self._event(kind, payload)

    def event_boundary(self):
        with self._lock:
            cursor = self._db.execute("SELECT COALESCE(MAX(sequence),0) FROM events").fetchone()[0]
            return {"cursor": cursor, "state": self.snapshot(), "calibrations": self.calibrations()}

    def events_since(self, cursor, limit=256):
        with self._lock:
            rows = self._db.execute("SELECT sequence,payload FROM events WHERE sequence>? ORDER BY sequence LIMIT ?",
                                    (cursor,min(max(limit,1),1000))).fetchall()
            return [{"sequence":seq,"event":json.loads(payload)} for seq,payload in rows]

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

    def source_preferences(self):
        with self._lock:
            row = self._db.execute("SELECT payload FROM settings WHERE id='source_preferences'").fetchone()
            defaults = {"default_person": "best_coverage", "autoplay_video": True}
            return {**defaults, **json.loads(row[0])} if row else defaults

    def set_source_preferences(self, preferences):
        with self._lock, self._db:
            self._db.execute("INSERT OR REPLACE INTO settings(id,payload) VALUES ('source_preferences',?)",
                             (_json(preferences),))
        return preferences

    def source_selection(self, media_id):
        """A local explicit choice, scoped to one immutable tracking generation."""
        with self._lock:
            row = self._db.execute("SELECT payload FROM settings WHERE id=?",
                                   (f"source_selection:{media_id}",)).fetchone()
            return json.loads(row[0]) if row else None

    def remember_source_selection(self, media_id, cache_key, generation, person_id):
        if not all((media_id, cache_key, generation, person_id)):
            raise ValueError("A completed tracking generation and person are required")
        selection = dict(media_id=media_id, cache_key=cache_key, generation=generation,
                         person_id=person_id)
        with self._lock, self._db:
            self._db.execute("INSERT OR REPLACE INTO settings(id,payload) VALUES (?,?)",
                             (f"source_selection:{media_id}", _json(selection)))
            self._event("mark", {"text": "Selección explícita de cuerpo",
                                 "source_selection": selection})
        return selection

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

    def list_capture_profiles(self):
        from .capture_profiles import CaptureProfile
        with self._lock:
            rows=self._db.execute("SELECT payload FROM settings WHERE id LIKE 'capture_profile:%'").fetchall()
        return sorted([CaptureProfile.model_validate_json(row[0]).model_dump() for row in rows],
                      key=lambda p:(p['name'].casefold(),p['id']))

    def save_capture_profile(self, profile):
        from .capture_profiles import CaptureProfile
        profile=CaptureProfile.model_validate(profile)
        with self._lock, self._db:
            self._db.execute("INSERT OR REPLACE INTO settings(id,payload) VALUES (?,?)",
                             ('capture_profile:'+profile.id,profile.model_dump_json()))
        return profile.model_dump()

    def load_capture_profile(self, ident):
        from .capture_profiles import CaptureProfile
        with self._lock:
            row=self._db.execute("SELECT payload FROM settings WHERE id=?",('capture_profile:'+ident,)).fetchone()
        if row is None:raise KeyError(ident)
        return CaptureProfile.model_validate_json(row[0])

    def save_calibration(self, calibration: Calibration):
        with self._lock, self._db:
            self._db.execute("INSERT OR REPLACE INTO calibrations(id,payload) VALUES (?,?)",
                             (calibration.id, calibration.model_dump_json()))
            self._event("calibration", {"calibration_id": calibration.id, "source_id": calibration.source_id,
                                       "calibration": calibration.model_dump()})

    def list_evaluation_profiles(self):
        from .evaluation.profiles import EvaluationProfile
        with self._lock:
            rows=self._db.execute("SELECT payload FROM settings WHERE id LIKE 'evaluation_profile:%'").fetchall()
        return sorted([EvaluationProfile.model_validate_json(row[0]).model_dump() for row in rows],
                      key=lambda p:(p['name'].casefold(),p['id']))

    def save_evaluation_profile(self,profile):
        from .evaluation.profiles import EvaluationProfile
        profile=EvaluationProfile.model_validate(profile)
        with self._lock,self._db:
            self._db.execute('INSERT OR REPLACE INTO settings(id,payload) VALUES (?,?)',
                             ('evaluation_profile:'+profile.id,profile.model_dump_json()))
        return profile.model_dump()

    def load_evaluation_profile(self,ident):
        from .evaluation.profiles import EvaluationProfile
        with self._lock:
            row=self._db.execute('SELECT payload FROM settings WHERE id=?',('evaluation_profile:'+ident,)).fetchone()
        if row is None:raise KeyError(ident)
        return EvaluationProfile.model_validate_json(row[0])

    def calibrations(self):
        with self._lock:
            return [Calibration.model_validate_json(r[0]).model_dump()
                    for r in self._db.execute("SELECT payload FROM calibrations ORDER BY id")]

    def mark(self, text, *, category="note", observed_epoch=None, transport_epoch=None, frame_time_s=None, source_identity=None):
        if category not in ("note","preparation","deployment","release","experience"):
            raise ValueError("Unknown mark category")
        if not isinstance(text, str) or not 1 <= len(text) <= 500:
            raise ValueError("mark must have 1..500 characters")
        with self._lock, self._db:
            self._event("mark", {"text": text, "preset_id": self.preset.id,
                                 "annotation_category": category, "annotation_origin": "human_button",
                                 "timing_basis": "latest_observed_source_time",
                                 "reaction_latency_corrected": False,
                                 "observed_epoch": observed_epoch, "transport_epoch": transport_epoch,
                                 "frame_time_s": frame_time_s, "source_identity":source_identity})

    def marks_snapshot(self, *, source_id=None, person_id=None, start_s=None, end_s=None, category=None, session_id=None, observed_epoch=None, through_sequence=None):
        if through_sequence is not None and (type(through_sequence) is not int or through_sequence<0):
            raise ValueError("Mark cursor requires a nonnegative integer")
        if observed_epoch is not None and (type(observed_epoch) is not int or observed_epoch<0 or not session_id):
            raise ValueError("Observed epoch requires an explicit session and nonnegative integer")
        for value in (start_s,end_s):
            if value is not None and (type(value) not in (int,float) or not math.isfinite(value) or value<0):
                raise ValueError("Mark interval requires finite nonnegative times")
        if start_s is not None and end_s is not None and start_s>=end_s:
            raise ValueError("Mark interval end must follow start")
        if category is not None and category not in ("note","preparation","deployment","release","experience"):
            raise ValueError("Unknown mark category")
        with self._lock:
            cursor=self._db.execute("SELECT COALESCE(MAX(sequence),0) FROM events").fetchone()[0]
            if through_sequence is not None:
                if through_sequence>cursor:raise ValueError("Mark cursor is beyond the recorded journal")
                cursor=through_sequence
            rows=self._db.execute("SELECT sequence,payload FROM events WHERE sequence<=? AND json_extract(payload,'$.kind')='mark' ORDER BY sequence",(cursor,)).fetchall()
            result={"schema_version":1,"through_sequence":cursor,
                    "selection":{"source_id":source_id,"person_id":person_id,"start_s":start_s,"end_s":end_s,"category":category,"interval":"[start_s,end_s)","session_id":session_id,"observed_epoch":observed_epoch},
                    "marks":[{"sequence":seq,"event":event} for seq,payload in rows
                             if (event:=json.loads(payload)) is not None
                             and (source_id is None or event['payload'].get('source_id')==source_id)
                             and (person_id is None or event['payload'].get('person_id')==person_id)
                             and (session_id is None or event['session_id']==session_id)
                             and (observed_epoch is None or event['payload'].get('observed_epoch')==observed_epoch)
                             and (category is None or event['payload'].get('annotation_category')==category)
                             and (start_s is None or event.get('source_time_s') is not None and event['source_time_s']>=start_s)
                             and (end_s is None or event.get('source_time_s') is not None and event['source_time_s']<end_s)],
                    "limits":["Button timestamps are not reaction-corrected movement onsets",
                              "Includes historical and system marks; annotation_origin distinguishes typed human marks",
                              "Local export may contain private text and source/person context"]}
            canonical=json.dumps(result,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
            return {**result,"content_sha256":sha256(canonical).hexdigest()}

    def events(self, limit=100):
        with self._lock:
            return [json.loads(r[0]) for r in self._db.execute(
                "SELECT payload FROM events ORDER BY sequence DESC LIMIT ?", (min(max(limit, 1), 1000),))]
