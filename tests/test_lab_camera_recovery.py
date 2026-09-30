import json
from pathlib import Path

import pytest
from harmonic_weaver.lab.capture_camera import CameraCapture
from harmonic_weaver.lab.capture_camera_recovery import recover_camera
from harmonic_weaver.lab.cache import sha256_file
from test_lab_capture_camera import packet


def test_inactive_prefix_preserves_originals_and_stops_at_truncated_tail(tmp_path):
    capture=CameraCapture(tmp_path)
    capture.offer(packet());capture.offer(packet(2));capture.close(error='interrupted fixture')
    index=tmp_path/'camera'/'frames.jsonl'
    with index.open('ab') as handle:handle.write(b'{"broken":')
    before=sha256_file(index)
    result=recover_camera(tmp_path)
    assert result['status']=='recovered' and result['verified_frames']==2
    assert result['stop_reason']=='truncated_row'
    assert sha256_file(index)==before
    assert len((Path(result['directory'])/'frames.jsonl').read_text().splitlines())==2
    assert result['frame_root']==str(tmp_path/'camera')


def test_active_complete_changed_image_and_symlinks_are_not_recovered(tmp_path):
    capture=CameraCapture(tmp_path)
    with pytest.raises(ValueError,match='active'):recover_camera(tmp_path)
    capture.offer(packet());capture.close()
    with pytest.raises(ValueError,match='complete'):recover_camera(tmp_path)
    capture.close(error='interrupted fixture')
    image=tmp_path/'camera'/'00000000.jpg';image.write_bytes(b'changed')
    result=recover_camera(tmp_path)
    assert result['verified_frames']==0 and 'changed image' in result['stop_reason']
    image.unlink();image.symlink_to(tmp_path/'outside.jpg')
    assert recover_camera(tmp_path)['verified_frames']==0
    lock=tmp_path/'camera'/'writer.lock';lock.unlink()
    with pytest.raises(ValueError,match='requires'):recover_camera(tmp_path)


def test_killed_writer_releases_lock_and_confirmed_prefix_is_recoverable(tmp_path):
    import subprocess
    import sys
    code='''
import base64,sys,time
from harmonic_weaver.lab.capture_camera import CameraCapture
capture=CameraCapture(sys.argv[1])
capture.offer(dict(jpeg=base64.b64encode(b"synthetic-jpeg").decode(),stream_id="camera",sequence=1,captured_monotonic_s=10,available_monotonic_s=10.1))
deadline=time.monotonic()+3
while capture.written<1 and time.monotonic()<deadline:time.sleep(.005)
assert capture.written==1
print("ready",flush=True)
time.sleep(30)
'''
    process=subprocess.Popen([sys.executable,'-c',code,str(tmp_path)],stdout=subprocess.PIPE,text=True)
    try:
        assert process.stdout.readline().strip()=='ready'
        with pytest.raises(ValueError,match='active'):recover_camera(tmp_path)
        process.kill();process.wait(timeout=3)
        result=recover_camera(tmp_path)
        assert result['verified_frames']==1 and result['status']=='recovered'
        assert json.loads((tmp_path/'camera'/'manifest.json').read_text())['status']=='recording'
    finally:
        if process.poll() is None:process.kill();process.wait(timeout=3)
        process.stdout.close()


def test_nonconsecutive_image_index_does_not_extend_prefix(tmp_path):
    capture=CameraCapture(tmp_path)
    capture.offer(packet());capture.offer(packet(2));capture.close(error='fixture')
    index=tmp_path/'camera'/'frames.jsonl'
    rows=list(map(json.loads,index.read_text().splitlines()))
    rows[1]['file']=rows[0]['file'];rows[1]['sha256']=rows[0]['sha256']
    index.write_text(''.join(json.dumps(row)+'\n' for row in rows))
    result=recover_camera(tmp_path)
    assert result['verified_frames']==1 and 'Nonconsecutive' in result['stop_reason']
