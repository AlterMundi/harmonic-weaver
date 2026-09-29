import time

from harmonic_weaver.lab.contracts import PerceptionSettings
from harmonic_weaver.lab.media import VideoLibrary


class FakeWorker:
    calls = 0

    def probe(self):
        return {"version": "fake-1"}

    def messages(self, settings, *, source_id, stream_id, video):
        type(self).calls += 1
        for i, t in enumerate((0., .04, .11)):
            yield {"type": "frame", "frame": dict(source_id=source_id, stream_id=stream_id,
                sequence=i, source_time_s=t, available_monotonic_s=1.+i,
                timestamp_origin="pts", width=360, height=640, persons=[])}
        yield {"type": "complete", "frames": 3}

    def stop(self):
        pass


def wait(library, job):
    library.jobs[job["id"]].thread.join(timeout=3)
    state = library.snapshot(job["id"])
    assert state["status"] == "ready", state
    return state


def test_video_loops_and_reopening_never_reinfer(tmp_path):
    FakeWorker.calls = 0
    media, model = tmp_path / "vfr.mp4", tmp_path / "model.pt"
    media.write_bytes(b"video")
    model.write_bytes(b"model")
    config = PerceptionSettings(checkpoint=str(model))
    library = VideoLibrary(tmp_path / "data", worker_factory=FakeWorker)
    job = library.open(media, config)
    first = wait(library, job)
    for _ in range(20):
        assert library.frame_at(job["id"], .045).sequence == 1
        assert library.frame_at(job["id"], .12).sequence == 2
        assert library.frame_at(job["id"], .0).sequence == 0
    assert FakeWorker.calls == 1
    library.close()
    reopened = VideoLibrary(tmp_path / "data", worker_factory=FakeWorker)
    second = wait(reopened, reopened.open(media, config))
    assert second["cache_hit"] and FakeWorker.calls == 1
    assert second["media_id"] == first["media_id"]
    assert reopened.list_assets()[0]["path"] == str(media)
    forced = wait(reopened, reopened.open(media, config, force=True))
    assert not forced["cache_hit"] and FakeWorker.calls == 2
    reopened.close()
