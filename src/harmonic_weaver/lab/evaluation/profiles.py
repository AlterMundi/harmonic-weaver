"""Portable processing controls, never frozen sources or renderer identities."""
from copy import deepcopy
from typing import Literal
from uuid import uuid4
from pydantic import Field
from ..contracts import Contract, Identifier, Number
from .pcm import PCMSettings
from .runner import Request


class PortablePCM(PCMSettings):
    engine_sha256: None = Field(default=None,exclude=True)
    environment_sha256: None = Field(default=None,exclude=True)


class EvaluationProfile(Contract):
    schema_version: Literal[1] = 1
    id: Identifier = Field(default_factory=lambda:uuid4().hex)
    name: str = Field(default='Procesamiento de comparación',min_length=1,max_length=120)
    # Reuse the execution contract's actual defaults and bounds.
    control_hz: int = deepcopy(Request.model_fields['control_hz'])
    preroll_s: Number = deepcopy(Request.model_fields['preroll_s'])
    max_runs_per_invocation: int = deepcopy(Request.model_fields['max_runs_per_invocation'])
    pcm: PortablePCM = Field(default_factory=PortablePCM)
