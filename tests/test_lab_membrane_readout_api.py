import copy
import json
import shutil

from fastapi.testclient import TestClient

from harmonic_weaver.lab.app import create_app
from membrane_readout_fixture import seed


def test_verified_figures_api_repeat_restart_and_explicit_recomputation(tmp_path):
    request = seed(tmp_path)
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        config = {key: value for key, value in request.items() if key != "cases"}
        assert (
            client.post(
                "/api/research/r07-readout/configuration", json=config
            ).status_code
            == 200
        )
        bad = copy.deepcopy(request)
        bad["cases"][-1]["recording_id"] = bad["cases"][0]["recording_id"]
        assert client.post("/api/research/r07-readout", json=bad).status_code == 422
        assert client.get("/api/research/r07-readout").json() == []
        results = []
        for _ in range(2):
            started = client.post("/api/research/r07-readout", json=request)
            assert started.status_code == 200, started.text
            ident = started.json()["id"]
            result = client.get(
                f"/api/research/r07-readout/{ident}/artifacts/result.json"
            )
            assert result.status_code == 200
            results.append(result.content)
            restored = client.get(f"/api/research/r07-readout/{ident}/request")
            assert restored.status_code == 200, restored.text
            from harmonic_weaver.lab.research.membrane_readout import Request
            assert restored.json() == Request.model_validate(request).model_dump()

            assert (
                result.json()["mean_squared_error"]["rms_full"][0]
                < result.json()["mean_squared_error"]["training_mean"][0] / 1000
            )
            assert (
                client.get(f"/api/research/r07-readout/{ident}/verification").json()[
                    "read_verification"
                ]
                == "integrity_only"
            )
            assert (
                client.get(
                    f"/api/research/r07-readout/{ident}/verification?recompute=true"
                ).json()["read_verification"]
                == "numerically_recomputed"
            )
            assert (
                client.get(
                    f"/api/research/r07-readout/{ident}/artifacts/source.json"
                ).status_code
                == 422
            )
        assert results[0] == results[1]
    # Frozen decoding remains possible without the original source figures/PCM.
    shutil.rmtree(tmp_path / "synthetic-readout-sources")
    shutil.rmtree(tmp_path / "research/r07")
    with TestClient(create_app(tmp_path), base_url="http://127.0.0.1") as client:
        assert len(client.get("/api/research/r07-readout").json()) == 2
        result = client.get(f"/api/research/r07-readout/{ident}/artifacts/result.json")
        assert result.content == results[1]
        assert (
            client.get(
                f"/api/research/r07-readout/{ident}/verification?recompute=true"
            ).status_code
            == 200
        )
        dataset = client.get(
            f"/api/research/r07-readout/{ident}/artifacts/dataset.json"
        ).json()
        assert dataset["provider"] == "r07_snapshot"
        assert all(c["source_origin_s"] == 0 for c in dataset["cases"])
        assert [c["projection_run_id"] for c in dataset["cases"]] == [
            c["projection_run_id"] for c in request["cases"]
        ]
        # Hash alteration is detected during read; incomplete staging is invisible.
        (tmp_path / "research/r07-readout/.incomplete.staging").mkdir()
        (tmp_path / f"research/r07-readout/{ident}/result.json").write_text(
            json.dumps({})
        )
        assert (
            client.get(
                f"/api/research/r07-readout/{ident}/artifacts/result.json"
            ).status_code
            == 422
        )
        assert len(client.get("/api/research/r07-readout").json()) == 1
