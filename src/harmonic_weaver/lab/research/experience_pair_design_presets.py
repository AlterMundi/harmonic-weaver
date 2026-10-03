"""Portable R10 configuration, excludes people, sources, exposure and responses."""
from pathlib import Path
from typing import Literal
from uuid import uuid4
import re
from pydantic import Field
from ..contracts import Contract
from ..cache import atomic_json
from .experience_pair_design import Configuration


class Preset(Contract):
    schema_version:Literal[1]=1
    name:str=Field(min_length=1,max_length=80)
    config:Configuration


class PairDesignPresets:
    def __init__(self,data_dir):
        self.root=Path(data_dir)/'research/r10-pair-design-presets'
        self.root.mkdir(mode=0o700,parents=True,exist_ok=True)

    def load(self,ident):
        if not isinstance(ident,str) or not re.fullmatch('[a-f0-9]{32}',ident):raise ValueError('Invalid experience preset ID')
        path=self.root/f'{ident}.json'
        if path.is_symlink() or not path.is_file() or path.stat().st_size>65536:raise ValueError('Regular bounded experience preset required')
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
