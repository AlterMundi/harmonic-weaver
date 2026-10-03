import io
import numpy as np
import pytest
import soundfile as sf
from fastapi import FastAPI,Request
from fastapi.testclient import TestClient
from harmonic_weaver.lab.research.audio_preview import preview_response


def test_float32_preview_is_explicit_bounded_conversion_and_exact_ranges(tmp_path):
    path=tmp_path/'sum.wav';values=np.linspace(-2,2,10000,dtype=np.float64)
    sf.write(path,values,8000,subtype='DOUBLE');original=path.read_bytes()
    app=FastAPI()
    @app.get('/preview')
    def preview(request:Request):return preview_response(path,gain=.5,range_header=request.headers.get('range'))
    with TestClient(app) as client:
        response=client.get('/preview');assert response.status_code==200
        result,sr=sf.read(io.BytesIO(response.content),dtype='float64')
        np.testing.assert_array_equal(result,(values*.5).astype(np.float32).astype(np.float64))
        assert sr==8000 and len(response.content)==44+len(values)*4
        assert 'no normalization' in response.headers['x-r05-preview']
        for start,end in ((0,43),(41,53),(45,999),(16385,17000),(40000,40043)):
            part=client.get('/preview',headers={'Range':f'bytes={start}-{end}'})
            assert part.status_code==206 and part.content==response.content[start:end+1]
        assert client.get('/preview',headers={'Range':'bytes=-10'}).content==response.content[-10:]
        assert client.get('/preview',headers={'Range':'bytes=100-'}).content==response.content[100:]
        for bad in ('bytes=50000-','bytes=-0','bytes=100-90','bytes=0-1,4-5','invalid'):
            assert client.get('/preview',headers={'Range':bad}).status_code==416
    assert path.read_bytes()==original


def test_preview_never_normalizes_or_limits_over_full_scale(tmp_path):
    path=tmp_path/'sum.wav';sf.write(path,[2.,-2.],8000,subtype='DOUBLE')
    app=FastAPI()
    @app.get('/preview')
    def preview():return preview_response(path)
    with TestClient(app) as client:
        values,_=sf.read(io.BytesIO(client.get('/preview').content))
        np.testing.assert_array_equal(values,[2.,-2.])
    with pytest.raises(ValueError):preview_response(path,gain=float('nan'))
