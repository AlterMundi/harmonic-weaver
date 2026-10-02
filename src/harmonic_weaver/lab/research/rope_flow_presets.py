"""Portable temporal parameters, never observations, media or calibration."""
from pathlib import Path
from uuid import uuid4
from typing import Literal
import re
from pydantic import Field
from ..contracts import Contract
from ..cache import atomic_json
from .rope_flow import Settings


class Configuration(Contract):
    frames:int=Field(default=10,ge=2,le=120)
    settings:Settings=Field(default_factory=Settings)


class Preset(Contract):
    schema_version:Literal[1]=1
    name:str=Field(min_length=1,max_length=80)
    config:Configuration


class RopeFlowPresets:
    def __init__(self,data_dir):
        self.root=Path(data_dir)/'research/r08-flow-presets'
        self.root.mkdir(mode=0o700,parents=True,exist_ok=True)

    def load(self,ident):
        if not isinstance(ident,str) or not re.fullmatch('[a-f0-9]{32}',ident):raise ValueError('Invalid flow preset id')
        path=self.root/f'{ident}.json'
        if path.is_symlink() or not path.is_file() or path.stat().st_size>65536:raise ValueError('Regular bounded flow preset required')
        return Preset.model_validate_json(path.read_text())

    def save(self,preset):
        preset=Preset.model_validate(preset);ident=uuid4().hex
        atomic_json(self.root/f'{ident}.json',preset.model_dump())
        return {'id':ident,**preset.model_dump()}

    def list(self):
        rows=[]
        for path in sorted(self.root.glob('*.json')):
            try:rows.append({'id':path.stem,**self.load(path.stem).model_dump()})
            except (OSError,ValueError):continue
        return rows
