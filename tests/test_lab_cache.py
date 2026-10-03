import json
from pathlib import Path
import threading

import pytest

from harmonic_weaver.lab.cache import CacheCancelled, TrackingCache, cache_identity, sha256_file
from harmonic_weaver.lab.contracts import MotionFrame, PerceptionSettings


def inputs(tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"synthetic-media-identity")
    model = tmp_path / "model.pt"
    model.write_bytes(b"synthetic-model-identity")
    settings = PerceptionSettings(checkpoint=str(model))
    key, metadata = cache_identity(sha256_file(video), settings, {"version": 1})
    frames = [MotionFrame(source_id=metadata["media_sha256"], stream_id="first", sequence=i,
                          source_time_s=t, source_pts=pts, time_base_num=1, time_base_den=1000,
                          available_monotonic_s=10.+i, timestamp_origin="pts", width=640, height=480)
              for i, (t, pts) in enumerate([(0., 0), (.037, 37), (.094, 94)])]
    return video, model, settings, key, metadata, frames


def test_cache_roundtrip_reopen_rename_and_vfr(tmp_path):
    video, model, settings, key, metadata, frames = inputs(tmp_path)
    cache = TrackingCache(tmp_path / "data")
    saved = cache.write(video, key, metadata, iter(frames))
    assert saved.manifest_path.parent == Path(str(video) + ".weaver-cache")
    assert [f.source_time_s for f in saved.frames] == [0., .037, .094]
    assert [f.source_pts for f in saved.frames] == [0, 37, 94]
    renamed = video.with_name("renamed.mp4")
    video.rename(renamed)
    reopened = TrackingCache(tmp_path / "data").read(renamed, key)
    assert reopened is not None and reopened.frames == frames
    assert reopened.manifest["frames_sha256"] == saved.manifest["frames_sha256"]
    # Identity ignores path, camera-only fields and any musical preset.
    moved_model = model.with_name("renamed-model.pt")
    model.rename(moved_model)
    settings.checkpoint = str(moved_model)
    settings.camera_width = 640
    assert cache_identity(sha256_file(renamed), settings, {"version": 1})[0] == key


def test_model_settings_source_and_extractor_invalidate(tmp_path):
    video, model, settings, key, metadata, frames = inputs(tmp_path)
    assert cache_identity(sha256_file(video), settings, {"version": 2})[0] != key
    settings.imgsz = 640
    assert cache_identity(sha256_file(video), settings, {"version": 1})[0] != key
    settings.imgsz = 320
    model.write_bytes(b"new-weights")
    assert cache_identity(sha256_file(video), settings, {"version": 1})[0] != key
    model.write_bytes(b"synthetic-model-identity")
    video.write_bytes(b"new-content")
    assert cache_identity(sha256_file(video), settings, {"version": 1})[0] != key


def test_cancel_force_and_failure_keep_previous_generation(tmp_path):
    video, _, _, key, metadata, frames = inputs(tmp_path)
    cache = TrackingCache(tmp_path / "data")
    previous = cache.write(video, key, metadata, frames)
    cancel = threading.Event()
    with pytest.raises(CacheCancelled):
        cache.write(video, key, metadata, frames, cancel=cancel,
                    progress=lambda frame, count: cancel.set())
    assert cache.read(video, key).manifest == previous.manifest
    with pytest.raises(ValueError, match="regressing"):
        cache.write(video, key, metadata, list(reversed(frames)))
    assert cache.read(video, key).manifest == previous.manifest
    newer = cache.write(video, key, metadata, frames)
    assert newer.manifest["generation"] != previous.manifest["generation"]
    assert (previous.manifest_path.parent / previous.manifest["frames_file"]).exists()
    assert not list(previous.manifest_path.parent.glob("*.partial"))


def test_corruption_and_read_only_sidecar_fallback(tmp_path):
    video, _, _, key, metadata, frames = inputs(tmp_path)
    cache = TrackingCache(tmp_path / "data")
    sidecar = Path(str(video) + ".weaver-cache")
    sidecar.mkdir()
    sidecar.chmod(0o555)
    try:
        saved = cache.write(video, key, metadata, frames)
    finally:
        sidecar.chmod(0o755)
    assert saved.manifest_path.parent == cache.root
    data = saved.manifest_path.parent / saved.manifest["frames_file"]
    data.write_text("corrupted")
    assert cache.read(video, key) is None
    assert "checksum" in cache.last_problem


def test_manifest_cannot_escape_cache_directory(tmp_path):
    video, _, _, key, metadata, frames = inputs(tmp_path)
    cache = TrackingCache(tmp_path / "data")
    track = cache.write(video, key, metadata, frames)
    manifest = track.manifest.copy()
    manifest["frames_file"] = "../private.jsonl"
    track.manifest_path.write_text(json.dumps(manifest))
    assert cache.read(video, key) is None
    assert "invalid frames path" in cache.last_problem
