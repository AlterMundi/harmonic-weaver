import base64
import json
import threading
from pathlib import Path

import pytest

from harmonic_weaver.lab.capture_camera import CameraCapture
from harmonic_weaver.lab.cache import sha256_file


def packet(sequence=1,stream='camera'):
    return dict(jpeg=base64.b64encode(b'synthetic-jpeg').decode(),stream_id=stream,sequence=sequence,
                captured_monotonic_s=10,available_monotonic_s=10.1)


def test_camera_writer_preserves_packets_clocks_hashes_and_gap_counts(tmp_path):
    capture=CameraCapture(tmp_path)
    first=capture.offer(packet());assert capture.offer(packet()) is None
    capture.offer(packet(4));capture.offer(packet(1,'new-stream'))
    result=capture.close()
    assert result['status']=='complete' and result['written_frames']==3
    assert result['observed_sequence_gaps']==2
    folder=Path(result['directory'])
    rows=[json.loads(line) for line in (folder/'frames.jsonl').read_text().splitlines()]
    assert rows[0]['captured_monotonic_s']==10 and rows[0]['available_monotonic_s']==10.1
    assert (folder/first['file']).read_bytes()==b'synthetic-jpeg'
    assert sha256_file(folder/'frames.jsonl')==result['index_sha256']
    assert json.loads((folder/'manifest.json').read_text())['status']=='complete'
    assert sha256_file(folder/rows[0]['file'])==rows[0]['sha256']


def test_camera_budget_and_backwards_sequence_are_explicit(tmp_path):
    capture=CameraCapture(tmp_path,max_frames=1)
    capture.offer(packet())
    with pytest.raises(ValueError,match='backwards'):capture.offer(packet(0))
    with pytest.raises(ValueError,match='budget'):capture.offer(packet(2))
    assert capture.close(error='budget')['status']=='failed'


def test_slow_writer_overflow_never_waits_for_queue(tmp_path,monkeypatch):
    entered=threading.Event();release=threading.Event()
    original=Path.write_bytes
    def write(path,data):
        if path.suffix=='.jpg':entered.set();assert release.wait(3)
        return original(path,data)
    monkeypatch.setattr(Path,'write_bytes',write)
    capture=CameraCapture(tmp_path,queue_frames=1)
    capture.offer(packet());assert entered.wait(2)
    capture.offer(packet(2))
    with pytest.raises(ValueError,match='overflow'):capture.offer(packet(3))
    release.set();capture.close(error='overflow')


def test_disk_failure_is_visible_and_raw_metadata_is_retained(tmp_path,monkeypatch):
    original=Path.write_bytes
    def write(path,data):
        if path.suffix=='.jpg':raise OSError('synthetic disk failure')
        return original(path,data)
    monkeypatch.setattr(Path,'write_bytes',write)
    capture=CameraCapture(tmp_path);capture.offer(packet());capture.close()
    assert capture.snapshot()['status']=='failed'
    assert 'disk failure' in capture.snapshot()['error']


def test_close_rejects_late_frames_and_drains_accepted_frame(tmp_path,monkeypatch):
    entered=threading.Event();release=threading.Event()
    original=Path.write_bytes
    def write(path,data):
        if path.suffix=='.jpg':entered.set();assert release.wait(3)
        return original(path,data)
    monkeypatch.setattr(Path,'write_bytes',write)
    capture=CameraCapture(tmp_path)
    reference=capture.offer(packet());assert entered.wait(2)
    results=[]
    closer=threading.Thread(target=lambda:results.append(capture.close()))
    closer.start();assert capture.stop_event.wait(2)
    try:
        with pytest.raises(ValueError,match='closed'):capture.offer(packet(2))
        assert capture.accepted==1
    finally:release.set();closer.join(timeout=3)
    assert not closer.is_alive()
    assert results[0]['written_frames']==1
    assert (Path(results[0]['directory'])/reference['file']).is_file()
    assert capture.close()['index_sha256']==results[0]['index_sha256']
