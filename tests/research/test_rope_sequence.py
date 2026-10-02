import os
import subprocess
import sys
import threading
import cv2
import numpy as np
import pytest
from harmonic_weaver.lab.research.rope_media import probe,_frame_png
from harmonic_weaver.lab.research.rope_sequence import sequence,png_frames
from harmonic_weaver.lab.research.rope_process import DecodeCancelled


def video(tmp_path):
    path=tmp_path/'video.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=160x120:rate=10:duration=0.5','-c:v','libx264',str(path)],check=True)
    return path,probe(path)


def test_sequence_matches_individual_exact_frames_and_checks_source(tmp_path):
    path,media=video(tmp_path);sha=media['media_sha256']
    frames=list(sequence(path,1,3,sha,media))
    assert len(frames)==3
    for index,png in enumerate(frames,1):
        actual=cv2.imdecode(np.frombuffer(png,dtype=np.uint8),cv2.IMREAD_UNCHANGED)
        expected=cv2.imdecode(np.frombuffer(_frame_png(path,index,sha,media),dtype=np.uint8),cv2.IMREAD_UNCHANGED)
        np.testing.assert_array_equal(actual,expected)
    assert sorted(p.name for p in tmp_path.iterdir())==['video.mp4']
    stream=sequence(path,0,3,sha,media)
    next(stream)
    with path.open('ab') as handle:handle.write(b'changed')
    with pytest.raises(ValueError,match='changed'):list(stream)


def test_count_crc_and_memory_budgets_reject_bad_streams(tmp_path):
    path,media=video(tmp_path);png=_frame_png(path,0,media['media_sha256'],media)
    def command(data):return [sys.executable,'-c',f'import sys;sys.stdout.buffer.write(bytes.fromhex({data.hex()!r}))']
    assert list(png_frames(command(png*2),2))==[png,png]
    for data,count in ((png,2),(png*2,1),(png[:-1],1),(png[:20]+bytes([png[20]^1])+png[21:],1)):
        with pytest.raises(ValueError):list(png_frames(command(data),count))
    with pytest.raises(ValueError,match='budget'):list(png_frames(command(png),1,max_frame_bytes=40))


def test_cancel_after_yield_kills_owned_process_and_close_works(tmp_path):
    path,media=video(tmp_path);png=_frame_png(path,0,media['media_sha256'],media)
    marker=tmp_path/'pid'
    command=[sys.executable,'-c',f'from pathlib import Path;import os,sys,time;Path({str(marker)!r}).write_text(str(os.getpid()));sys.stdout.buffer.write(bytes.fromhex({png.hex()!r}));sys.stdout.buffer.flush();time.sleep(30)']
    event=threading.Event();stream=png_frames(command,2,cancel=event)
    assert next(stream)==png;pid=int(marker.read_text());os.kill(pid,0)
    event.set()
    with pytest.raises(DecodeCancelled):next(stream)
    with pytest.raises(ProcessLookupError):os.kill(pid,0)
    stream=png_frames(command,2);next(stream);pid=int(marker.read_text());stream.close()
    with pytest.raises(ProcessLookupError):os.kill(pid,0)


def test_inventory_pre_cancel_and_timeout_are_bounded(tmp_path):
    path,media=video(tmp_path)
    for start,count in ((True,2),(0,121),(4,2),(-1,2)):
        with pytest.raises(ValueError):list(sequence(path,start,count,media['media_sha256'],media))
    link=tmp_path/'link.mp4';link.symlink_to(path)
    with pytest.raises(ValueError,match='Regular'):list(sequence(link,0,2,media['media_sha256'],media))
    marker=tmp_path/'timeout.pid'
    command=[sys.executable,'-c',f'from pathlib import Path;import os,time;Path({str(marker)!r}).write_text(str(os.getpid()));time.sleep(30)']
    event=threading.Event();event.set()
    with pytest.raises(DecodeCancelled):list(png_frames(command,1,cancel=event))
    assert not marker.exists()
    with pytest.raises(ValueError,match='timed out'):list(png_frames(command,1,timeout=.5))
    assert marker.exists()
    with pytest.raises(ProcessLookupError):os.kill(int(marker.read_text()),0)
