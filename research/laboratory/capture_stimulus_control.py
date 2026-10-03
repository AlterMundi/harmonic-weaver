"""Public decoded digital flash/impulse control; no hardware or human media."""
import argparse
import json
import platform
import subprocess
from pathlib import Path
import numpy as np
import cv2
from harmonic_weaver.lab.cache import sha256_file
from harmonic_weaver.lab.capture_export import render_capture
from test_lab_capture_stimulus import stimulus_session,measure_export


def experiment(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    manifest,samples=stimulus_session(output/'input')
    report={'kind':'capture_decoded_digital_stimulus','recipe_sha256':sha256_file(Path(__file__)),
        'code_hashes':{name:sha256_file(Path('src/harmonic_weaver/lab')/name) for name in ['capture_export.py','capture_timeline.py']},
        'fixture_sha256':sha256_file(Path('tests/test_lab_capture_stimulus.py')),
        'environment':{'python':platform.python_version(),'numpy':np.__version__,'opencv':cv2.__version__,
                       'ffmpeg':subprocess.check_output(['ffmpeg','-version'],text=True).splitlines()[0]},
        'conditions':[],
        'limits':['Synthetic encoded flash and supplied PCM, not physical capture',
                  'Decoded MKV float PCM, not lossy browser preview',
                  'Sampled confirmed source positions, frame-resolution timing',
                  'No DAC/display/acoustic latency or human synchrony/acceptance measured']}
    for offset in [0.,.1,-.1]:
        measurements=[]
        for repeat in range(2):
            folder=output/f'offset-{offset}-repeat-{repeat}'
            render_capture(manifest,folder,{'fps':20,'width':160,'height':120,'offset_s':offset})
            decoded,measured=measure_export(folder/'capture.mkv');np.testing.assert_array_equal(decoded,samples)
            measured['video_minus_audio_s']=measured['video_onset_s']-measured['audio_onset_s']
            assert abs(measured['video_minus_audio_s']+offset)<1e-6
            measurements.append(measured)
        assert measurements[0]==measurements[1]
        report['conditions'].append({'offset_s':offset,'measurements':measurements,'repeat_measurements_identical':True})
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    args=parser.parse_args()
    print(json.dumps(experiment(args.output),indent=2,sort_keys=True,allow_nan=False))
