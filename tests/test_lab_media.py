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


def test_failed_gpu_generation_keeps_cache_and_cpu_uses_separate_key(tmp_path):
    class Worker(FakeWorker):
        fail = False
        def resolve_device(self, requested):
            return "cuda:0" if requested=="auto" else requested
        def messages(self, settings, **kwargs):
            yield from super().messages(settings, **kwargs)
            if self.fail and settings.device=="cuda:0":
                raise RuntimeError("CUDA illegal instruction")

    video, model=tmp_path/"clip.mp4", tmp_path/"m.pt"
    video.write_bytes(b"video");model.write_bytes(b"weights")
    config=PerceptionSettings(checkpoint=str(model),device="auto")
    library=VideoLibrary(tmp_path/"data",worker_factory=Worker)
    original=wait(library,library.open(video,config))
    Worker.fail=True
    failed=library.open(video,config,force=True)
    library.jobs[failed["id"]].thread.join(3)
    assert library.snapshot(failed["id"])["status"]=="error"
    reopened=wait(library,library.open(video,config))
    assert reopened["cache_hit"] and reopened["cache_key"]==original["cache_key"]
    cpu=wait(library,library.open(video,config.model_copy(update={"device":"cpu"})))
    assert cpu["cache_key"] != original["cache_key"]
    assert cpu["effective_device"]=="cpu"
    assert (tmp_path/"data/tracking-attempts.jsonl").is_file()
    library.close()
