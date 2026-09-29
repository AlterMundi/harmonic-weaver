from harmonic_weaver.lab.contracts import Preset
from harmonic_weaver.lab.routing import PreparedRoutes
from harmonic_weaver.lab.runtime import LaboratoryRuntime
from harmonic_weaver.lab.store import SessionStore
from test_lab_models import observation


class Audio:
    def __init__(self):
        self.targets, self.revision = [], -1

    def submit(self, targets, revision):
        self.targets, self.revision = targets, revision

    def snapshot(self):
        return {"shaper":{"applied_revision": self.revision}, "voice_frame":None}


class Library:
    def __init__(self):
        self.frames = [observation(i/30, i, missing=45 <= i < 50) for i in range(90)]
        self.read_ranges = []

    def snapshot(self, job):
        return {"status":"ready", "duration_s":3.}

    def frame_at(self, job, position):
        return next((f for f in reversed(self.frames) if f.source_time_s <= position), None)

    def frames_between(self, job, start, end):
        self.read_ranges.append((start,end))
        return [f for f in self.frames if start < f.source_time_s <= end]


def test_replay_pause_gap_loop_and_configuration_do_not_replay_old_events(tmp_path):
    now = [0.]
    store = SessionStore(tmp_path, prepare=PreparedRoutes)
    preset = Preset(algorithm={"id":"local"}, response={"pluck_enabled":False})
    store.edit(preset, 0)
    audio, library = Audio(), Library()
    runtime = LaboratoryRuntime(store, audio=audio, library=library, clock=lambda:now[0])
    runtime.kind, runtime.job_id = "video", "test"
    runtime.tick()
    runtime.calibrate()
    runtime.control(playing=True)
    for i in range(40):
        now[0] = i/30
        runtime.tick()
    assert any(v.gain > 0 for v in audio.targets)
    model = runtime.model
    preset.master = .2
    store.edit(preset, 1)
    now[0] += .01
    runtime.tick()
    assert runtime.model is model  # a gain edit must not clear motion history
    assert audio.revision == 2
    runtime.control(playing=False)
    assert audio.targets == []
    runtime.tick()
    assert audio.targets == []
    runtime.control(playing=True)
    for i in range(41, 65):
        now[0] = i/30
        runtime.tick()
    assert all(end-start < .1 for start,end in library.read_ranges)
    assert any(v.gain > 0 for v in audio.targets)
    runtime.control(position_s=.1)
    runtime.tick()
    assert not any(v.gain for v in audio.targets)
    assert len(runtime.model.kinematics.history) <= 1
    runtime.control(position_s=2.99)
    runtime.tick()
    now[0] += .03
    runtime.tick()
    assert not any(v.gain for v in audio.targets)
    assert runtime.transport.position() < .1
    store.close()
