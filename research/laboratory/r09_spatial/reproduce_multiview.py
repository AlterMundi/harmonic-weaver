"""Known synthetic 3D and deliberately incorrect pairing; no camera acquisition."""
import argparse
import copy
import json
import platform
from pathlib import Path
import numpy as np
from harmonic_weaver.lab.cache import sha256_file
from harmonic_weaver.lab.research import spatial_multiview as model


def run(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    base=model.synthetic_request();cases={'known':base,'clock_offset':copy.deepcopy(base),'low_parallax':copy.deepcopy(base),'wrong_pairing':copy.deepcopy(base)}
    cases['clock_offset']['right_clock']['offset_s']=.05
    cases['low_parallax']['settings']['min_ray_angle_deg']=89
    for i,frame in enumerate(cases['wrong_pairing']['frames']):frame['right']=copy.deepcopy(base['frames'][(i+1)%5]['right'])
    summary={'synthetic_only':True,'physical_calibration_verified':False,'environment':{'python':platform.python_version(),'numpy':np.__version__},'module_sha256':sha256_file(Path(model.__file__)),'conditions':{}}
    for name,request in cases.items():
        result=model.calculate(request)
        assert result==model.calculate(request)
        errors=[]
        for i,frame in enumerate(result['stream']['frames']):
            position=frame['points'][0]['position']
            if position is not None:errors.append(float(np.linalg.norm(np.asarray(position)-[i*.02,.2,4+i*.05])))
        reprojections=[max(row['reprojection_error_px']) for row in result['diagnostics'] if row['reprojection_error_px'] is not None]
        summary['conditions'][name]={'coverage':result['coverage'],'max_error_to_known_synthetic_3d_m':max(errors) if errors else None,'max_reprojection_error_px':max(reprojections) if reprojections else None,'causes':sorted({r['cause'] for r in result['diagnostics'] if r['cause']})}
        folder=output/name;folder.mkdir()
        for filename,value in [('request.json',request),('result.json',result)]:
            (folder/filename).write_text(json.dumps(value,indent=2,allow_nan=False))
    assert summary['conditions']['known']['max_error_to_known_synthetic_3d_m']<1e-10
    assert summary['conditions']['clock_offset']['coverage']['missing']==5
    assert summary['conditions']['low_parallax']['coverage']['missing']==5
    assert summary['conditions']['wrong_pairing']['max_error_to_known_synthetic_3d_m']>.01
    (output/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False))
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();run(args.output)
