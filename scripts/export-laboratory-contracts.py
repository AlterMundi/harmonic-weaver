"""Regenerate reviewable JSON schemas and synthetic six-voice fixtures."""
import json
from pathlib import Path

from harmonic_weaver.lab.contracts import (
    EffectiveVoice, MotionFrame, Person, Joint, PERSISTED_CONTRACTS, Preset, VoiceFrame,
)

root = Path(__file__).resolve().parents[1] / "docs/laboratory/contracts"
root.mkdir(parents=True, exist_ok=True)
for contract in PERSISTED_CONTRACTS:
    (root / f"{contract.__name__}.schema.json").write_text(
        json.dumps(contract.model_json_schema(), indent=2, ensure_ascii=False) + "\n")
fixtures = root / "fixtures"
fixtures.mkdir(exist_ok=True)
preset = Preset(id="six-zones")
(fixtures / "preset-six-zones.json").write_text(preset.model_dump_json(indent=2) + "\n")
motion = MotionFrame(source_id="synthetic", stream_id="fixture", sequence=0, source_time_s=0.,
                     available_monotonic_s=0., timestamp_origin="synthetic", width=1280, height=720,
                     persons=[Person(person_id="person-1", joints=[
                         Joint(index=i, position=[.5 + (i % 2) * .2, .2 + (i // 2) * .06],
                               confidence=1., state="observed") for i in range(17)])])
(fixtures / "motion-frame.json").write_text(motion.model_dump_json(indent=2) + "\n")
voices = VoiceFrame(sample_index=0, sample_rate=48000, block_frames=256,
                    generated_monotonic_s=0., running=True,
                    voices=[EffectiveVoice(voice_id=7100+i, harmonic_n=i, frequency_hz=40.4*i,
                                           gain=.1, phase_rad=i*.1, envelope=1., pan=0.,
                                           shape=0., releasing=False) for i in range(1, 7)])
(fixtures / "voice-frame-six.json").write_text(voices.model_dump_json(indent=2) + "\n")
