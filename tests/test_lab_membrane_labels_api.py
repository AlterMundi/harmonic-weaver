import copy
import json
from fastapi.testclient import TestClient

from harmonic_weaver.lab.app import create_app
from harmonic_weaver.lab.research.membrane_worker import run_frozen
from harmonic_weaver.lab.cache import atomic_json
from membrane_labels_fixture import seed


def test_label_api_binds_eval_sound_and_decoder_with_original_figure_preserved(
    tmp_path,
):
    ids = seed(tmp_path)

    class Runtime:
        library = None

        def start(self):
            pass

        def close(self):
            pass

    with TestClient(
        create_app(tmp_path, runtime=Runtime()), base_url="http://127.0.0.1"
    ) as client:
        signals = client.get(
            f"/api/research/r07-readout/projections/{ids[0]}/label-signals"
        )
        assert signals.status_code == 200, signals.text
        assert signals.json()["start_s"] == 0.2
        assert signals.json()["signals"]["zone.1.speed"]["unit"] == "T/s"
        cases = []
        config = None
        for i, ident in enumerate(ids):
            before = (tmp_path / "research/r07" / ident / "result.json").read_bytes()
            settings = {"signal_ids": ["zone.1.speed"], "method": "mean"}
            response = client.post(
                "/api/research/r07-readout/label",
                json={**settings, "projection_run_id": ident},
            )
            assert response.status_code == 200, response.text
            label = response.json()
            assert label["coverage"]["observed_fraction"] == 1
            assert (
                tmp_path / "research/r07" / ident / "result.json"
            ).read_bytes() == before
            cases.append(
                {
                    "id": f"case-{i}",
                    "role": "train" if i < 3 else "test",
                    "projection_run_id": ident,
                    "recording_id": "synthetic-same-take",
                    "subject_group": "synthetic",
                    "targets": label["targets"],
                    "computed_label": settings,
                }
            )
            config = {
                "reservation": "within_take",
                "attribute_ids": label["attribute_ids"],
                "attribute_units": label["attribute_units"],
                "cases": cases,
            }
        request = copy.deepcopy(config)
        request["cases"][-1]["targets"][0] += 1
        rejected = client.post("/api/research/r07-readout", json=request)
        assert rejected.status_code == 422 and "Computed label" in rejected.text
        result = client.post("/api/research/r07-readout", json=config)
        assert result.status_code == 200, result.text
        ident = result.json()["id"]
        restored = client.get(f"/api/research/r07-readout/{ident}/request")
        assert restored.status_code == 200, restored.text
        recovered = restored.json()
        assert recovered["label_settings"]["signal_ids"] == ["zone.1.speed"]
        assert recovered["cases"][0]["computed_label"]["method"] == "mean"
        repeated = client.post("/api/research/r07-readout", json=recovered)
        assert repeated.status_code == 200, repeated.text
        original_result = client.get(f"/api/research/r07-readout/{ident}/artifacts/result.json")
        repeated_id = repeated.json()["id"]
        assert client.get(f"/api/research/r07-readout/{repeated_id}/artifacts/result.json").content == original_result.content
        mixed = copy.deepcopy(recovered)
        mixed["cases"][-1]["computed_label"]["min_observations"] = 4
        mixed_result = client.post("/api/research/r07-readout", json=mixed)
        assert mixed_result.status_code == 200, mixed_result.text
        mixed_id = mixed_result.json()["id"]
        mixed_recovered = client.get(f"/api/research/r07-readout/{mixed_id}/request").json()
        assert "label_settings" not in mixed_recovered
        assert mixed_recovered["cases"][-1]["computed_label"]["min_observations"] == 4
        dataset = client.get(
            f"/api/research/r07-readout/{ident}/artifacts/dataset.json"
        ).json()
        assert all(
            c["computed_label"]["provenance"]["source"]["person_id"] == "one"
            for c in dataset["cases"]
        )
        assert (
            client.get(
                f"/api/research/r07-readout/{ident}/verification?recompute=true"
            ).status_code
            == 200
        )
        # Unit mismatch, unrelated feature, and audio tail cannot silently become labels.
        for settings in (
            {"signal_ids": ["zone.1.speed", "zone.1.acceleration"]},
            {"signal_ids": ["unknown"]},
        ):
            assert (
                client.post(
                    "/api/research/r07-readout/label",
                    json={"projection_run_id": ids[0], **settings},
                ).status_code
                == 422
            )
        tail_id = "f" * 32
        tail = tmp_path / "research/r07" / tail_id
        tail.mkdir()
        atomic_json(
            tail / "request.json",
            {
                "membrane": {"sample_rate": 8000},
                "grid_x": 5,
                "grid_y": 5,
                "start_sample": 14400,
                "stop_sample_exclusive": 15200,
            },
        )
        reference = json.loads(
            (tmp_path / "research/r07" / ids[0] / "source.json").read_text()
        )
        atomic_json(tail / "source.json", reference)
        run_frozen(tail)
        response = client.post(
            "/api/research/r07-readout/label",
            json={"projection_run_id": tail_id, "signal_ids": ["zone.1.speed"]},
        )
        assert response.status_code == 422 and "tail" in response.text
