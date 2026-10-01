"""Exact sampled model-state projection; no carrier extrapolation or physical cymatics."""
from pathlib import Path
from typing import Literal
import numpy as np
import soundfile as sf
from pydantic import Field,model_validator
from ..contracts import Contract,Number
from ..cache import sha256_file
from .resonator_artifacts import verify as verify_arm
from .mechanism_run import verify as verify_pair


class Settings(Contract):
    arm:Literal['single','excited','mapped']='single'
    points:int=Field(default=512,ge=2,le=4096)
    stride:int=Field(default=1,ge=1,le=32)
    weights:list[Number]|None=Field(default=None,min_length=6,max_length=32)
    phase_offsets_rad:list[Number]|None=Field(default=None,min_length=6,max_length=32)
    scale_x:Number=Field(default=1,gt=0,le=100)
    scale_y:Number=Field(default=1,gt=0,le=100)

    @model_validator(mode='after')
    def bounds(self):
        if self.weights is not None and any(abs(v)>100 for v in self.weights):
            raise ValueError('Projection weights within ±100 required')
        if self.phase_offsets_rad is not None and any(abs(v)>1000 for v in self.phase_offsets_rad):
            raise ValueError('Projection offsets within ±1000 required')
        return self


class PlaybackSettings(Contract):
    follow_audio:bool=True
    refresh_hz:Number=Field(default=10,ge=1,le=30)
    preview_gain:Number=Field(default=1,ge=0,le=10)
    loop_audio:bool=False


class Configuration(Contract):
    schema_version:Literal[1]=1
    settings:Settings=Field(default_factory=Settings)
    playback:PlaybackSettings|None=None


class Request(Settings):
    start_sample:int=Field(default=0,ge=0)


def project(folder,request,*,reader=None):
    request=Request.model_validate(request);folder=Path(folder)
    if reader is not None:
        manifest,fingerprint=reader.prepare(folder,request.arm)
        arm=folder if request.arm=='single' else folder/request.arm
    elif request.arm=='single':manifest=verify_arm(folder);arm=folder
    else:
        verify_pair(folder);arm=folder/request.arm;manifest=verify_arm(arm)
    if 'quadrature.wav' not in manifest['output_hashes']:
        raise ValueError('This historical run has no measured model quadrature')
    n=manifest['pcm']['voice_channels'];sr=manifest['pcm']['sample_rate']
    weights=np.array(request.weights if request.weights is not None else [1.]*n,dtype=float)
    offsets=np.array(request.phase_offsets_rad if request.phase_offsets_rad is not None else [0.]*n,dtype=float)
    if weights.shape!=(n,) or offsets.shape!=(n,) or not np.isfinite(weights).all() or not np.isfinite(offsets).all() or np.any(np.abs(weights)>100) or np.any(np.abs(offsets)>1000):
        raise ValueError('One finite projection weight ±100 and phase offset ±1000 per voice required')
    frames=manifest['levels']['frames']
    if request.start_sample>=frames:raise ValueError('Projection starts beyond PCM')
    count=min(frames-request.start_sample,(request.points-1)*request.stride+1)
    with sf.SoundFile(arm/'voices.wav') as audible,sf.SoundFile(arm/'quadrature.wav') as quadrature:
        audible.seek(request.start_sample);quadrature.seek(request.start_sample)
        y=audible.read(count,dtype='float64',always_2d=True)[::request.stride]
        x=quadrature.read(count,dtype='float64',always_2d=True)[::request.stride]
    if x.shape!=y.shape or x.shape[1]!=n or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError('Invalid projection components')
    cos=np.cos(offsets)*weights;sin=np.sin(offsets)*weights
    points=np.column_stack(((x*cos-y*sin).sum(axis=1)*request.scale_x,
                            (x*sin+y*cos).sum(axis=1)*request.scale_y))
    indices=request.start_sample+np.arange(len(points))*request.stride
    preparation=manifest['preparation'];selection=preparation.get('selection') or preparation['excitation']['selection']
    # Read-only response remains tied to the files verified before the bounded read.
    if reader is not None:reader.check(folder,request.arm,fingerprint)
    else:
        for name in ('voices.wav','quadrature.wav'):
            if (arm/name).is_symlink() or sha256_file(arm/name)!=manifest['output_hashes'][name]:
                raise ValueError('Projection components changed during read')
    return {'schema_version':1,'settings':request.model_dump(),'sample_rate':sr,'total_frames':frames,'voices':n,
        'sample_indices':indices.tolist(),'elapsed_s':((indices+1)/sr).tolist(),
        'source_time_s':(selection['start_s']+(indices+1)/sr).tolist(),
        'tail':(indices>=preparation['segment_frames']).tolist(),'points':points.tolist(),
        'component_hashes':{name:manifest['output_hashes'][name] for name in ('voices.wav','quadrature.wav')},
        'verification_mode':'cached_hashes_with_file_metadata_checks' if reader is not None else 'full_hashes_per_call',
        'limits':['Projection sums every stored voice with explicit weights and phase offsets',
            'Actual sampled model state, no future carrier extrapolation or Hilbert inference',
            'Sample timestamps are right edges of exact PCM steps; tail is instrument activity',
            'Stride is display decimation without antialias filtering, not an audio-rate conversion',
            'No automatic scale normalization or physical cymatic interpretation',
            'Local integrity only, not signed custody; metadata cache assumes ordinary filesystem semantics',
            'UI playback latency and physical audio/display synchronization still unmeasured']}
