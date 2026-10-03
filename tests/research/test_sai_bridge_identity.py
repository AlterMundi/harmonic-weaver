"""Regression cases for Nico's PR #36 review: repeated times are separate units."""
import json

import pytest

from research.laboratory.sai_bridge.adapter import common_observed, read_models
from research.laboratory.sai_bridge.synthetic import motion_frame


def row(stream, value, *, source="session", person="p0", time=0., state="observed"):
    return {"source_id": source, "stream_id": stream, "person_id": person,
            "source_time_s": time,
            "signals": {"probe": {"state": state, "value": value, "unit": "1"}}}


def test_repeated_times_match_their_epoch_even_when_conditions_reorder_or_omit_epochs():
    a = [row("loop0", 1.), row("loop1", 2.), row("seek0", 3.)]
    b = [row("seek0", 30.), row("loop0", 10.), row("loop1", None, state="missing")]
    assert common_observed(a, b, "probe") == [
        (("session", "loop0", "p0", 0.), 1., 10.),
        (("session", "seek0", "p0", 0.), 3., 30.),
    ]
    # Removing one epoch cannot renumber another into its place.
    assert common_observed(a, b[:1], "probe") == [
        (("session", "seek0", "p0", 0.), 3., 30.),
    ]


@pytest.mark.parametrize("field", ["source_id", "stream_id", "person_id"])
def test_identical_times_do_not_match_different_sources_streams_or_people(field):
    left = row("epoch", 1.)
    other = dict(left, **{field: "other"})
    assert common_observed([left], [other], "probe") == []


@pytest.mark.parametrize("side", ["left", "right"])
def test_duplicate_units_raise_even_if_one_signal_is_missing(side):
    valid = row("epoch", 1.)
    missing = row("epoch", None, state="missing")
    a, b = ([valid, missing], [valid]) if side == "left" else ([valid], [valid, missing])
    with pytest.raises(ValueError, match="duplicate comparison unit"):
        common_observed(a, b, "probe")


def test_time_only_legacy_records_require_explicit_identity():
    legacy = {"source_time_s": 0., "signals": {}}
    with pytest.raises(ValueError, match="missing comparison identity"):
        common_observed([legacy], [], "probe")


def test_replay_preserves_identity_and_separates_same_time_sessions():
    first = [motion_frame(k/30, k, left=[.3 + k*.01, .4], stream="loop0") for k in range(10)]
    second = [motion_frame(k/30, k, left=[.3 + k*.02, .4], stream="loop1") for k in range(10)]
    frames = first + second
    outputs = read_models(frames, algorithms=("local",))["local"]
    assert [(r["source_id"], r["stream_id"], r["person_id"], r["sequence"])
            for r in outputs] == [(f.source_id, f.stream_id, "p0", f.sequence) for f in frames]
    json.dumps(outputs, allow_nan=False)
    common = common_observed(outputs, list(reversed(outputs)), "zone.6.speed")
    assert common and {key[1] for key, _, _ in common} == {"loop0", "loop1"}
    assert all(x == y for _, x, y in common)


def test_reusing_a_stream_after_a_loop_is_rejected_before_model_evaluation():
    frames = [motion_frame(0., 0, stream="old"), motion_frame(.1, 1, stream="old"),
              motion_frame(0., 0, stream="new"), motion_frame(0., 0, stream="old")]
    with pytest.raises(ValueError, match="distinct stream_id"):
        read_models(frames, algorithms=())


def test_source_change_resets_history_even_if_stream_name_is_reused():
    first = [motion_frame(k/30, k, left=[.3 + k*.01, .4]) for k in range(10)]
    second = [motion_frame(k/30, k, left=[.4 - k*.01, .5]) for k in range(10)]
    for frame in second:
        frame.source_id = "different_session"
    combined = read_models(first + second, algorithms=("local",))["local"]
    fresh = read_models(second, algorithms=("local",))["local"]
    assert combined[len(first):] == fresh
