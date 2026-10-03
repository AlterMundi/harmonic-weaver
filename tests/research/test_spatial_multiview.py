import copy
import math
import numpy as np
import pytest
from harmonic_weaver.lab.research.spatial_multiview import calculate, synthetic_request, Camera, Request


def test_known_metric_trajectory_repeats_and_remains_inferred():
    request=synthetic_request();original=copy.deepcopy(request)
    result=calculate(request)
    assert result==calculate(request) and request==original
    assert result['coverage']=={'observed':0,'held':0,'inferred':5,'missing':0}
    assert result['stream']['units']=='metres'
    assert result['stream']['clock']['method']=='declared_assumption'
    for i,frame in enumerate(result['stream']['frames']):
        np.testing.assert_allclose(frame['points'][0]['position'],[i*.02,.2,4+i*.05],atol=1e-10)
        assert frame['points'][0]['confidence'] is None
        assert max(result['diagnostics'][i]['reprojection_error_px'])<1e-9


def test_world_to_camera_rotation_and_translation_not_camera_to_world():
    request=synthetic_request();theta=.2
    request['right_camera']['world_to_camera_rotation']=[[math.cos(theta),0,math.sin(theta)],[0,1,0],[-math.sin(theta),0,math.cos(theta)]]
    camera=Camera.model_validate(request['right_camera'])
    for i,frame in enumerate(request['frames']):
        projected=camera.projection()@np.array([i*.02,.2,4+i*.05,1])
        frame['right'][0]['position']=(projected[:2]/projected[2]).tolist()
    result=calculate(request)
    np.testing.assert_allclose(result['stream']['frames'][3]['points'][0]['position'],[.06,.2,4.15],atol=1e-10)


@pytest.mark.parametrize('change,cause',[('time','paired_time_difference'),('uncertainty','declared_clock_uncertainty'),('held','requires_two_observed_pixels'),('absent','requires_two_observed_pixels'),('parallax','insufficient_parallax'),('reprojection','reprojection_error')])
def test_exclusion_never_manufactures_origin_coordinates(change,cause):
    request=synthetic_request()
    if change=='time':request['right_clock']['offset_s']=.05
    if change=='uncertainty':request['right_clock']['uncertainty_s']=.1
    if change=='held':request['frames'][0]['right'][0]['state']='held'
    if change=='absent':request['frames'][0]['right']=[]
    if change=='parallax':request['settings']['min_ray_angle_deg']=89
    if change=='reprojection':request['frames'][0]['right'][0]['position'][1]+=30
    result=calculate(request);point=result['stream']['frames'][0]['points'][0]
    assert point['state']=='missing' and point['position'] is None and point['confidence'] is None
    assert point['cause']==cause
    assert result['request']==Request.model_validate(request).model_dump()


@pytest.mark.parametrize('change',['rotation','baseline','clock','pixel_mode','time_order','dimensions','duplicates','negative_common','budget','calibration'])
def test_invalid_calibration_pairing_or_budgets_rejected(change):
    request=synthetic_request()
    if change=='rotation':request['left_camera']['world_to_camera_rotation'][0][0]=-1
    if change=='baseline':request['right_camera']['world_to_camera_translation_m']=[0,0,0]
    if change=='clock':request['right_clock']['common_clock']='another'
    if change=='pixel_mode':request['image_coordinates']='distorted_pixels'
    if change=='time_order':request['frames'][1]['right_time_s']=0
    if change=='dimensions':request['frames'][0]['left'][0]['position'].append(2)
    if change=='duplicates':request['labels']=['marker','marker']
    if change=='negative_common':request['left_clock']['offset_s']=-1
    if change=='budget':request['frames']*=10000
    if change=='calibration':request.pop('calibration_evidence')
    with pytest.raises(ValueError):calculate(request)


def test_infinite_rays_and_points_behind_cameras_stay_missing():
    request=synthetic_request()
    request['frames'][0]['right'][0]['position']=request['frames'][0]['left'][0]['position']
    assert calculate(request)['stream']['frames'][0]['points'][0]['state']=='missing'
    request=synthetic_request()
    for key in ('left_camera','right_camera'):
        p=Camera.model_validate(request[key]).projection()@np.array([0,.2,-4,1])
        request['frames'][0]['left' if key=='left_camera' else 'right'][0]['position']=(p[:2]/p[2]).tolist()
    assert calculate(request)['stream']['frames'][0]['points'][0]['cause']=='behind_or_on_camera_plane'


def test_http_and_portable_configuration(tmp_path):
    from types import SimpleNamespace
    from fastapi.testclient import TestClient
    from harmonic_weaver.lab.app import create_app
    runtime=SimpleNamespace(library=None,start=lambda:None,close=lambda:None)
    with TestClient(create_app(tmp_path,runtime=runtime),base_url='http://127.0.0.1') as client:
        root='/api/research/r09/multiview'
        request=client.get(root+'/example').json()
        response=client.post(root,json=request);assert response.status_code==200,response.text
        assert response.json()==calculate(request)
        assert client.post(root+'/configuration',json={}).json()['min_ray_angle_deg']==1
        assert client.post(root+'/configuration',json={'calibration_id':'secret-source'}).status_code==422
        request['left_camera']['world_to_camera_rotation'][0][0]=-1
        assert client.post(root,json=request).status_code==422
