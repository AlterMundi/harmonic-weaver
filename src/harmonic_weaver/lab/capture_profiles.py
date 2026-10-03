"""Portable capture/export preferences, without source, calibration or actions."""
from typing import Literal
from uuid import uuid4

from pydantic import Field, model_validator

from .contracts import Contract, Identifier
from .capture import CaptureSettings
from .capture_export import ExportSettings


class CaptureProfile(Contract):
    schema_version: Literal[1] = 1
    id: Identifier = Field(default_factory=lambda: uuid4().hex)
    name: str = Field(default='Captura y exportación',min_length=1,max_length=120)
    capture: CaptureSettings = Field(default_factory=CaptureSettings)
    export: ExportSettings = Field(default_factory=ExportSettings)

    @model_validator(mode='after')
    def portable(self):
        if self.export.recovered_prefix:
            raise ValueError('recovered_prefix is selected per capture, not stored in a portable profile')
        return self
