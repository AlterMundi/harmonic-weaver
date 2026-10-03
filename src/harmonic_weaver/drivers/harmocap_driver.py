"""HarMoCAP OSC 1.1 source driver for Harmonic Weaver.

Receives the HarMoCAP multi-person stream (``/harmocap/v1/*``) and exposes
slots, keypoints and features as Source Frame v1 channels under
``source_id.channel`` addressing (CORE_DESIGN §2). Default ``source_id`` is
``harmocap``.

Engine seam (T4.2)
------------------
The engine registers a callback::

    def on_frame(
        source_id: str,
        channel_values: dict[str, tuple[float, int, float]],
    ) -> None: ...

Each value is ``(value, state, confidence)`` where ``state`` is the Source
Frame enum code: ``0=observed``, ``1=held``, ``2=invalid``. Keys in
``channel_values`` are bare channel names (no ``source_id.`` prefix); the
registry address is ``f"{source_id}.{name}"``.

Channel naming (per slot ``s`` in ``0..7``)
-------------------------------------------
* ``slot_{s}_present`` / ``slot_{s}_focused`` — 0.0 or 1.0
* ``slot_{s}_keypoint_{name}_{x|y|conf}`` — 17 COCO keypoints
* ``slot_{s}_{feature}`` — 21 features in kit ``feature_order``
  (``laban_weight_proxy`` is the kinetic-energy proxy cited as
  ``kinetic_energy`` in CORE_DESIGN examples)

Receiver rules (INTERFACE_SPEC / Source Frame)
----------------------------------------------
* Hello + calibration gating on matching
  ``(contract_id, calibration_generation, calibration_hash)``
* Monotonic discard of ``bundle_seq`` within a ``stream_id``
* New ``stream_id`` resets counters, leases and cached values
* Per-slot presence lease of 2000 ms (expiry → absent / channels invalid)
* Tombstone ``present=0`` clears the slot
* ``feat_state`` / ``kp_state`` propagate observed|held|invalid

Codec origin
------------
Minimal OSC 1.0 decode + HarMoCAP blob unpackers are copied from the portable
kit file::

    ~/Projects/HarMoCAP/harmocap-nico-kit/osc_codec.py
    sha256: 465f33f4de77e96ef15a841b776865cb5218a1132d789d5ae928b0f9b6fa3dd4

so this driver stays stdlib-only and kit-path-free at runtime. Encode/replay
helpers are not copied; tests build wire packets via the kit when needed.

Usage
-----
For an opt-in per-slot event preserving capture/receipt clocks::

    driver = HarMoCAPDriver(on_observation=my_observation_callback)

See ``docs/laboratory/OSC_OBSERVATIONS.md`` for version, lifecycle and migration.
Do not connect that partial event directly to the historical engine callback.

Feed raw UDP datagrams (preferred for tests)::

    driver = HarMoCAPDriver(on_frame=my_callback)
    driver.handle_datagram(raw_bytes)
    driver.tick()  # optional lease sweep between packets

Or bind a socket::

    driver.serve_udp("0.0.0.0", 9000)  # blocking
"""

from __future__ import annotations

from .observations import ObservationEvent

from collections import deque
import hashlib
import socket
import struct
import time
from dataclasses import dataclass, field
from typing import Callable, Iterable

# ---------------------------------------------------------------------------
# Constants (contract 1.1 / Source Frame v1)
# ---------------------------------------------------------------------------

OSC_NAMESPACE = "/harmocap/v1"
SOURCE_ID_DEFAULT = "harmocap"
N_SLOTS = 8
N_KEYPOINTS = 17
N_FEATURES = 24  # contrato 1.3 (feature_set 1.1): +tempo_bpm/beat_phase/tempo_conf
N_CALIB_PARAMS = 6
LEASE_MS_DEFAULT = 2000.0
LAYOUT_VERSION = "1"

STATE_OBSERVED = 0
STATE_HELD = 1
STATE_INVALID = 2

KEYPOINT_NAMES: tuple[str, ...] = (
    "nose",
    "left_eye",
    "right_eye",
    "left_ear",
    "right_ear",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
)

FEATURE_NAMES: tuple[str, ...] = (
    "qom",
    "contraction",
    "expansion",
    "vel_hand_l",
    "vel_hand_r",
    "vel_center",
    "smoothness_l",
    "smoothness_r",
    "symmetry",
    "verticality",
    "angle_elbow_l",
    "angle_elbow_r",
    "angle_knee_l",
    "angle_knee_r",
    "angle_shoulder_l",
    "angle_shoulder_r",
    "angle_hip_l",
    "angle_hip_r",
    "laban_weight_proxy",
    "laban_time_proxy",
    "laban_space_proxy",
    "tempo_bpm",
    "beat_phase",
    "tempo_conf",
)

# CORE_DESIGN §2 cites this as the kinetic-energy channel; it aliases feature 18.
KINETIC_ENERGY_FEATURE = "laban_weight_proxy"
KINETIC_ENERGY_ALIAS = "kinetic_energy"

OnFrame = Callable[[str, dict[str, tuple[float, int, float]]], None]

# Copied from harmocap-nico-kit/osc_codec.py
# sha256: 57ce3c93bd34d9dcc5a05eb7433aa9b09fb27cc810c6ff28e372cc4c865f35d9
_CODEC_SOURCE = (
    "HarMoCAP/harmocap-nico-kit/osc_codec.py"
    " sha256:57ce3c93bd34d9dcc5a05eb7433aa9b09fb27cc810c6ff28e372cc4c865f35d9"
)


# ---------------------------------------------------------------------------
# Minimal OSC 1.0 + blob decode (copied from kit osc_codec.py)
# ---------------------------------------------------------------------------


def _dec_string(data: bytes, ofs: int) -> tuple[str, int]:
    end = data.index(b"\x00", ofs)
    s = data[ofs:end].decode("utf-8")
    ofs = end + 1
    ofs += (4 - ofs % 4) % 4
    return s, ofs


def decode_message(data: bytes) -> tuple[str, list]:
    address, ofs = _dec_string(data, 0)
    typetags, ofs = _dec_string(data, ofs)
    args: list = []
    for tag in typetags[1:]:
        if tag == "i":
            args.append(struct.unpack_from(">i", data, ofs)[0])
            ofs += 4
        elif tag == "f":
            args.append(struct.unpack_from(">f", data, ofs)[0])
            ofs += 4
        elif tag == "h":
            args.append(struct.unpack_from(">q", data, ofs)[0])
            ofs += 8
        elif tag == "d":
            args.append(struct.unpack_from(">d", data, ofs)[0])
            ofs += 8
        elif tag == "s":
            s, ofs = _dec_string(data, ofs)
            args.append(s)
        elif tag == "b":
            n = struct.unpack_from(">i", data, ofs)[0]
            ofs += 4
            args.append(data[ofs : ofs + n])
            ofs += n + (4 - n % 4) % 4
        else:
            raise ValueError(f"unsupported OSC typetag: {tag}")
    return address, args


def decode_bundle(data: bytes) -> list[tuple[str, list]]:
    """Decode an OSC bundle (or a lone message) to ``[(address, args), ...]``."""
    if not data.startswith(b"#bundle\x00"):
        return [decode_message(data)]
    ofs = 8 + 8  # '#bundle\0' + timetag
    out: list[tuple[str, list]] = []
    while ofs < len(data):
        n = struct.unpack_from(">i", data, ofs)[0]
        ofs += 4
        out.append(decode_message(data[ofs : ofs + n]))
        ofs += n
    return out


def unpack_keypoints(blob: bytes) -> list[tuple[float, float, float]]:
    if len(blob) != N_KEYPOINTS * 12:
        raise ValueError(f"keypoints blob length {len(blob)} != {N_KEYPOINTS * 12}")
    return [struct.unpack_from(">fff", blob, i * 12) for i in range(N_KEYPOINTS)]


def unpack_kp_state(blob: bytes) -> list[tuple[int, int, int]]:
    size = struct.calcsize(">BIQ")
    if len(blob) != N_KEYPOINTS * size:
        raise ValueError(f"kp_state blob length {len(blob)} != {N_KEYPOINTS * size}")
    return [struct.unpack_from(">BIQ", blob, i * size) for i in range(N_KEYPOINTS)]


def unpack_features(blob: bytes) -> list[float]:
    if len(blob) != N_FEATURES * 4:
        raise ValueError(f"features blob length {len(blob)} != {N_FEATURES * 4}")
    return list(struct.unpack(f">{N_FEATURES}f", blob))


def unpack_feat_state(blob: bytes) -> list[int]:
    if len(blob) != N_FEATURES:
        raise ValueError("feat_state blob length incorrect")
    return list(struct.unpack(f">{N_FEATURES}B", blob))


def unpack_calibration_params(blob: bytes) -> list[float]:
    if len(blob) != N_CALIB_PARAMS * 4:
        raise ValueError("calibration blob length incorrect")
    return list(struct.unpack(f">{N_CALIB_PARAMS}f", blob))


def calibration_hash(params_blob: bytes) -> str:
    """SHA-256/128 over layout descriptor + normative calibration bytes."""
    descriptor = f"calibration:v{LAYOUT_VERSION}:>{N_CALIB_PARAMS}f".encode()
    return hashlib.sha256(descriptor + params_blob).hexdigest()[:32]


# ---------------------------------------------------------------------------
# Channel catalogue
# ---------------------------------------------------------------------------


def channel_names(*, include_kinetic_energy_alias: bool = True) -> list[str]:
    """Return every channel name this driver may emit (all 8 slots)."""
    names: list[str] = []
    for s in range(N_SLOTS):
        names.append(f"slot_{s}_present")
        names.append(f"slot_{s}_focused")
        for kp in KEYPOINT_NAMES:
            names.append(f"slot_{s}_keypoint_{kp}_x")
            names.append(f"slot_{s}_keypoint_{kp}_y")
            names.append(f"slot_{s}_keypoint_{kp}_conf")
        for feat in FEATURE_NAMES:
            names.append(f"slot_{s}_{feat}")
        if include_kinetic_energy_alias:
            names.append(f"slot_{s}_{KINETIC_ENERGY_ALIAS}")
    return names


def registry_address(channel: str, source_id: str = SOURCE_ID_DEFAULT) -> str:
    """Compose CORE_DESIGN ``source_id.channel`` addressing."""
    return f"{source_id}.{channel}"


# ---------------------------------------------------------------------------
# Slot state
# ---------------------------------------------------------------------------


@dataclass
class _SlotState:
    present: bool = False
    focused: bool = False
    keypoints: list[tuple[float, float, float]] | None = None
    kp_state: list[tuple[int, int, int]] | None = None
    features: list[float] | None = None
    feat_state: list[int] | None = None
    last_data_ms: float = 0.0
    captured_frame_id: int = -1
    captured_at_us: int | None = None


@dataclass
class _Hello:
    stream_id: str
    contract_id: str
    calibration_generation: int
    calibration_state: str
    calibration_hash: str
    frame_w: int
    frame_h: int
    schema_version: str = ""
    feature_set_version: str = ""


@dataclass
class _Calibration:
    generation: int
    hash: str
    params: list[float] = field(default_factory=list)


@dataclass
class DriverStats:
    bundles: int = 0
    dropped_old: int = 0
    gated: int = 0
    stream_resets: int = 0
    lease_expiries: int = 0
    tombstones: int = 0
    decode_errors: int = 0
    callback_errors: int = 0
    dropped_slot_frame: int = 0


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


class HarMoCAPDriver:
    """Receive OSC and emit legacy snapshots or opt-in per-slot observations."""

    def __init__(
        self,
        on_frame: OnFrame | None = None,
        *,
        on_observation: Callable[[ObservationEvent], None] | None = None,
        source_id: str = SOURCE_ID_DEFAULT,
        lease_ms: float = LEASE_MS_DEFAULT,
        include_kinetic_energy_alias: bool = True,
    ) -> None:
        if on_frame is not None and on_observation is not None:
            raise ValueError(
                "Choose legacy on_frame or versioned on_observation, not both"
            )
        self.on_frame = on_frame
        self.on_observation = on_observation
        self.source_id = source_id
        self.lease_ms = float(lease_ms)
        self.include_kinetic_energy_alias = include_kinetic_energy_alias

        self._retired_streams = deque(maxlen=64)
        self.stream_id: str | None = None
        self.hello: _Hello | None = None
        self.calibration: _Calibration | None = None
        self.last_seq: int = -1
        self.slots: dict[int, _SlotState] = {s: _SlotState() for s in range(N_SLOTS)}
        self.stats = DriverStats()
        self._channel_catalogue = channel_names(
            include_kinetic_energy_alias=include_kinetic_energy_alias
        )

    # -- public API ---------------------------------------------------------

    def handle_datagram(self, data: bytes, *, now_ms: float | None = None) -> None:
        """Ingest one OSC datagram (hello, calibration, or person bundle)."""
        now = self._now_ms(now_ms)
        try:
            msgs = decode_bundle(data)
        except Exception:
            self.stats.decode_errors += 1
            return
        if not msgs:
            return
        if (
            self.on_observation is not None
            and msgs[0][1]
            and msgs[0][1][0] in self._retired_streams
        ):
            self.stats.dropped_old += 1
            self._expire_leases(now)
            return
        addr0 = msgs[0][0]
        try:
            if addr0.endswith("/hello"):
                self._on_hello(msgs[0][1], now_ms=now)
            elif addr0.endswith("/calibration"):
                self._on_calibration(msgs[0][1], now_ms=now)
            elif addr0.endswith("/meta"):
                self._on_person_bundle(msgs, now_ms=now)
        except (ValueError, TypeError, IndexError, OverflowError, struct.error):
            if self.on_observation is None:
                raise
            self.stats.decode_errors += 1
        # Lease sweep after any packet so silence is observed even without tick().
        self._expire_leases(now)

    def tick(self, now_ms: float | None = None) -> None:
        """Sweep presence leases; call when no packets arrive for a while."""
        self._expire_leases(self._now_ms(now_ms))

    def reset(self) -> None:
        """Clear all receiver state (as if the process restarted)."""
        self._invalidate_observations("receiver_reset", self._now_ms(None))
        if self.on_observation is not None and self.stream_id is not None:
            self._retired_streams.append(self.stream_id)
        self.stream_id = None
        self.hello = None
        self.calibration = None
        self.last_seq = -1
        self.slots = {s: _SlotState() for s in range(N_SLOTS)}

    def serve_udp(
        self,
        host: str = "0.0.0.0",
        port: int = 9000,
        *,
        seconds: float = 0.0,
    ) -> DriverStats:
        """Blocking UDP receive loop (stdlib socket). ``seconds=0`` runs forever."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((host, port))
        sock.settimeout(0.1)
        t0 = time.monotonic()
        try:
            while not seconds or (time.monotonic() - t0) < seconds:
                try:
                    data, _ = sock.recvfrom(4096)
                except socket.timeout:
                    self.tick()
                    continue
                self.handle_datagram(data)
        finally:
            sock.close()
        return self.stats

    def snapshot(self) -> dict[str, tuple[float, int, float]]:
        """Current channel map for all 8 slots (no callback)."""
        return self._build_channel_values()

    # -- stream / handshake -------------------------------------------------

    def _now_ms(self, now_ms: float | None) -> float:
        return time.monotonic() * 1000.0 if now_ms is None else float(now_ms)

    def _reset_stream(self, stream_id: str, *, now_ms: float | None = None) -> None:
        self._invalidate_observations("stream_changed", self._now_ms(now_ms))
        if self.on_observation is not None and self.stream_id is not None:
            self._retired_streams.append(self.stream_id)
        self.stream_id = stream_id
        self.hello = None
        self.calibration = None
        self.last_seq = -1
        self.slots = {s: _SlotState() for s in range(N_SLOTS)}
        self.stats.stream_resets += 1

    def _is_gated(self) -> bool:
        """True while frames must not be consumed."""
        if self.hello is None or self.calibration is None:
            return True
        if self.hello.calibration_generation != self.calibration.generation:
            return True
        if self.hello.calibration_hash != self.calibration.hash:
            return True
        return False

    def _on_hello(self, args: list, *, now_ms: float | None = None) -> None:
        # /hello: stream_id, schema, feature_set, producer, model, config_hash,
        # contract_id, layout, calib_gen, calib_state, calib_hash, eff_from(h),
        # frame_w, frame_h
        if self.on_observation is not None:
            if len(args) < 14 or not isinstance(args[0], str) or not args[0]:
                raise ValueError("invalid observation hello")
            for index in (8, 12, 13):
                if type(args[index]) is not int or args[index] < 0:
                    raise ValueError("invalid observation hello integer")
        stream_id = args[0]
        if stream_id != self.stream_id:
            self._reset_stream(stream_id, now_ms=now_ms)
        if self.hello is not None and (
            self.hello.contract_id != args[6]
            or self.hello.calibration_generation != int(args[8])
            or self.hello.calibration_hash != str(args[10])
        ):
            self._invalidate_observations(
                "contract_or_calibration_changed", self._now_ms(now_ms)
            )
        self.hello = _Hello(
            stream_id=stream_id,
            schema_version=args[1],
            feature_set_version=args[2],
            contract_id=args[6],
            calibration_generation=int(args[8]),
            calibration_state=str(args[9]),
            calibration_hash=str(args[10]),
            frame_w=int(args[12]),
            frame_h=int(args[13]),
        )

    def _on_calibration(self, args: list, *, now_ms: float | None = None) -> None:
        # /calibration: stream_id, generation, hash, effective_from(h), params_blob
        if self.on_observation is not None:
            if len(args) < 5 or not isinstance(args[0], str) or not args[0]:
                raise ValueError("invalid observation calibration")
            if type(args[1]) is not int or args[1] < 0:
                raise ValueError("invalid observation calibration generation")
            unpack_calibration_params(args[4])
        stream_id = args[0]
        if stream_id != self.stream_id:
            self._reset_stream(stream_id, now_ms=now_ms)
        params_blob = args[4]
        expected = calibration_hash(params_blob)
        if expected != args[2]:
            # Corrupt / mismatched calibration — reject, keep previous if any.
            return
        if self.calibration is not None and (
            self.calibration.generation != int(args[1])
            or self.calibration.hash != str(args[2])
        ):
            self._invalidate_observations("calibration_changed", self._now_ms(now_ms))
        self.calibration = _Calibration(
            generation=int(args[1]),
            hash=str(args[2]),
            params=unpack_calibration_params(params_blob),
        )

    # -- person bundles -----------------------------------------------------

    def _on_person_bundle(self, msgs: list[tuple[str, list]], *, now_ms: float) -> None:
        meta = msgs[0][1]
        if len(meta) < 11:
            self.stats.decode_errors += 1
            return
        if self.on_observation is not None:
            if not isinstance(meta[0], str) or not meta[0]:
                raise ValueError("invalid observation stream")
            for index in (1, 2, 6, 8, 9, 10):
                if type(meta[index]) is not int or meta[index] < 0:
                    raise ValueError("invalid observation metadata integer")
        stream_id = meta[0]
        captured_frame_id = int(meta[1])
        seq = int(meta[2])
        contract_id = meta[5]
        calibration_generation = int(meta[6])

        if stream_id != self.stream_id:
            self._reset_stream(stream_id, now_ms=now_ms)

        if seq <= self.last_seq:
            self.stats.dropped_old += 1
            return
        if self.on_observation is None:
            self.last_seq = seq

        if self._is_gated():
            self.stats.gated += 1
            return

        assert self.hello is not None
        if contract_id != self.hello.contract_id:
            self.stats.gated += 1
            return
        if calibration_generation != self.hello.calibration_generation:
            self.stats.gated += 1
            return

        self.stats.bundles += 1
        person = self._parse_person_messages(msgs[1:])
        if person is None:
            return

        slot = person["slot"]
        if not (0 <= slot < N_SLOTS):
            return
        if self.on_observation is not None and (
            captured_frame_id <= self.slots[slot].captured_frame_id
            or (
                self.slots[slot].captured_at_us is not None
                and int(meta[8]) <= self.slots[slot].captured_at_us
            )
        ):
            self.stats.dropped_slot_frame += 1
            return
        if not person["present"]:
            self.stats.tombstones += 1
            self.last_seq = seq
            self.slots[slot] = _SlotState(present=False, last_data_ms=now_ms)
            self.slots[slot].captured_frame_id = captured_frame_id
            self.slots[slot].captured_at_us = int(meta[8])
            self._emit_observation(slot, now_ms, meta, "tombstone")
            self._emit(now_ms)
            return

        st = _SlotState(
            present=True,
            focused=bool(person.get("focused", False)),
            keypoints=person["keypoints"],
            kp_state=person["kp_state"],
            features=person["features"],
            feat_state=person["feat_state"],
            last_data_ms=now_ms,
            captured_frame_id=captured_frame_id,
            captured_at_us=int(meta[8]),
        )
        event = (
            self._make_observation(slot, st, now_ms, meta, "person_bundle")
            if self.on_observation is not None
            else None
        )
        self.slots[slot] = st
        self.last_seq = seq
        self._emit_observation(slot, now_ms, meta, "person_bundle", event=event)
        self._emit(now_ms)

    def _parse_person_messages(self, msgs: Iterable[tuple[str, list]]) -> dict | None:
        persons: dict[int, dict] = {}
        for addr, args in msgs:
            # /harmocap/v1/person/{slot}/{field}
            parts = addr.split("/")
            if len(parts) < 6 or parts[3] != "person":
                continue
            try:
                slot = int(parts[4])
            except ValueError:
                continue
            field = parts[5]
            p = persons.setdefault(slot, {"slot": slot})
            if field == "present":
                p["present"] = bool(args[0])
            elif field == "focused":
                p["focused"] = bool(args[0])
            elif field == "keypoints":
                p["keypoints"] = unpack_keypoints(args[0])
            elif field == "kp_state":
                p["kp_state"] = unpack_kp_state(args[0])
            elif field == "features":
                p["features"] = unpack_features(args[0])
            elif field == "feat_state":
                p["feat_state"] = unpack_feat_state(args[0])
            # bbox ignored for channel map (not in CORE_DESIGN channel set)

        if not persons:
            return None
        if self.on_observation is not None and len(persons) != 1:
            self.stats.decode_errors += 1
            return None
        # One person per bundle (contract 1.1); take the only entry.
        p = next(iter(persons.values()))
        if not p.get("present", False):
            p["present"] = False
            return p
        # Require dense payloads for present persons.
        for key in ("keypoints", "kp_state", "features", "feat_state"):
            if key not in p:
                return None
        p["present"] = True
        return p

    # -- leases -------------------------------------------------------------

    def _expire_leases(self, now_ms: float) -> None:
        changed = False
        for slot, st in list(self.slots.items()):
            if not st.present:
                continue
            if now_ms - st.last_data_ms > self.lease_ms:
                self.slots[slot] = _SlotState(
                    present=False,
                    last_data_ms=now_ms,
                    captured_frame_id=st.captured_frame_id,
                    captured_at_us=st.captured_at_us,
                )
                self._emit_observation(slot, now_ms, None, "lease_expired")
                self.stats.lease_expiries += 1
                changed = True
        if changed:
            self._emit(now_ms)

    # -- emit ---------------------------------------------------------------

    def _invalidate_observations(self, reason, now_ms):
        if self.on_observation is None:
            return
        for slot, state in list(self.slots.items()):
            if state.present:
                self.slots[slot] = _SlotState(present=False, last_data_ms=now_ms)
                self._emit_observation(slot, now_ms, None, reason)

    def _make_observation(self, slot, state, now_ms, meta, reason):
        channels = (
            self._channels_for_present_slot(slot, state)
            if state.present
            else self._channels_for_absent_slot(slot)
        )
        return ObservationEvent(
            source_id=self.source_id,
            stream_id=self.stream_id or "",
            slot=slot,
            event_kind="slot_update" if state.present else "slot_invalidated",
            reason=reason,
            contract_id=self.hello.contract_id if self.hello else None,
            calibration_generation=self.hello.calibration_generation
            if self.hello
            else None,
            calibration_hash=self.hello.calibration_hash if self.hello else None,
            captured_frame_id=int(meta[1]) if meta else None,
            bundle_seq=int(meta[2]) if meta else None,
            captured_at_us=int(meta[8]) if meta else None,
            processed_at_us=int(meta[9]) if meta else None,
            queued_for_send_at_us=int(meta[10]) if meta else None,
            received_at_us=round(now_ms * 1000),
            channel_values=channels,
        )

    def _emit_observation(self, slot, now_ms, meta, reason, *, event=None):
        if self.on_observation is None:
            return
        if event is None:
            event = self._make_observation(slot, self.slots[slot], now_ms, meta, reason)
        try:
            self.on_observation(event)
        except Exception:
            self.stats.callback_errors += 1

    def _emit(self, now_ms: float) -> None:
        if self.on_frame is None:
            return
        try:
            self.on_frame(self.source_id, self._build_channel_values())
        except Exception:
            # A consumer raising (e.g. engine range validation on an
            # out-of-contract value) must never kill the UDP listener: a dead
            # listener ends ingestion permanently with no re-hello path (S13).
            self.stats.callback_errors += 1

    def _build_channel_values(self) -> dict[str, tuple[float, int, float]]:
        out: dict[str, tuple[float, int, float]] = {}
        for s in range(N_SLOTS):
            st = self.slots[s]
            if st.present and st.keypoints is not None:
                out.update(self._channels_for_present_slot(s, st))
            else:
                out.update(self._channels_for_absent_slot(s))
        return out

    def _channels_for_absent_slot(
        self, slot: int
    ) -> dict[str, tuple[float, int, float]]:
        inv = (0.0, STATE_INVALID, 0.0)
        ch: dict[str, tuple[float, int, float]] = {
            f"slot_{slot}_present": (0.0, STATE_OBSERVED, 1.0),
            f"slot_{slot}_focused": inv,
        }
        for kp in KEYPOINT_NAMES:
            ch[f"slot_{slot}_keypoint_{kp}_x"] = inv
            ch[f"slot_{slot}_keypoint_{kp}_y"] = inv
            ch[f"slot_{slot}_keypoint_{kp}_conf"] = inv
        for feat in FEATURE_NAMES:
            ch[f"slot_{slot}_{feat}"] = inv
        if self.include_kinetic_energy_alias:
            ch[f"slot_{slot}_{KINETIC_ENERGY_ALIAS}"] = inv
        return ch

    def _channels_for_present_slot(
        self, slot: int, st: _SlotState
    ) -> dict[str, tuple[float, int, float]]:
        assert st.keypoints is not None and st.kp_state is not None
        assert st.features is not None and st.feat_state is not None
        ch: dict[str, tuple[float, int, float]] = {
            f"slot_{slot}_present": (1.0, STATE_OBSERVED, 1.0),
            f"slot_{slot}_focused": (
                1.0 if st.focused else 0.0,
                STATE_OBSERVED,
                1.0,
            ),
        }
        for i, name in enumerate(KEYPOINT_NAMES):
            x, y, conf = st.keypoints[i]
            kp_st = int(st.kp_state[i][0])
            if kp_st == STATE_INVALID:
                ch[f"slot_{slot}_keypoint_{name}_x"] = (0.0, STATE_INVALID, 0.0)
                ch[f"slot_{slot}_keypoint_{name}_y"] = (0.0, STATE_INVALID, 0.0)
                ch[f"slot_{slot}_keypoint_{name}_conf"] = (0.0, STATE_INVALID, 0.0)
            else:
                # conf is effective reliability from the producer (decays when held).
                c = float(conf) if kp_st == STATE_OBSERVED else float(conf)
                ch[f"slot_{slot}_keypoint_{name}_x"] = (float(x), kp_st, c)
                ch[f"slot_{slot}_keypoint_{name}_y"] = (float(y), kp_st, c)
                ch[f"slot_{slot}_keypoint_{name}_conf"] = (float(conf), kp_st, c)

        for i, name in enumerate(FEATURE_NAMES):
            f_st = int(st.feat_state[i])
            if f_st == STATE_INVALID:
                ch[f"slot_{slot}_{name}"] = (0.0, STATE_INVALID, 0.0)
            else:
                # Features have no separate wire confidence; held keeps value
                # with reduced confidence so validity policy can filter.
                conf = 1.0 if f_st == STATE_OBSERVED else 0.5
                ch[f"slot_{slot}_{name}"] = (float(st.features[i]), f_st, conf)

        if self.include_kinetic_energy_alias:
            ch[f"slot_{slot}_{KINETIC_ENERGY_ALIAS}"] = ch[
                f"slot_{slot}_{KINETIC_ENERGY_FEATURE}"
            ]
        return ch


__all__ = [
    "FEATURE_NAMES",
    "KEYPOINT_NAMES",
    "KINETIC_ENERGY_ALIAS",
    "LEASE_MS_DEFAULT",
    "N_FEATURES",
    "N_KEYPOINTS",
    "N_SLOTS",
    "SOURCE_ID_DEFAULT",
    "STATE_HELD",
    "STATE_INVALID",
    "STATE_OBSERVED",
    "DriverStats",
    "HarMoCAPDriver",
    "calibration_hash",
    "channel_names",
    "decode_bundle",
    "decode_message",
    "registry_address",
    "unpack_calibration_params",
    "unpack_feat_state",
    "unpack_features",
    "unpack_kp_state",
    "unpack_keypoints",
]
