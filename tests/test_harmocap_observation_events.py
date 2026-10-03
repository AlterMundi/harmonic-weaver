import copy
import json
from dataclasses import replace
import pytest
from harmonic_weaver.drivers.harmocap_driver import HarMoCAPDriver
from harmonic_weaver.drivers.observations import SlotObservationHistory
from test_harmocap_driver import TWO_PERSONS, frame_to_wire, handshake_bytes


def fixture():
    rows = [
        json.loads(line)
        for line in TWO_PERSONS.read_text().splitlines()
        if line.strip()
    ]
    return rows[0], next(
        row for row in rows if row.get("persons") and len(row["persons"]) >= 2
    )


def ready():
    hello, frame = fixture()
    events = []
    driver = HarMoCAPDriver(on_observation=events.append, lease_ms=100)
    for packet in handshake_bytes(hello):
        driver.handle_datagram(packet, now_ms=1000)
    return driver, events, frame


def test_two_person_bundle_emits_only_updated_slot_and_preserves_clocks():
    driver, events, frame = ready()
    packets = frame_to_wire(frame, first_seq=10)
    for packet in packets:
        driver.handle_datagram(packet, now_ms=1000)
    assert len(events) == 2 and len({e.slot for e in events}) == 2
    for event in events:
        assert all(
            key.startswith(f"slot_{event.slot}_") for key in event.channel_values
        )
        assert event.captured_frame_id == frame["captured_frame_id"]
        assert (
            event.captured_at_us == frame["captured_at_us"]
            and event.received_at_us == 1000000
        )
        assert (
            event.capture_clock != event.receipt_clock
            and event.scope == "updated_slot_only"
        )
    history = SlotObservationHistory()
    for event in events:
        history.consume(event)
    assert len(
        {(r["slot"], r["channel"], r["captured_frame_id"]) for r in history.rows}
    ) == len(history.rows)
    assert all(r["derivative_per_producer_s"] is None for r in history.rows)
    driver.handle_datagram(packets[0], now_ms=1001)
    assert len(events) == 2 and driver.stats.dropped_old == 1
    for packet in frame_to_wire(frame, first_seq=20):
        driver.handle_datagram(packet, now_ms=1002)
    assert len(events) == 2 and driver.stats.dropped_slot_frame == 2


def test_expiry_watermark_prevents_late_resurrection_and_reset_invalidates():
    driver, events, frame = ready()
    for packet in frame_to_wire(frame, 10):
        driver.handle_datagram(packet, now_ms=1000)
    driver.tick(now_ms=1101)
    assert len(events) == 4 and all(e.reason == "lease_expired" for e in events[2:])
    assert all(e.captured_at_us is None for e in events[2:])
    for packet in frame_to_wire(frame, 20):
        driver.handle_datagram(packet, now_ms=1102)
    assert len(events) == 4
    new = copy.deepcopy(frame)
    new["captured_frame_id"] += 1
    new["captured_at_us"] += 33333
    for packet in frame_to_wire(new, 30):
        driver.handle_datagram(packet, now_ms=1103)
    assert len(events) == 6
    driver.reset()
    assert len(events) == 8 and all(e.reason == "receiver_reset" for e in events[-2:])


def test_consumer_derivative_only_new_observed_and_gap_not_fake_motion():
    driver, events, frame = ready()
    for packet in frame_to_wire(frame, 10):
        driver.handle_datagram(packet, now_ms=1000)
    first = events[0]
    key = next(k for k, v in first.channel_values.items() if v[1] == 0)
    history = SlotObservationHistory(max_gap_us=100000)
    first = replace(
        first,
        channel_values={key: (1.0, 0, 1.0)},
        captured_at_us=1000000,
        captured_frame_id=1,
    )
    history.consume(first)
    history.consume(first)
    history.consume(
        replace(
            first,
            channel_values={key: (2.0, 0, 1.0)},
            captured_at_us=1050000,
            captured_frame_id=2,
        )
    )
    assert len(history.rows) == 2 and history.rows[-1][
        "derivative_per_producer_s"
    ] == pytest.approx(20.0)
    history.consume(
        replace(
            first,
            channel_values={key: (2.0, 1, 0.5)},
            captured_at_us=1060000,
            captured_frame_id=3,
        )
    )
    history.consume(
        replace(
            first,
            channel_values={key: (8.0, 0, 1.0)},
            captured_at_us=1070000,
            captured_frame_id=4,
        )
    )
    assert history.rows[-1]["derivative_per_producer_s"] is None
    history.consume(
        replace(
            first,
            channel_values={key: (100.0, 0, 1.0)},
            captured_at_us=2070000,
            captured_frame_id=5,
        )
    )
    assert history.rows[-1]["cause"] == "capture_gap_or_nonincreasing_clock"
    with pytest.raises(ValueError):
        HarMoCAPDriver(on_frame=lambda *a: None, on_observation=lambda e: None)


def test_stream_and_calibration_changes_invalidate_and_retire_late_stream():
    driver, events, frame = ready()
    hello, _ = fixture()
    for packet in frame_to_wire(frame, 10):
        driver.handle_datagram(packet, now_ms=1000)
    calibrated = copy.deepcopy(hello)
    calibrated["calibration_generation"] += 1
    for packet in handshake_bytes(calibrated):
        driver.handle_datagram(packet, now_ms=1001)
    assert all(e.reason == "contract_or_calibration_changed" for e in events[-2:])
    new = copy.deepcopy(frame)
    new["calibration_generation"] += 1
    new["captured_at_us"] += 33333
    new["captured_frame_id"] += 1
    for packet in frame_to_wire(new, 20):
        driver.handle_datagram(packet, now_ms=1002)
    assert all(
        e.calibration_generation == calibrated["calibration_generation"]
        for e in events[-2:]
    )
    restarted = copy.deepcopy(calibrated)
    restarted["stream_id"] = "new-stream"
    for packet in handshake_bytes(restarted):
        driver.handle_datagram(packet, now_ms=1003)
    assert all(e.reason == "stream_changed" for e in events[-2:])
    previous = len(events)
    for packet in handshake_bytes(hello) + frame_to_wire(frame, 50):
        driver.handle_datagram(packet, now_ms=1004)
    assert driver.stream_id == "new-stream" and len(events) == previous
    new["stream_id"] = "new-stream"
    for packet in frame_to_wire(new, 0):
        driver.handle_datagram(packet, now_ms=1005)
    assert len(events) == previous + 2


def test_tombstone_keeps_clock_watermark_and_callback_failure_isolated():
    driver, events, frame = ready()
    for packet in frame_to_wire(frame, 10):
        driver.handle_datagram(packet, now_ms=1000)
    tombstone = copy.deepcopy(frame)
    tombstone["captured_frame_id"] += 1
    tombstone["captured_at_us"] += 1000
    for person in tombstone["persons"]:
        person["present"] = False
    for packet in frame_to_wire(tombstone, 20):
        driver.handle_datagram(packet, now_ms=1001)
    assert all(e.reason == "tombstone" for e in events[-2:])
    late = copy.deepcopy(frame)
    late["captured_frame_id"] += 2
    for packet in frame_to_wire(late, 30):
        driver.handle_datagram(packet, now_ms=1002)
    assert len(events) == 4
    late["captured_at_us"] += 2000
    driver.on_observation = lambda event: (_ for _ in ()).throw(
        ValueError("consumer failure")
    )
    for packet in frame_to_wire(late, 40):
        driver.handle_datagram(packet, now_ms=1003)
    assert driver.stats.callback_errors == 2 and driver.stats.bundles > 0


def encode_messages(messages):
    from test_harmocap_driver import osc_codec

    return osc_codec.encode_bundle(
        [
            osc_codec.encode_message(
                address,
                [
                    ("h", value)
                    if type(value) is int and not -(2**31) <= value < 2**31
                    else value
                    for value in arguments
                ],
            )
            for address, arguments in messages
        ]
    )


def test_malformed_packets_do_not_replace_valid_slot_or_poison_sequence():
    from harmonic_weaver.drivers.harmocap_driver import decode_bundle

    driver, events, frame = ready()
    packet = frame_to_wire(frame, 10)[0]
    messages = decode_bundle(packet)
    broken = copy.deepcopy(messages)
    broken[0][1][1] = "not-a-frame-id"
    driver.handle_datagram(encode_messages(broken), now_ms=1000)
    assert driver.stats.decode_errors == 1 and not events and driver.last_seq == -1
    # Nonfinite observed values fail before committing state or sequence.
    import struct

    bad = copy.deepcopy(messages)
    bad[0][1][2] = 1000
    for address, arguments in bad:
        if address.endswith("/features"):
            arguments[0] = struct.pack(">f", float("nan")) + arguments[0][4:]
        elif address.endswith("/feat_state"):
            arguments[0] = bytes([0]) + arguments[0][1:]
    driver.handle_datagram(encode_messages(bad), now_ms=1000)
    assert driver.stats.decode_errors == 2 and not events and driver.last_seq == -1
    driver.handle_datagram(packet, now_ms=1001)
    assert len(events) == 1 and driver.last_seq == 10
    driver.handle_datagram(
        encode_messages([("/harmocap/v1/hello", ["unknown"])]), now_ms=1002
    )
    assert driver.stream_id == frame["stream_id"] and len(events) == 1


def test_multi_person_payload_is_rejected_and_trace_preserves_lifecycle():
    from harmonic_weaver.drivers.harmocap_driver import decode_bundle

    driver, events, frame = ready()
    packets = frame_to_wire(frame, 10)
    messages = decode_bundle(packets[0]) + decode_bundle(packets[1])[1:]
    driver.handle_datagram(encode_messages(messages), now_ms=1000)
    assert driver.stats.decode_errors == 1 and not events and driver.last_seq == -1
    for packet in packets:
        driver.handle_datagram(packet, now_ms=1001)
    driver.tick(now_ms=1102)
    rows = json.loads(
        json.dumps([event.to_dict() for event in events], allow_nan=False)
    )
    assert len(rows) == 4
    assert rows[0]["captured_at_us"] == frame["captured_at_us"]
    assert rows[0]["bundle_seq"] == 10 and rows[1]["bundle_seq"] == 11
    assert (
        rows[-1]["captured_frame_id"] is None and rows[-1]["reason"] == "lease_expired"
    )
    assert all(row["received_at_us"] >= 1001000 for row in rows)


def test_versioned_event_rejects_clock_relabelling_and_cross_slot_payload():
    driver, events, frame = ready()
    driver.handle_datagram(frame_to_wire(frame, 10)[0], now_ms=1000)
    event = events[0]
    with pytest.raises(ValueError, match="clock domains"):
        replace(event, capture_clock="receiver_monotonic_us")
    with pytest.raises(ValueError, match="another slot"):
        replace(event, channel_values={"slot_7_wrong": (1.0, 0, 1.0)})
    with pytest.raises(ValueError, match="identity and capture time"):
        replace(event, captured_frame_id=None)
    with pytest.raises(ValueError, match="max_gap_us"):
        SlotObservationHistory(max_gap_us=0)


def test_consumer_late_capture_does_not_replace_derivative_baseline():
    driver, events, frame = ready()
    driver.handle_datagram(frame_to_wire(frame, 10)[0], now_ms=1000)
    base = events[0]
    key = next(k for k, value in base.channel_values.items() if value[1] == 0)

    def sample(frame_id, at, value):
        return replace(
            base,
            captured_frame_id=frame_id,
            captured_at_us=at,
            channel_values={key: (value, 0, 1.0)},
        )

    history = SlotObservationHistory()
    history.consume(sample(1, 1000000, 1.0))
    history.consume(sample(2, 1050000, 2.0))
    history.consume(sample(3, 1040000, 100.0))
    history.consume(sample(4, 1100000, 3.0))
    assert len(history.rows) == 3
    assert history.rows[-1]["derivative_per_producer_s"] == pytest.approx(20.0)
    history.consume(replace(sample(5, 1150000, 4.0), contract_id="another-contract"))
    assert history.rows[-1]["derivative_per_producer_s"] is None
