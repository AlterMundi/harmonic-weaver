"""Decoded lossy preview timing control; no human media or audio devices."""
import argparse
import json
import platform
import subprocess
import numpy as np
import cv2
from pathlib import Path
from harmonic_weaver.lab.capture_export import render_capture
from harmonic_weaver.lab.cache import sha256_file
from test_lab_capture_stimulus import stimulus_session
from test_lab_capture_preview_timing import measure_preview


def experiment(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    manifest,_=stimulus_session(output/'input')
    report={'kind':'capture_aac_preview_transient_control','recipe_sha256':sha256_file(Path(__file__)),
            'fixture_sha256':sha256_file(Path('tests/test_lab_capture_preview_timing.py')),
            'export_code_sha256':sha256_file(Path('src/harmonic_weaver/lab/capture_export.py')),
            'environment':{'python':platform.python_version(),'numpy':np.__version__,'opencv':cv2.__version__,
                           'ffmpeg':subprocess.check_output(['ffmpeg','-version'],text=True).splitlines()[0]},
            'reference_energy_centroid_s':(24000+15.5)/48000,'control_tolerance_s':.002,'conditions':[],
            'limits':['Fixed synthetic transient and 100ms analysis window, not general codec error bound',
                      'Energy centroid/peak are timing controls, not perceptual onset',
                      'Decoded lossy AAC is not exact archive PCM',
                      'No hardware, acoustics or human synchrony/acceptance measured']}
    for bitrate,offset in [(64,0),(192,0),(320,0),(192,.1),(192,-.1)]:
        measurements=[]
        for repeat in range(2):
            folder=output/f'bitrate-{bitrate}-offset-{offset}-repeat-{repeat}'
            render_capture(manifest,folder,{'fps':20,'width':160,'height':120,'browser_preview':True,'preview_audio_kbps':bitrate,'offset_s':offset})
            _,measured=measure_preview(folder/'preview.mp4')
            assert abs(measured['audio_energy_centroid_s']-report['reference_energy_centroid_s'])<.002
            assert abs(measured['video_flash_pts_s']-(.5-offset))<1e-6
            measurements.append(measured)
        assert measurements[0]==measurements[1]
        report['conditions'].append({'preview_audio_kbps':bitrate,'offset_s':offset,'measurements':measurements,'repeat_measurements_identical':True})
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    args=parser.parse_args()
    print(json.dumps(experiment(args.output),indent=2,sort_keys=True,allow_nan=False))
