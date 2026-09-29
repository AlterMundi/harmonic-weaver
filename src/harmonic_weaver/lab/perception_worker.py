"""Standalone HarMoCAP worker: run using its own Python/torch environment.

Only standard library imports at module load, so --probe needs no model/GPU.
stdout is JSONL IPC; third-party logs go to stderr. Files decode sequentially
with original PTS; cameras use HarMoCAP's bounded latest-frame capture.
"""
from __future__ import annotations

import argparse
import base64
from contextlib import redirect_stdout
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys
import time


def file_hash(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def probe(harmocap_dir):
    import ultralytics
    root = Path(harmocap_dir)
    tracker_root = Path(ultralytics.__file__).parent / "cfg/trackers"
    return {
        "protocol": 1,
        "worker_sha256": file_hash(__file__),
        "code": {name: file_hash(root / "src/harmocap" / name) for name in ("perception.py", "identity.py", "capture.py")},
        "packages": {name: importlib.metadata.version(name) for name in ("ultralytics", "torch", "av", "opencv-python")},
        "trackers": {name: file_hash(tracker_root / name) for name in ("bytetrack.yaml", "botsort.yaml")},
    }


def file_frames(path):
    import av
    import numpy as np
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        origin = float(stream.start_time * stream.time_base) if stream.start_time is not None else None
        fps = float(stream.average_rate or 30)
        for sequence, frame in enumerate(container.decode(stream)):
            if frame.pts is not None and frame.time_base is not None:
                raw_time = float(frame.pts * frame.time_base)
                if origin is None:
                    origin = raw_time - sequence / fps
                stamp = raw_time - origin
                timestamp_origin = "pts"
            else:
                stamp = sequence / fps
                timestamp_origin = "index_fps"
            image = frame.to_ndarray(format="bgr24")
            rotation = frame.rotation
            if rotation % 90:
                raise ValueError("video display rotation must be a multiple of 90 degrees")
            if rotation:
                image = np.ascontiguousarray(np.rot90(image, rotation // 90))
            yield image, {
                "sequence": sequence, "source_time_s": stamp,
                "source_pts": frame.pts,
                "time_base_num": frame.time_base.numerator if frame.time_base else None,
                "time_base_den": frame.time_base.denominator if frame.time_base else None,
                "timestamp_origin": timestamp_origin,
                "duration_s": float(frame.duration * frame.time_base) if frame.duration and frame.time_base else None,
                "available_monotonic_s": time.monotonic(),
            }


def camera_frames(index, config):
    from harmocap.capture import LatchingCamera
    camera = LatchingCamera(index, width=config["camera_width"], height=config["camera_height"],
                            fps=config["camera_fps"]).start()
    started = time.monotonic()
    origin = None
    last_frame = started
    try:
        while True:
            camera.wait_for_frame(.05)
            latest = camera.get_latest()
            if latest is None:
                if time.monotonic() - last_frame > 5:
                    raise RuntimeError("camera produced no frame for five seconds")
                continue
            image, sequence, stamp_us = latest
            last_frame = time.monotonic()
            if origin is None:
                origin = stamp_us / 1e6
            yield image, {"sequence": sequence, "source_time_s": stamp_us / 1e6 - origin,
                          "timestamp_origin": "capture", "captured_monotonic_s": stamp_us / 1e6,
                          "available_monotonic_s": stamp_us / 1e6}
    finally:
        camera.stop()


def run(args, emit):
    import cv2
    from harmocap.identity import SlotManager
    from harmocap.perception import PoseBackend
    config = json.loads(args.config_json)
    checkpoint = Path(config["checkpoint"])
    if not checkpoint.is_file():
        raise FileNotFoundError(f"checkpoint must already exist: {checkpoint}")
    backend = PoseBackend(realtime_checkpoint=str(checkpoint), fallback_checkpoint=str(checkpoint),
                          device=config["device"], imgsz=config["imgsz"], conf=config["confidence"],
                          max_det=config["max_detections"], tracker=config["tracker"])
    slots = SlotManager(max_slots=config["max_slots"], reacquisition={"enabled": config["reacquisition"]})
    generations = [0] * config["max_slots"]
    if args.video:
        import av
        with av.open(args.video) as container:
            stream = container.streams.video[0]
            duration = float(stream.duration * stream.time_base) if stream.duration else (
                container.duration / 1e6 if container.duration else None)
            emit({"type": "metadata", "duration_s": duration})
    frames = file_frames(args.video) if args.video else camera_frames(args.camera, config)
    count = 0
    for image, timing in frames:
        dets, _, _, (width, height) = backend.track_frame(image)
        events = slots.update(dets, int(timing["source_time_s"] * 1e6), aspect=width / height)
        persons = []
        for event in events:
            if event.slot_reset:
                generations[event.slot_id] += 1
            if event.detection is None:
                continue
            joints = []
            for index, (x, y, confidence) in enumerate(event.detection.keypoints_iso):
                valid = confidence >= config["joint_confidence"]
                joints.append({"index": index, "position": [x, y] if valid else None,
                               "confidence": confidence, "state": "observed" if valid else "missing"})
            persons.append({"person_id": f"slot-{event.slot_id}-generation-{generations[event.slot_id]}", "joints": joints})
        frame = {"schema_version": 1, "source_id": args.source_id, "stream_id": args.stream_id,
                 **timing, "width": width, "height": height, "coordinate_frame": "camera_isotropic",
                 "unit": "frame_height", "dimensions": 2, "persons": persons}
        frame["available_monotonic_s"] = time.monotonic()
        message = {"type": "frame", "frame": frame}
        if not args.video:
            preview = cv2.resize(image, (min(width, 960), round(height * min(width, 960) / width)))
            ok, jpg = cv2.imencode(".jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if ok:
                message["jpeg"] = base64.b64encode(jpg).decode("ascii")
        emit(message)
        count += 1
    emit({"type": "complete", "frames": count})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--harmocap-dir", required=True)
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--video")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--source-id", default="camera")
    parser.add_argument("--stream-id", default="worker")
    parser.add_argument("--config-json")
    args = parser.parse_args()
    sys.path.insert(0, str(Path(args.harmocap_dir) / "src"))
    protocol_out = sys.stdout
    def emit(message):
        protocol_out.write(json.dumps(message, allow_nan=False, separators=(",", ":")) + "\n")
        protocol_out.flush()
    try:
        with redirect_stdout(sys.stderr):
            if args.probe:
                emit(probe(args.harmocap_dir))
            else:
                run(args, emit)
    except Exception as exc:
        emit({"type": "error", "error": f"{type(exc).__name__}: {exc}"})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
