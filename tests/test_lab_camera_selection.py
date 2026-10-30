"""Live selection must recover after tracker identity renewal without stealing a pinned body."""
import math

from harmonic_weaver.lab.contracts import Joint, MotionFrame, Person, Preset
from harmonic_weaver.lab.routing import PreparedRoutes
from harmonic_weaver.lab.runtime import LaboratoryRuntime
from harmonic_weaver.lab.store import SessionStore


class Camera:
    frame = None

    def latest(self):
        return self.frame

    def snapshot(self):
        return {"status": "ready", "error": None}


class Audio:
    def __init__(self):
        self.targets = []
        self.revision = -1

    def submit(self, targets, revision):
        self.targets, self.revision = targets, revision

    def snapshot(self):
        return {"shaper": {"applied_revision": self.revision}, "voice_frame": None}


def frame(now, sequence, identities):
    t = now - 10
    joints = [Joint(index=i, position=[.4 + (i % 2) * .2 + math.sin(t * (1 + i / 30)) * .1,
                                     .2 + (i // 2) * .07 + math.cos(t * 2 + i) * .03],
                    confidence=1, state="observed") for i in range(17)]
    return MotionFrame(source_id="camera-test", stream_id="same-camera-stream", sequence=sequence,
        source_time_s=t, available_monotonic_s=now, captured_monotonic_s=now,
        timestamp_origin="synthetic", width=640, height=480,
        persons=[Person(person_id=identity, joints=joints) for identity in identities])


def setup_runtime(tmp_path, algorithm="baseline"):
    now = [10.]
    store = SessionStore(tmp_path, prepare=PreparedRoutes)
    store.edit(Preset(algorithm={"id": algorithm}, response={"pluck_enabled": False}), 0)
    camera, audio = Camera(), Audio()
    runtime = LaboratoryRuntime(store, camera=camera, audio=audio, library=object(), clock=lambda: now[0])
    runtime.kind = "camera"
    runtime.transport.reset(playing=True)
    return runtime, camera, audio, store, now


def advance(runtime, camera, now, sequence, identities):
    now[0] = 10 + sequence / 30
    camera.frame = frame(now[0], sequence, identities)
    runtime.tick()


def test_automatic_camera_reacquires_renewed_identity_and_resumes_controls(tmp_path):
    runtime, camera, audio, store, now = setup_runtime(tmp_path)
    try:
        for i in range(20):
            advance(runtime, camera, now, i, ["slot-0-generation-1"])
        assert any(target.gain > 0 for target in audio.targets)
        advance(runtime, camera, now, 20, [])
        assert audio.targets == []
        for i in range(21, 42):
            advance(runtime, camera, now, i, ["slot-0-generation-2"])
        assert runtime.person_id == "slot-0-generation-2"
        assert runtime.selection_status == "automatic_changed"
        assert runtime.diagnostic["pose"]["observed"] == 17
        assert any(target.gain > 0 for target in audio.targets)
    finally:
        store.close()


def test_camera_body_change_discards_old_scale_and_history(tmp_path):
    runtime, camera, audio, store, now = setup_runtime(tmp_path, "local")
    try:
        advance(runtime, camera, now, 0, ["old-body"])
        runtime.calibrate()
        for i in range(1, 20):
            advance(runtime, camera, now, i, ["old-body"])
        old_model = runtime.model
        assert runtime.calibration is not None
        advance(runtime, camera, now, 20, ["renewed-body"])
        assert runtime.person_id == "renewed-body"
        assert runtime.calibration is None and runtime.model is not old_model
        assert runtime.diagnostic["code"] == "calibration_required"
        assert not any(target.gain > 0 for target in audio.targets)
    finally:
        store.close()


def test_explicit_camera_selection_stays_pinned_when_other_person_appears(tmp_path):
    runtime, camera, audio, store, now = setup_runtime(tmp_path)
    try:
        advance(runtime, camera, now, 0, ["chosen-body"])
        runtime.select_person("chosen-body")
        advance(runtime, camera, now, 1, [])
        advance(runtime, camera, now, 2, ["other-body"])
        assert runtime.person_id == "chosen-body"
        assert runtime.selection_status == "explicit"
        assert runtime.diagnostic["code"] == "tracking_missing"
        assert audio.targets == []
    finally:
        store.close()


def test_automatic_camera_keeps_current_person_while_still_visible(tmp_path):
    runtime, camera, audio, store, now = setup_runtime(tmp_path)
    try:
        advance(runtime, camera, now, 0, ["chosen-body"])
        advance(runtime, camera, now, 1, ["another-body", "chosen-body"])
        assert runtime.person_id == "chosen-body"
        assert runtime.selection_status == "automatic"
        # An absent or expired frame does not itself select an unrelated identity.
        camera.frame = None
        runtime.tick()
        assert runtime.person_id == "chosen-body"
        advance(runtime, camera, now, 2, [])
        assert runtime.person_id == "chosen-body"
    finally:
        store.close()
