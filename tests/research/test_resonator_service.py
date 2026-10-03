import time
import pytest
from harmonic_weaver.lab.research.resonator_service import ResonatorService
from harmonic_weaver.lab.research.resonator_artifacts import verify
from harmonic_weaver.lab.research.coincidence_service import CoincidenceService
from harmonic_weaver.lab.research.resonator_worker import run_frozen


def document(end=.3):
    return {'request':dict(evaluation_id='a'*32,run_index=0,signal_id='speed',
        start_s=0,end_s=end,high=1,low=.2),'unit':'T/s',
        'rows':[{'time_s':t,'value':v,'valid':True} for t,v in [(0,0),(.03,2)]],
        'provenance':{'fixture':'synthetic'}}


def test_real_worker_restore_download_and_tamper(tmp_path):
    service = ResonatorService(tmp_path)
    try:
        job = service.start({'resonators':{'sample_rate':8000}},document())
        assert service.processes[job['id']].wait(timeout=10) == 0
        assert service.report(job['id'])['status'] == 'complete'
        assert verify(service.folder(job['id']))['levels']['frames'] == 6400
        restored = ResonatorService(tmp_path)
        try:
            assert restored.list()[0]['status'] == 'complete'
            assert restored.artifact(job['id'],'voices.wav').is_file()
            assert CoincidenceService(tmp_path).list() == []
            with pytest.raises(ValueError,match='Unknown'): restored.artifact(job['id'],'../sum.wav')
            with pytest.raises(ValueError,match='owned'): restored.cancel(job['id'])
            with pytest.raises(ValueError,match='already'):run_frozen(service.folder(job['id']))
            (service.folder(job['id'])/'sum.wav').write_bytes(b'broken')
            with pytest.raises(ValueError,match='hash'): restored.artifact(job['id'],'input.json')
        finally: restored.close()
    finally: service.close()


def test_cancel_active_render_keeps_no_completed_download(tmp_path):
    service = ResonatorService(tmp_path)
    try:
        job = service.start({'resonators':{'sample_rate':96000}},document(120))
        process = service.processes[job['id']]; deadline=time.monotonic()+10
        while not (service.folder(job['id'])/'manifest.json').exists():
            assert process.poll() is None and time.monotonic()<deadline
            time.sleep(.01)
        assert service.report(job['id'])['status'] == 'running'
        with pytest.raises(ValueError,match='active'): service.start({},document())
        assert service.cancel(job['id'])['status'] == 'cancelled'
        assert process.poll() is not None
        with pytest.raises(ValueError):service.artifact(job['id'],'sum.wav')
        assert ResonatorService(tmp_path).list()[0]['status'] == 'cancelled'
    finally: service.close()
    with pytest.raises(ValueError,match='closed'):service.start({},document())


def test_invalid_contract_does_not_enqueue(tmp_path):
    service=ResonatorService(tmp_path)
    try:
        with pytest.raises(ValueError):service.start({'render':{'tail_s':11}},document())
        assert service.list() == [] and service.processes == {}
    finally:service.close()
