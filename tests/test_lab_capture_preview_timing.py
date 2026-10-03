"""Measure AAC preview timing separately from exact archival PCM."""
import json
import subprocess
import cv2
import numpy as np
import pytest
from harmonic_weaver.lab.capture_export import render_capture
from test_lab_capture_stimulus import stimulus_session


def measure_preview(path):
    raw=subprocess.check_output(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-i',str(path),'-map','0:a:0','-f','f32le','-'])
    samples=np.frombuffer(raw,dtype='<f4').reshape(-1,2)
    # Energy centroid inside a fixed, declared 100ms window around the supplied
    # transient; not threshold onset, exact PCM identity or a perceptual metric.
    first,last=21600,26400
    energy=np.sum(samples[first:last].astype(float)**2,axis=1)
    assert energy.sum()>0
    centroid=float(np.dot(np.arange(first,last)/48000,energy)/energy.sum())
    peak=int(np.argmax(np.sum(samples.astype(float)**2,axis=1)))
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_frames','-show_entries','frame=best_effort_timestamp_time','-of','json',str(path)]))
    times=[float(r['best_effort_timestamp_time']) for r in probe['frames']]
    decoder=cv2.VideoCapture(str(path));bright=[];index=0
    while True:
        ok,image=decoder.read()
        if not ok:break
        if image.mean()>200:bright.append(index)
        index+=1
    decoder.release()
    assert index==20 and len(times)==20 and len(bright)==1
    return samples,{'audio_energy_centroid_s':centroid,'audio_peak_s':peak/48000,
                    'decoded_audio_samples':len(samples),'video_flash_pts_s':times[bright[0]],
                    'analysis_window_s':[.45,.55]}


@pytest.mark.parametrize('bitrate,offset',[(64,0),(192,0),(320,0),(192,.1),(192,-.1)])
def test_preview_aac_transient_timing_and_copied_flash(tmp_path,bitrate,offset):
    manifest,original=stimulus_session(tmp_path/'input')
    folder=tmp_path/'export'
    report=render_capture(manifest,folder,{'fps':20,'width':160,'height':120,'browser_preview':True,'preview_audio_kbps':bitrate,'offset_s':offset})
    decoded,measured=measure_preview(folder/'preview.mp4')
    # Three pulse widths (2ms) is an explicit control tolerance; detects an
    # uncompensated AAC frame delay (~21ms) without claiming sample identity.
    reference=(24000+15.5)/48000
    assert abs(measured['audio_energy_centroid_s']-reference)<.002
    assert abs(measured['audio_peak_s']-.5)<.002
    assert measured['video_flash_pts_s']==pytest.approx(.5-offset,abs=1e-6)
    assert not np.array_equal(decoded,original)
    assert report['preview']['audio']=='lossy AAC derived from confirmed PCM'
    exact=np.frombuffer(subprocess.check_output(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-i',str(folder/'capture.mkv'),'-map','0:a:0','-f','f32le','-']),dtype='<f4').reshape(-1,2)
    np.testing.assert_array_equal(exact,original)
