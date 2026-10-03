"""Portable temporal parameters, never observations, media or calibration."""
from pathlib import Path
from uuid import uuid4
from typing import Literal
import re
from pydantic import Field
from ..contracts import Contract
from ..cache import atomic_json


class Configuration(Contract):
    axes:Literal['0,1','0,2','1,2']='0,1'
    scale:float=Field(default=100,ge=1,le=10000)
    center_x:float=0
    center_y:float=0
    speed:float=Field(default=1,ge=.1,le=10)
    loop:bool=False
    max_gap_s:float=Field(default=.1,ge=.001,le=10)


class Preset(Contract):
    schema_version:Literal[1]=1
    name:str=Field(min_length=1,max_length=80)
    config:Configuration


class SpatialViewPresets:
    model=Preset
    directory='research/r09-view-presets'
    def __init__(self,data_dir):
        self.root=Path(data_dir)/self.directory
        self.root.mkdir(mode=0o700,parents=True,exist_ok=True)

    def load(self,ident):
        if not isinstance(ident,str) or not re.fullmatch('[a-f0-9]{32}',ident):raise ValueError('Invalid spatial view preset id')
        path=self.root/f'{ident}.json'
        if path.is_symlink() or not path.is_file() or path.stat().st_size>65536:raise ValueError('Regular bounded spatial view preset required')
        return self.model.model_validate_json(path.read_text())

    def save(self,preset):
        preset=self.model.model_validate(preset);ident=uuid4().hex
        atomic_json(self.root/f'{ident}.json',preset.model_dump())
        return {'id':ident,**preset.model_dump()}

    def list(self):
        rows=[]
        for path in sorted(self.root.glob('*.json')):
            try:rows.append({'id':path.stem,**self.load(path.stem).model_dump()})
            except (OSError,ValueError):continue
        return rows


from .spatial_compare import Settings

class ComparisonPreset(Contract):
    schema_version:Literal[1]=1
    name:str=Field(min_length=1,max_length=80)
    config:Settings

class SpatialComparisonPresets(SpatialViewPresets):
    model=ComparisonPreset
    directory='research/r09-comparison-presets'
