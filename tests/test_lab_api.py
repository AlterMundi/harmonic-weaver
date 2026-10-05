from fastapi.testclient import TestClient

from harmonic_weaver.lab.app import create_app


def test_api_two_clients_persistence_and_websocket(tmp_path):
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        original = client.get("/api/state").json()
        p = original["preset"]
        p["name"] = "Ángulos y aire"
        p["algorithm"]["id"] = "angular"
        assert client.post("/api/presets", json=p).status_code == 200
        assert client.post(f'/api/presets/{p["id"]}/apply', json={"expected_revision": 0}).status_code == 200
        with client.websocket_connect("ws://127.0.0.1/ws") as ws:
            assert ws.receive_json()["preset"]["algorithm"]["id"] == "angular"
        stale = client.put("/api/configuration", json={"expected_revision": 0, "preset": p})
        assert stale.status_code == 409
        assert stale.json()["state"]["session"]["desired_revision"] == 1
        bad = {**p, "source_id": "should-not-be-portable"}
        assert client.post("/api/presets", json=bad).status_code == 422
        assert len(client.get("/api/presets").json()) == 1
        assert client.post("/api/marks", json={"text": "Se siente bien"}).status_code == 200
        assert client.get("/api/events").json()[0]["kind"] == "mark"
        assert "Preset" in client.get("/api/schemas").json()
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as reopened:
        assert reopened.get("/api/state").json()["preset"] == p
        assert reopened.get(f'/api/presets/{p["id"]}').json() == p


def test_api_invalid_edits_leave_revision_untouched_and_foreign_origin_rejected(tmp_path):
    with TestClient(create_app(tmp_path), base_url="http://localhost") as client:
        state = client.get("/api/state").json()
        assert client.post("/api/marks", json={"text": "x"}, headers={"Origin": "https://example.com"}).status_code == 403
        assert client.get("/api/state", headers={"Host": "remote.example"}).status_code == 403
        p = state["preset"]
        p["algorithm"]["version"] = 99
        assert client.put("/api/configuration", json={"expected_revision": 0, "preset": p}).status_code == 422
        assert client.get("/api/state").json()["session"]["desired_revision"] == 0
        assert client.get("/api/events").json() == []


def test_typed_human_marks_are_persistent_and_reject_unknown_categories(tmp_path):
    with TestClient(create_app(tmp_path),base_url="http://127.0.0.1") as client:
        assert client.post('/api/marks',json={'text':'Preparación percibida','category':'preparation'}).status_code==200
        mark=client.get('/api/events').json()[0]
        assert mark['payload']['annotation_category']=='preparation'
        assert mark['payload']['reaction_latency_corrected'] is False
        assert mark['payload']['timing_basis']=='latest_observed_source_time'
        assert client.post('/api/marks',json={'text':'x','category':'proven_intention'}).status_code==422
        assert client.get('/api/events').json()[0]==mark
    with TestClient(create_app(tmp_path),base_url="http://127.0.0.1") as client:
        assert client.get('/api/events').json()[0]==mark


def test_marks_snapshot_hash_cursor_and_restart(tmp_path):
    import json
    from hashlib import sha256
    with TestClient(create_app(tmp_path),base_url="http://127.0.0.1") as client:
        client.post('/api/marks',json={'text':'A','category':'deployment'})
        response=client.get('/api/marks/snapshot');first=response.json()
        assert 'attachment' in response.headers['content-disposition']
        raw={k:v for k,v in first.items() if k!='content_sha256'}
        assert sha256(json.dumps(raw,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()==first['content_sha256']
        assert client.get('/api/marks/snapshot').json()==first
        client.post('/api/marks',json={'text':'B'})
        second=client.get('/api/marks/snapshot').json()
        assert second['through_sequence']>first['through_sequence']
        assert second['marks'][:len(first['marks'])]==first['marks']
    with TestClient(create_app(tmp_path),base_url="http://127.0.0.1") as client:
        assert client.get('/api/marks/snapshot').json()==second


def test_marks_snapshot_is_not_limited_to_visible_event_history(tmp_path):
    from harmonic_weaver.lab.store import SessionStore
    store=SessionStore(tmp_path)
    try:
        for i in range(1005):store.mark(str(i))
        snapshot=store.marks_snapshot()
        assert len(snapshot['marks'])==1005
        assert len(store.events())==100
        assert snapshot['marks'][0]['event']['payload']['text']=='0'
        assert snapshot['marks'][-1]['event']['payload']['text']=='1004'
    finally:store.close()


def test_mark_snapshot_filters_exact_source_and_person_without_relabeling(tmp_path):
    from harmonic_weaver.lab.store import SessionStore
    store=SessionStore(tmp_path)
    try:
        store.record_event('mark',{'text':'A','source_id':'source-A','person_id':'right'})
        store.record_event('mark',{'text':'B','source_id':'source-A','person_id':'left'})
        store.record_event('mark',{'text':'C','source_id':'source-B','person_id':'right'})
        full=store.marks_snapshot()
    finally:store.close()
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        selected=client.get('/api/marks/snapshot',params={'source_id':'source-A','person_id':'right'}).json()
        assert selected['through_sequence']==full['through_sequence']
        assert selected['marks']==full['marks'][:1]
        assert selected['selection']['source_id']=='source-A'
        assert selected['selection']['person_id']=='right'
        assert client.get('/api/marks/snapshot',params={'source_id':'absent'}).json()['marks']==[]
        assert client.get('/api/marks/snapshot').json()==full


def test_mark_interval_and_category_selection_are_explicit_and_validated(tmp_path):
    from harmonic_weaver.lab.store import SessionStore
    store=SessionStore(tmp_path)
    try:
        for stamp,category in [(1.,'preparation'),(2.,'deployment'),(3.,'deployment')]:
            store.state.position_s=stamp
            store.mark(str(stamp),category=category)
        selected=store.marks_snapshot(start_s=1.,end_s=3.,category='deployment')
        assert [r['event']['source_time_s'] for r in selected['marks']]==[2.]
        assert selected['selection']['interval']=='[start_s,end_s)'
    finally:store.close()
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        assert client.get('/api/marks/snapshot',params={'start_s':1,'end_s':3,'category':'deployment'}).json()==selected
        for params in ({'start_s':3,'end_s':1},{'start_s':'nan'},{'end_s':-1},{'category':'unknown'}):
            assert client.get('/api/marks/snapshot',params=params).status_code==422


def test_epoch_filter_requires_session_and_does_not_infer_historical_epochs(tmp_path):
    from harmonic_weaver.lab.store import SessionStore
    store=SessionStore(tmp_path)
    try:
        store.mark('Known',observed_epoch=2)
        session_id=store.events()[0]['session_id']
        store.mark('Unknown')
    finally:store.close()
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        assert client.get('/api/marks/snapshot',params={'observed_epoch':2}).status_code==422
        selected=client.get('/api/marks/snapshot',params={'session_id':session_id,'observed_epoch':2}).json()
        assert len(selected['marks'])==1
        assert selected['marks'][0]['event']['payload']['text']=='Known'
        assert client.get('/api/marks/snapshot',params={'session_id':'other','observed_epoch':2}).json()['marks']==[]


def test_frozen_mark_cursor_repeats_after_new_marks(tmp_path):
    with TestClient(create_app(tmp_path),base_url='http://127.0.0.1') as client:
        client.post('/api/marks',json={'text':'Frozen'})
        frozen=client.get('/api/marks/snapshot').json()
        client.post('/api/marks',json={'text':'Later'})
        repeated=client.get('/api/marks/snapshot',params={'through_sequence':frozen['through_sequence']}).json()
        assert repeated==frozen
        assert client.get('/api/marks/snapshot',params={'through_sequence':0}).json()['marks']==[]
        for cursor in (-1,999999):
            assert client.get('/api/marks/snapshot',params={'through_sequence':cursor}).status_code==422


def test_transport_api_exposes_explicit_prefix_boundary_and_rejects_bad_inputs(tmp_path):
    from harmonic_weaver.lab.runtime import LaboratoryRuntime
    from harmonic_weaver.lab.store import SessionStore
    from harmonic_weaver.lab.routing import PreparedRoutes
    from test_lab_runtime import Library, Audio
    store = SessionStore(tmp_path, prepare=PreparedRoutes)
    library = Library()
    library.snapshot = lambda job: {'status':'building','duration_s':3.,'prefix_s':1.}
    runtime = LaboratoryRuntime(store, library=library, audio=Audio(), clock=lambda:0.)
    runtime.kind, runtime.job_id = 'video','test'
    runtime.start = lambda:None
    runtime.close = lambda:None
    try:
        with TestClient(create_app(tmp_path,store=store,runtime=runtime),base_url='http://127.0.0.1') as client:
            assert client.post('/api/transport',json={'tracked_prefix':True,'playing':True}).status_code == 200
            runtime.tick()
            assert client.get('/api/state').json()['session']['loop_end_s'] == 1.
            assert client.post('/api/transport',json={'tracked_prefix':False}).status_code == 200
            runtime.tick()
            assert client.get('/api/state').json()['session']['loop_end_s'] is None
            assert client.post('/api/transport',json={'tracked_prefix':'yes'}).status_code == 422
            assert client.post('/api/transport',json={'loop_end_s':999}).status_code == 422
            assert runtime.transport.loop_end_s is None
    finally:
        store.close()
