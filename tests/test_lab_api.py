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
