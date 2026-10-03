"""Adapter around the preserved kinetic controller, without a second audio path."""
from functools import lru_cache
import importlib.util
from pathlib import Path

from .contracts import FeatureFrame, Signal


@lru_cache(maxsize=1)
def baseline_module():
    source = Path(__file__).resolve().parents[3] / "research/movement-consonance/consonance/driver.py"
    if not source.exists():
        raise RuntimeError("the frozen baseline requires a complete Weaver checkout (editable installation)")
    spec = importlib.util.spec_from_file_location("weaver_lab_frozen_driver", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FrozenBaseline:
    def __init__(self, preset):
        self.preset = preset.model_copy(deep=True)
        self.frame = None
        self.person_id = None
        self.reset()

    def reset(self):
        driver = baseline_module()
        self.controls = driver.LiveControls()
        response = self.preset.response.model_dump()
        response["pluck_enabled"] = int(response["pluck_enabled"])
        response["zones"] = {str(i): zone for i, zone in enumerate(response["zones"], 1)}
        # The global master is applied once, downstream by the runtime/Shaper.
        # Frequency is also synthesized downstream; only the unchanged controller's
        # gain/detune/phase signals are used, so its historical f1 limit is irrelevant.
        self.controls.update({**response, "master": 1., "f1": 40.4})
        self.session = driver.ConsonanceSession(
            driver.ShaperOut("127.0.0.1", 0, self.preset.fundamental_hz, .03, True),
            controls=self.controls, pred_tau=self.preset.algorithm.horizon_s)
        self.frame = None
        self.person_id = None

    def observe(self, frame, person_id, now):
        if self.frame is not None and (frame.source_time_s < self.frame.source_time_s or
                                       frame.source_time_s-self.frame.source_time_s > self.preset.algorithm.max_gap_s):
            self.reset()
        self.frame, self.person_id = frame, person_id
        return self.tick(now)

    def tick(self, now):
        frame = self.frame
        person = next((p for p in frame.persons if p.person_id == self.person_id), None) if frame else None
        persons = []
        if person:
            joints = {j.index: j for j in person.joints}
            keypoints, states = [], []
            for index in range(17):
                joint = joints.get(index)
                valid = joint is not None and joint.state == "observed" and joint.position is not None
                keypoints.append((*joint.position[:2], joint.confidence) if valid else (0., 0., 0.))
                states.append((0 if valid else 2, 0, 0))
            persons = [dict(slot_id=0, focused=True, present=True, keypoints=keypoints, kp_state=states,
                            captured_at_us=round(frame.source_time_s*1e6))]
        self.session.update({"stream_id": f"{frame.stream_id}:{self.person_id}" if frame else "none",
                             "persons": persons}, now=now)
        signals = {}
        for zone in self.session.state()["zones"]:
            n = zone["n"]
            state = "observed" if zone["observed"] else "missing"
            for key, unit, value in (("gain", "1", zone["gain"]), ("detune", "1", zone["detune"]),
                                      ("phase_deg", "deg", zone["phase_deg"]), ("speed", "T/s", zone["speed"]),
                                      ("acceleration", "T/s2", zone["acceleration"])):
                signals[f"zone.{n}.{key}"] = Signal(value=float(value) if state == "observed" else None,
                                                     unit=unit, state=state)
        return FeatureFrame(source_time_s=frame.source_time_s if frame else 0., available_monotonic_s=now,
                            person_id=self.person_id, algorithm_id="baseline", signals=signals,
                            diagnostics={"normalization": "frozen adaptive torso", "reference": "camera",
                                         "source": "2089ed3 kinetic controller; master applied downstream"})
