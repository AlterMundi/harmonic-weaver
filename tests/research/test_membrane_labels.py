from unittest.mock import patch

import pytest

from harmonic_weaver.lab.research.membrane_labels import calculate


def document():
    return {
        "rows": [{"time_s": i / 10, "values": [float(i), -float(i)]} for i in range(4)],
        "unit": "T/s",
        "provenance": {"trace_sha256": "a" * 64},
        "duplicate_control_holds_excluded": 3,
    }


def aggregate(doc, **settings):
    class Evaluation:
        def report(self, _):
            return {"manifest": {"runs": [{"sha256": "a" * 64}]}}

    bound = {
        "evaluation_id": "a" * 32,
        "run_index": 0,
        "start_s": 0.0,
        "end_s": 0.4,
        "trace_sha256": "a" * 64,
        "projection_sha256": "b" * 64,
        "paths": {},
    }
    with (
        patch(
            "harmonic_weaver.lab.research.membrane_labels.context", return_value=bound
        ),
        patch(
            "harmonic_weaver.lab.research.membrane_labels.body_snapshot",
            return_value=doc,
        ),
    ):
        return calculate(
            object(),
            Evaluation(),
            {
                "projection_run_id": "b" * 32,
                "signal_ids": ["a", "b"],
                "max_gap_s": 0.11,
                **settings,
            },
        )


@pytest.mark.parametrize(
    "method,expected",
    [
        ("mean", [1.5, -1.5]),
        ("rms", [3.5**0.5, 3.5**0.5]),
        ("std", [1.25**0.5, 1.25**0.5]),
        ("peak_abs", [3.0, 3.0]),
    ],
)
def test_sample_statistics_units_and_support(method, expected):
    result = aggregate(document(), method=method)
    assert result["targets"] == pytest.approx(expected)
    assert result["attribute_units"] == ["T/s", "T/s"]
    assert result["coverage"]["duplicate_control_holds_excluded"] == 3
    assert result["coverage"]["observed"] == 4
    assert result["window"] == {"start_s": 0.0, "end_s": 0.4}


def test_missing_coverage_is_explicit_and_does_not_impute():
    doc = document()
    doc["rows"][1] = {
        "time_s": 0.1,
        "values": None,
        "invalid_signals": {"a": "pose missing"},
    }
    with pytest.raises(ValueError, match="coverage"):
        aggregate(doc)
    result = aggregate(doc, min_observed_fraction=0.7, max_gap_s=0.21)
    assert result["targets"] == pytest.approx([5 / 3, -5 / 3])
    assert result["coverage"]["invalid_causes"] == {"a: pose missing": 1}
    with pytest.raises(ValueError, match="gap"):
        aggregate(doc, min_observed_fraction=0.7)


def test_edges_and_insufficient_observations_rejected():
    doc = document()
    doc["rows"] = doc["rows"][2:]
    with pytest.raises(ValueError, match="gap"):
        aggregate(doc)
    with pytest.raises(ValueError, match="coverage"):
        aggregate(doc, min_observations=3)
