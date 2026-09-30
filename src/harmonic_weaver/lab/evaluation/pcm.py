"""Offline adapter to Shaper's production block kernel; no audio device opened."""
import hashlib
import importlib
import json
import math
from pathlib import Path
import sys
import struct

import numpy as np
from pydantic import Field
from ..contracts import Contract, Number
from ..cache import sha256_file


class PCMSettings(Contract):
    enabled: bool = False
    sample_rate: int = Field(default=48000, ge=8000, le=192000)
    block_frames: int = Field(default=256, ge=16, le=4096)
    shaper_master: Number = Field(default=.8, ge=0, le=1)
    tail_s: Number = Field(default=0, ge=0, le=2)
    engine_sha256: str | None = None


def engine_modules():
    # SHAPER_DIR is selected by the launcher; never guess or switch repositories.
    import os
    selected = os.environ.get("SHAPER_DIR")
    if selected:
        path = str(Path(selected).expanduser().resolve()/"src")
        if path not in sys.path: sys.path.insert(0, path)
    try:
        modules = [importlib.import_module("harmonic_shaper."+name)
                   for name in ("audio_engine", "state", "laboratory", "audio_levels", "config")]
    except ImportError as exc:
        raise ValueError("PCM requiere Shaper instalado o SHAPER_DIR explícito") from exc
    if selected and Path(modules[0].__file__).resolve().parent.parent != Path(selected).expanduser().resolve()/"src":
        raise ValueError("Shaper ya importado de otro checkout; iniciar un proceso nuevo con SHAPER_DIR correcto")
    if not hasattr(modules[0].AudioEngine, "render_block"):
        raise ValueError("Este Shaper no tiene render_block; usar la rama offline-render compatible")
    return modules


def engine_identity():
    modules = engine_modules()
    files = {Path(m.__file__).name: sha256_file(m.__file__) for m in modules}
    digest = hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return {"files": files, "code_sha256": digest, "module_path": str(Path(modules[0].__file__).parent)}


def canonicalize_wav(path):
    """Clear libsndfile's wall-clock PEAK timestamp in logical-render WAVs.

    Samples and peak values remain unchanged. Zero means no physical recording
    timestamp; capture provenance belongs in the manifest, never this field.
    """
    with Path(path).open('r+b') as handle:
        header = handle.read(12)
        if header[:4] != b'RIFF' or header[8:] != b'WAVE':
            raise ValueError("Expected RIFF WAVE output")
        limit = struct.unpack('<I',header[4:8])[0]+8
        offset = 12
        while offset+8 <= limit:
            handle.seek(offset)
            kind, size = struct.unpack('<4sI',handle.read(8))
            if kind == b'PEAK' and size >= 8:
                handle.seek(offset+12)
                handle.write(struct.pack('<I',0))
            offset += 8+size+(size%2)


class PCMWriter:
    def __init__(self, path, settings, *, begin_s, start_s, end_s):
        import soundfile as sf
        modules = engine_modules()
        identity = engine_identity()
        if settings.engine_sha256 and settings.engine_sha256 != identity['code_sha256']:
            raise ValueError("El motor Shaper cambió desde la corrida congelada")
        self.identity, self.settings = identity, settings
        self.store = modules[1].VoiceParameterStore()
        self.store.set_master_gain(settings.shaper_master)
        self.input = modules[2].LaboratoryInput(self.store)
        self.store.laboratory_input = self.input
        self.engine = modules[0].AudioEngine(self.store,sample_rate=settings.sample_rate,
                                             block_size=settings.block_frames)
        self.begin = begin_s
        self.first = round((start_s-begin_s)*settings.sample_rate)
        self.last = round((end_s-begin_s)*settings.sample_rate)
        self.final = self.last+round(settings.tail_s*settings.sample_rate)
        self.index, self.sequence, self.written = 0, 0, 0
        self.peak, self.squares = 0., 0.
        self.path = Path(path)
        self.audio = sf.SoundFile(self.path,mode='w',samplerate=settings.sample_rate,
                                  channels=2,format='WAV',subtype='FLOAT')
        self.frames_path = self.path.with_suffix('.voice-frames.jsonl')
        self.frames = self.frames_path.open('w')

    def _apply(self, targets):
        self.sequence += 1
        self.input.apply(dict(schema_version=1,owner='offline',sequence=self.sequence,
                              lease_ms=2000,voices=targets),now=self.index/self.settings.sample_rate)

    def _render_until(self, limit):
        while self.index < limit:
            count=self.settings.block_frames
            pcm=self.engine.render_block(now=self.index/self.settings.sample_rate)
            lo=max(self.first-self.index,0); hi=min(self.final-self.index,count)
            if hi>lo:
                portion=pcm[lo:hi]
                self.audio.write(portion); self.written+=len(portion)
                self.peak=max(self.peak,float(np.max(np.abs(portion))))
                self.squares+=float(np.sum(portion.astype(np.float64)**2))
                frame=self.engine.voice_frame()
                frame.update(clock='logical_render', source_time_s=self.begin+self.index/self.settings.sample_rate,
                             audio_file_sample_start=self.index+lo-self.first,
                             crop_block_start=lo,crop_block_end=hi)
                self.frames.write(json.dumps(frame,sort_keys=True,allow_nan=False)+'\n')
            self.index+=count

    def feed(self, row):
        # Controls are consumed at the first production block boundary at/after
        # their logical timestamp. Never split synthesis blocks at control ticks.
        sample=round(row['control_time_s']*self.settings.sample_rate)
        self._render_until(sample)
        self._apply(row['targets'])

    def finish(self):
        self._render_until(self.last)
        self._apply([])
        self._render_until(self.final)
        self.close()
        canonicalize_wav(self.path)
        return {"file":self.path.name,"sha256":sha256_file(self.path),
                "voice_frames":self.frames_path.name,"voice_frames_sha256":sha256_file(self.frames_path),
                "settings":self.settings.model_dump(),"engine":self.identity,
                "samples":self.written,"channels":2,"subtype":"FLOAT", "peak_chunk_timestamp":"zero; logical render has no physical recording timestamp",
                "peak":self.peak,"rms":math.sqrt(self.squares/max(1,2*self.written)),
                "stage":"post_shape_master_soft_limiter",
                "clock":"logical_render","control_schedule":"first block boundary at/after control timestamp",
                "max_control_quantization_s":self.settings.block_frames/self.settings.sample_rate,
                "segment_source_start_s":self.begin+self.first/self.settings.sample_rate,
                "tail_samples":self.final-self.last,
                "numpy_version":np.__version__,
                "soundfile_version":__import__("soundfile").__version__,
                "libsndfile_version":__import__("soundfile").__libsndfile_version__}

    def close(self):
        self.audio.close(); self.frames.close()
