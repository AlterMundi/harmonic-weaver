"""Replay the live LaboratoryRuntime on a fixed control clock, without audio I/O."""
from bisect import bisect_right
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import platform
import subprocess
import tempfile

from pydantic import Field, model_validator
from ..cache import TrackingCache, atomic_json, sha256_file
from ..contracts import Calibration, Contract, Number, Preset
from ..quality import coverage
from ..routing import PreparedRoutes
from ..runtime import LaboratoryRuntime
from ..store import SessionStore


class Source(Contract):
    media_path: str
    cache_manifest: str
    person_id: str
    cache_manifest_sha256: str | None = None
    start_s: Number = Field(default=0, ge=0)
    end_s: Number = Field(gt=0)
    torso_scale: Number | None = Field(default=None, gt=0)
    calibration_provenance: str | None = None

    @model_validator(mode="after")
    def valid_segment(self):
        if self.end_s <= self.start_s:
            raise ValueError("end_s must exceed start_s")
        if self.torso_scale is not None and not self.calibration_provenance:
            raise ValueError("explicit calibration provenance is required")
        return self


class Request(Contract):
    schema_version: int = Field(default=1, ge=1, le=1)
    presets: list[Preset] = Field(min_length=1, max_length=32)
    sources: list[Source] = Field(min_length=1, max_length=32)
    control_hz: int = Field(default=60, ge=10, le=240)
    preroll_s: Number = Field(default=2., ge=0, le=30)

    @model_validator(mode="after")
    def compatible(self):
        if any(p.algorithm.id != "baseline" for p in self.presets):
            if any(s.torso_scale is None for s in self.sources):
                raise ValueError("non-baseline models require explicit calibration for every source")
        return self


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class ReplayAudio:
    def __init__(self):
        self.targets = []
        self.revision = -1

    def submit(self, targets, revision):
        self.targets, self.revision = targets, revision

    def snapshot(self):
        return {"shaper": {"applied_revision": self.revision, "error": None}, "voice_frame": None}

    def close(self):
        pass


class ReplayLibrary:
    def __init__(self, frames, duration):
        self.frames, self.duration = frames, duration
        self.times = [f.source_time_s for f in frames]

    def snapshot(self, job):
        return {"status": "ready", "duration_s": self.duration}

    def frame_at(self, job, position):
        i = bisect_right(self.times, position)-1
        return self.frames[i] if i >= 0 and position <= self.duration else None

    def frames_between(self, job, start, end):
        return self.frames[bisect_right(self.times, start):bisect_right(self.times, end)]

    def close(self):
        pass


def load_source(source, cache):
    path = Path(source.cache_manifest).expanduser().resolve()
    if source.cache_manifest_sha256 and sha256_file(path) != source.cache_manifest_sha256:
        raise ValueError("Frozen cache generation changed; select sources for a new comparison")
    manifest = json.loads(path.read_text())
    # The named manifest must be the generation that is actually read.
    cache._index[manifest["key"]] = str(path)
    track = cache.read(source.media_path, manifest["key"])
    if track is None or track.manifest["frames_sha256"] != manifest["frames_sha256"]:
        raise ValueError("Cache absent, corrupt or changed")
    if sha256_file(source.media_path) != manifest["media_sha256"]:
        raise ValueError("Source video does not match its cache")
    if source.end_s > manifest["duration_s"] + 1e-8:
        raise ValueError("Requested segment exceeds source duration")
    if not any(p.person_id == source.person_id for f in track.frames for p in f.persons):
        raise ValueError("Selected person is absent from source")
    return track


def replay(preset, source, frames, duration, request):
    """Same tick/reset/calibration/model/router as live, on a logical 60 Hz clock."""
    now = [0.]
    audio = ReplayAudio()
    with tempfile.TemporaryDirectory(prefix="weaver-eval-state-") as folder:
        store = SessionStore(Path(folder), prepare=PreparedRoutes)
        store.edit(preset, 0)
        runtime = LaboratoryRuntime(store, library=ReplayLibrary(frames, duration),
                                    audio=audio, clock=lambda: now[0])
        runtime.kind, runtime.job_id, runtime.person_id = "video", "replay", source.person_id
        runtime.selection_status = "explicit"
        if source.torso_scale is not None:
            runtime.calibration = Calibration(source_id=frames[0].source_id, person_id=source.person_id,
                torso_scale=source.torso_scale, measured_at="logical_replay",
                provenance=source.calibration_provenance, policy="reuse_explicit")
        begin = max(0., source.start_s-request.preroll_s)
        runtime.transport.duration_s = duration
        runtime.control(position_s=begin, loop=False, playing=True)
        try:
            count = math.ceil((source.end_s-begin)*request.control_hz)
            for tick in range(count):
                now[0] = tick/request.control_hz
                runtime.tick()
                position = runtime.transport.position()
                if position+1e-9 < source.start_s:
                    continue
                features = runtime.features.model_dump() if runtime.features else None
                # available_monotonic_s is a LOGICAL replay time, not measured latency.
                targets = [asdict(t) for t in audio.targets]
                yield {"tick": tick, "source_time_s": position, "control_time_s": now[0],
                       "features": features, "targets": targets,
                       "diagnostic": runtime.diagnostic, "routing": runtime.routing}
        finally:
            runtime.close()
            store.close()


def code_identity():
    root = Path(__file__).resolve().parents[4]
    files = sorted((root/"src/harmonic_weaver/lab").rglob("*.py"))
    files += sorted((root/"research/movement-consonance/consonance").glob("*.py"))
    hashes = {str(p.relative_to(root)): sha256_file(p) for p in files}
    def git(*args):
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else None
    return {"head": git("rev-parse", "HEAD"), "working_tree": git("status", "--porcelain"),
            "files": hashes, "code_sha256": digest(hashes),
            "python": platform.python_version(), "platform": platform.platform(),
            "packages": {n: importlib.metadata.version(n) for n in ("numpy", "pydantic")}}


def run(request: Request, output: Path, *, progress=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    frozen = request.model_dump()
    atomic_json(output/"request.json", frozen)
    manifest = {"format": 1, "status": "running", "request_sha256": digest(frozen),
                "code": code_identity(), "request": frozen, "seed": 0,
                "clock": "logical_replay", "output_stage": "voice_targets_before_shaper",
                "units": "per FeatureFrame signal; no combined scientific score",
                "source_records": [], "runs": [],
                "limits": ["No PCM/audio rendering or physical latency measurement",
                           "Coverage is availability, not geometric precision",
                           "Private local paths and features: review before sharing"]}
    atomic_json(output/"manifest.json", manifest)
    try:
        cache = TrackingCache(output/".cache-index")
        for source_index, source in enumerate(request.sources):
            track = load_source(source, cache)
            manifest["source_records"].append({"source_index": source_index,
                "cache_manifest_sha256": sha256_file(source.cache_manifest),
                "cache_manifest": track.manifest, "coverage": coverage(track.frames,
                    start_s=source.start_s, end_s=source.end_s, person_id=source.person_id)})
            per_source = []
            for preset_index, preset in enumerate(request.presets):
                name = f"source-{source_index:02d}-preset-{preset_index:02d}.jsonl"
                support, summaries = {}, {}
                gain_sum, sounding, nrows = 0., 0, 0
                with (output/name).open("w") as handle:
                    for row in replay(preset, source, track.frames, track.manifest["duration_s"], request):
                        handle.write(canonical(row)+"\n")
                        nrows += 1
                        active = [t["gain"] for t in row["targets"]]
                        gain_sum += sum(active)
                        sounding += any(g > 1e-6 for g in active)
                        signals = (row["features"] or {}).get("signals", {})
                        for key, signal in signals.items():
                            unit = signal["unit"]
                            entry = summaries.setdefault(key, {"unit": unit, "count": 0, "sum": 0.,
                                "states": {}, "reasons": {}, "gap": 0, "max_gap": 0})
                            if unit != entry["unit"]:
                                raise ValueError("Signal unit changed within a run")
                            state = signal["state"]
                            entry["states"][state] = entry["states"].get(state, 0)+1
                            if state != "observed" or signal["value"] is None:
                                reason = signal.get("reason") or state
                                entry["reasons"][reason] = entry["reasons"].get(reason, 0)+1
                                entry["gap"] += 1
                                entry["max_gap"] = max(entry["max_gap"], entry["gap"])
                                continue
                            entry["gap"] = 0
                            support.setdefault(key, set()).add(row["tick"])
                            entry["count"] += 1
                            entry["sum"] += signal["value"]
                entry = {"source_index": source_index, "preset_index": preset_index, "preset_id": preset.id,
                         "preset_sha256": digest(preset.model_dump()), "file": name,
                         "sha256": sha256_file(output/name), "rows": nrows,
                         "sounding_fraction": sounding/max(1,nrows),
                         "mean_sum_target_gain": gain_sum/max(1,nrows),
                         "signals": {k: {"unit": v["unit"], "observed_count": v["count"],
                                        "mean_available": v["sum"]/v["count"] if v["count"] else None,
                                        "states": v["states"], "invalid_reasons": v["reasons"],
                                        "max_invalid_s_on_control_clock": v["max_gap"]/request.control_hz,
                                        "observed_fraction_on_control_clock": v["count"]/max(nrows, 1)} for k,v in summaries.items()}}
                manifest["runs"].append(entry)
                per_source.append((entry, support))
                atomic_json(output/"manifest.json", manifest)
                if progress:
                    progress(len(manifest["runs"]), len(request.sources)*len(request.presets))
            common = set.intersection(*(set(support) for _, support in per_source)) if per_source else set()
            comparisons, common_ticks = {}, {}
            for signal in sorted(common):
                units = {entry["signals"][signal]["unit"] for entry, _ in per_source}
                if len(units) != 1:
                    continue
                ticks = set.intersection(*(support[signal] for _, support in per_source))
                common_ticks[signal] = ticks
                comparisons[signal] = {"unit": next(iter(units)), "common_count": len(ticks),
                    "common_ticks_sha256": digest(sorted(ticks)), "means_same_support": []}
            for entry, _ in per_source:
                sums = {signal: 0. for signal in comparisons}
                with (output/entry["file"]).open() as handle:
                    for line in handle:
                        row = json.loads(line)
                        signals = (row["features"] or {}).get("signals", {})
                        for signal, ticks in common_ticks.items():
                            if row["tick"] in ticks:
                                sums[signal] += signals[signal]["value"]
                for signal, stats in comparisons.items():
                    count = stats["common_count"]
                    stats["means_same_support"].append(sums[signal]/count if count else None)
            atomic_json(output/f"comparison-{source_index:02d}.json",
                        {"source_index": source_index, "signals": comparisons,
                         "warning": "Descriptive comparison, not prediction gain or efficacy"})
        manifest["status"] = "complete"
        manifest["comparison_hashes"] = {p.name: sha256_file(p) for p in output.glob("comparison-*.json")}
        atomic_json(output/"manifest.json", manifest)
        return manifest
    except Exception as exc:
        manifest["status"], manifest["error"] = "failed", str(exc)
        atomic_json(output/"manifest.json", manifest)
        raise
