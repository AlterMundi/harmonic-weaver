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


def test_audio_diagnostic_distinguishes_explicit_disabled_mode_from_connection(tmp_path):
    store=SessionStore(tmp_path)
    try:
        runtime=LaboratoryRuntime(store,audio=Audio(),library=Library())
        runtime._diagnose(Preset(),False,{"audio_disabled":True,"error":None},None)
        assert runtime.diagnostic['audio_status']=='disabled'
        assert runtime.diagnostic['audio_error'] is None
        runtime._diagnose(Preset(),False,{"audio_disabled":True,"error":"control failed"},None)
        assert runtime.diagnostic['audio_error']=='control failed'
        runtime._diagnose(Preset(),False,{"error":"503"},None)
        assert runtime.diagnostic['audio_status']=='unavailable'
    finally:
        store.close()


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
    # Display edits must not restart kinematics, subspace or articulation.
    history = list(model.kinematics.history)
    targets = list(audio.targets)
    preset.visual.collective_view = "projector"
    preset.visual.collective_max_axes = 8
    store.edit(preset, 2)
    runtime.tick()  # same source instant, no new observation
    assert runtime.model is model
    assert list(model.kinematics.history) == history
    assert audio.targets == targets
    assert audio.revision == 3
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


def test_last_video_survives_restart_but_explicit_close_clears_it(tmp_path):
    from harmonic_weaver.lab.contracts import PerceptionSettings

    class RestorableLibrary(Library):
        def open(self, path, settings, force=False):
            assert not force
            return {"id": "restored", "path": str(path)}
        def cancel(self, job):
            pass

    settings = PerceptionSettings(checkpoint="test.pt")
    store = SessionStore(tmp_path)
    runtime = LaboratoryRuntime(store, library=RestorableLibrary(), audio=Audio())
    runtime.open_video("/example.mp4", settings)
    store.close()
    store = SessionStore(tmp_path)
    runtime = LaboratoryRuntime(store, library=RestorableLibrary(), audio=Audio())
    runtime.restore_video()
    assert runtime.job_id == "restored"
    assert runtime.transport.position() == 0
    assert not runtime.transport.playing
    runtime.close_source()
    assert store.last_video() is None
    store.close()


def test_calibration_diagnostic_and_compatible_edits_preserve_response(tmp_path):
    now=[0.]
    store=SessionStore(tmp_path,prepare=PreparedRoutes)
    p=Preset(algorithm={"id":"local"},response={"pluck_enabled":False},expression=1)
    store.edit(p,0)
    runtime=LaboratoryRuntime(store,library=Library(),audio=Audio(),clock=lambda:now[0])
    runtime.kind,runtime.job_id="video","test"
    runtime.tick()
    assert runtime.diagnostic["code"]=="calibration_required"
    runtime.calibrate()
    runtime.control(playing=True)
    for i in range(20):
        now[0]=i/30
        runtime.tick()
    assert runtime.diagnostic["observed_signals"]>0
    previous=dict(runtime.routes.expression_history)
    p.expression=2
    store.edit(p,1)
    runtime.tick()
    assert runtime.routes.expression_history==previous
    store.close()


class TwoPeopleLibrary(Library):
    def __init__(self, *, generation="g1", media_id="media-a", status="ready"):
        super().__init__()
        self.generation, self.media_id, self.status = generation, media_id, status
        for frame in self.frames:
            if not frame.persons:
                continue
            other = frame.persons[0].model_copy(deep=True)
            other.person_id = "two"
            for joint in other.joints:
                if joint.position is not None:
                    joint.position[0] += .5
            frame.persons.append(other)

    def snapshot(self, job):
        return {"status":self.status, "duration_s":3., "media_id":self.media_id,
                "cache_key":"cache", "generation":self.generation if self.status=="ready" else None,
                "default_person_id":"two", "person_ids":["one","two"] if self.status=="ready" else []}

    def open(self, path, settings, force=False):
        return {"id":"test", "path":str(path)}


def test_two_people_selection_restores_only_same_generation_without_calibration(tmp_path):
    from harmonic_weaver.lab.contracts import PerceptionSettings
    settings=PerceptionSettings(checkpoint="example.pt")
    store=SessionStore(tmp_path,prepare=PreparedRoutes)
    runtime=LaboratoryRuntime(store,library=TwoPeopleLibrary(),audio=Audio())
    runtime.open_video("/example.mp4",settings)
    runtime.tick()
    assert runtime.person_id == "two"
    runtime.select_person("two")
    runtime.calibrate()
    assert runtime.calibration is not None
    store.close()

    store=SessionStore(tmp_path,prepare=PreparedRoutes)
    restored=LaboratoryRuntime(store,library=TwoPeopleLibrary(),audio=Audio())
    restored.restore_video()
    restored.tick()
    assert restored.person_id=="two" and restored.selection_status=="restored"
    assert restored.calibration is None
    restored.open_video("/example.mp4",settings)
    restored.library.generation="g2"
    restored.tick()
    assert restored.person_id == "two"
    assert restored.selection_status=="automatic_changed"
    assert store.source_selection("media-a")["generation"]=="g1"
    restored.select_person("one")
    assert store.source_selection("media-a")["generation"]=="g2"
    # Identical slot names in another source do not grant identity continuity.
    restored.library.media_id="media-b"
    restored.open_video("/other.mp4",settings)
    restored.tick()
    assert restored.person_id == "two" and restored.selection_status=="automatic"
    store.close()


def test_explicit_prefix_selection_is_pinned_when_generation_finishes(tmp_path):
    import pytest
    store=SessionStore(tmp_path,prepare=PreparedRoutes)
    library=TwoPeopleLibrary(status="building")
    runtime=LaboratoryRuntime(store,library=library,audio=Audio())
    runtime.kind,runtime.job_id="video","test"
    runtime.tick()
    assert runtime.person_id == "one"
    with pytest.raises(ValueError,match="detectada"):
        runtime.select_person("unknown")
    runtime.select_person("two")
    assert store.source_selection("media-a") is None
    library.status="ready"
    runtime.tick()
    assert store.source_selection("media-a")["person_id"]=="two"
    # An temporarily absent chosen person must never switch to the other body.
    library.frames[0].persons=[library.frames[0].persons[0]]
    runtime.tick()
    assert runtime.person_id=="two"
    assert runtime.diagnostic["code"]=="tracking_missing"
    store.close()


def test_automatic_final_body_selection_cannot_inherit_prefix_calibration(tmp_path):
    store=SessionStore(tmp_path,prepare=PreparedRoutes)
    store.edit(Preset(algorithm={'id':'local'}),0)
    library=TwoPeopleLibrary(status='building')
    runtime=LaboratoryRuntime(store,library=library,audio=Audio())
    runtime.kind,runtime.job_id='video','test'
    runtime.tick()
    assert runtime.person_id=='one'
    runtime.calibrate();runtime.tick()
    previous=runtime.model;calibration=runtime.calibration
    assert calibration is not None
    library.status='ready';runtime.tick()
    assert runtime.person_id=='two' and runtime.selection_status=='automatic'
    assert runtime.calibration is None
    assert runtime.model is not previous
    assert runtime.model.scale is None and runtime.model.kinematics.scale is None
    assert runtime.diagnostic['code']=='calibration_required'
    assert runtime.audio.targets==[]
    assert store.calibrations()[0]['id']==calibration.id  # preserve historical explicit measurement
    assert 'se descartó la escala activa' in runtime.snapshot()['calibration_notice']
    runtime.calibrate()
    assert runtime.snapshot()['calibration_notice'] is None
    store.close()


def test_explicit_same_prefix_body_keeps_its_calibration_when_tracking_finishes(tmp_path):
    store=SessionStore(tmp_path,prepare=PreparedRoutes)
    library=TwoPeopleLibrary(status='building')
    runtime=LaboratoryRuntime(store,library=library,audio=Audio())
    runtime.kind,runtime.job_id='video','test';runtime.tick();runtime.select_person('two');runtime.calibrate();runtime.tick()
    previous,calibration=runtime.model,runtime.calibration
    library.status='ready';runtime.tick()
    assert runtime.person_id=='two' and runtime.selection_status=='explicit'
    assert runtime.calibration is calibration and runtime.model is previous
    assert runtime.snapshot()['calibration_notice'] is None
    assert store.source_selection('media-a')['person_id']=='two'
    store.close()


def test_automatic_selection_without_scale_does_not_issue_a_reset_notice(tmp_path):
    store=SessionStore(tmp_path,prepare=PreparedRoutes);library=TwoPeopleLibrary(status='building')
    runtime=LaboratoryRuntime(store,library=library,audio=Audio());runtime.kind,runtime.job_id='video','test'
    runtime.tick();library.status='ready';runtime.tick()
    assert runtime.person_id=='two' and runtime.snapshot()['calibration_notice'] is None
    store.close()


def test_new_source_and_explicit_choice_clear_previous_calibration_notice(tmp_path):
    from harmonic_weaver.lab.contracts import PerceptionSettings
    store=SessionStore(tmp_path,prepare=PreparedRoutes);library=TwoPeopleLibrary()
    runtime=LaboratoryRuntime(store,library=library,audio=Audio());runtime.kind,runtime.job_id='video','test';runtime.tick()
    runtime.calibration_notice='previous automatic body change'
    runtime.select_person('one');assert runtime.snapshot()['calibration_notice'] is None
    runtime.calibration_notice='previous automatic body change'
    runtime.open_video('/example.mp4',PerceptionSettings(checkpoint='example.pt'));assert runtime.snapshot()['calibration_notice'] is None
    runtime.calibration_notice='previous automatic body change'
    library.cancel=lambda job:None
    runtime.close_source();assert runtime.snapshot()['calibration_notice'] is None
    store.close()


def test_default_first_autoplay_waits_for_cache_and_manual_pause_wins(tmp_path):
    from harmonic_weaver.lab.contracts import PerceptionSettings
    store=SessionStore(tmp_path,prepare=PreparedRoutes)
    store.set_source_preferences({"default_person":"first", "autoplay_video":True})
    library=TwoPeopleLibrary(status="building")
    runtime=LaboratoryRuntime(store,library=library,audio=Audio())
    runtime.open_video("/example.mp4",PerceptionSettings(checkpoint="example.pt"))
    runtime.tick()
    assert not runtime.transport.playing
    library.status="ready"
    runtime.tick()
    assert runtime.transport.playing and runtime.person_id=="one"
    runtime.open_video("/example.mp4",PerceptionSettings(checkpoint="example.pt"))
    runtime.control(playing=False)
    runtime.tick()
    assert not runtime.transport.playing
    store.close()
    store=SessionStore(tmp_path,prepare=PreparedRoutes)
    assert store.source_preferences()=={"default_person":"first", "autoplay_video":True}
    store.close()


def test_marks_distinguish_observed_epoch_from_pending_transport_seek(tmp_path):
    store=SessionStore(tmp_path,prepare=PreparedRoutes)
    runtime=LaboratoryRuntime(store,audio=Audio(),library=Library(),clock=lambda:0.)
    try:
        runtime.kind,runtime.job_id='video','test'
        runtime.tick();runtime.mark('Before',category='preparation')
        first=store.events()[0]
        runtime.control(position_s=1.)
        runtime.mark('Seek pending',category='deployment')
        pending=store.events()[0]
        assert pending['payload']['observed_epoch']==first['payload']['observed_epoch']
        assert pending['payload']['transport_epoch']!=first['payload']['transport_epoch']
        assert pending['payload']['frame_time_s']==first['payload']['frame_time_s']
        runtime.tick();runtime.mark('After')
        after=store.events()[0]
        assert after['payload']['observed_epoch']==after['payload']['transport_epoch']
        assert after['payload']['frame_time_s']>=1.
    finally:store.close()


def test_tracked_prefix_loop_is_explicit_fixed_and_resets_history(tmp_path):
    import pytest
    now = [0.]
    store = SessionStore(tmp_path, prepare=PreparedRoutes)
    library = TwoPeopleLibrary(status='building')
    original_snapshot = library.snapshot
    prefix = [1.]
    library.snapshot = lambda job: {**original_snapshot(job), 'prefix_s':prefix[0]}
    audio = Audio()
    runtime = LaboratoryRuntime(store, library=library, audio=audio, clock=lambda:now[0])
    runtime.kind, runtime.job_id = 'video','test'
    runtime.tick()
    runtime.control(tracked_prefix=True, playing=True)
    runtime.tick()
    assert store.snapshot()['session']['loop_end_s'] == 1.
    epoch = runtime.transport.epoch
    now[0] = 1.05
    runtime.tick()
    assert runtime.transport.epoch > epoch
    assert runtime.transport.position() == pytest.approx(.05)
    assert len(runtime.model.kinematics.history) <= 1
    prefix[0] = 2.
    runtime.tick()
    assert runtime.transport.loop_end_s == 1.
    runtime.control(tracked_prefix=True)
    assert runtime.transport.loop_end_s == 2.
    library.status = 'ready'
    runtime.tick()
    assert runtime.transport.loop_end_s == 2.
    runtime.control(loop=False)
    assert runtime.transport.loop_end_s is None
    prefix[0] = 0.
    with pytest.raises(ValueError,match='non-empty'):
        runtime.control(tracked_prefix=True)
    runtime.kind = 'camera'
    with pytest.raises(ValueError,match='only file'):
        runtime.control(tracked_prefix=True)
    store.close()
