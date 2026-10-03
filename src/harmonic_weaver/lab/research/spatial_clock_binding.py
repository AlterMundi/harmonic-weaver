"""Frozen inputs/provenance for reproducible clock application."""
from pydantic import Field
from ..contracts import Contract
from .spatial_observations import Stream,Clock
from .spatial_clock_fit import Request as FitRequest,fit


class Source(Contract):
    id:str=Field(pattern=r'^[a-f0-9]{32}$')
    manifest_sha256:str=Field(pattern=r'^[a-f0-9]{64}$')


class Application(Contract):
    conversion:Source
    clock_fit:Source
    original_stream:Stream
    fit_input:FitRequest
    allow_extrapolation:bool=False


def transformed(application):
    application=Application.model_validate(application)
    result=fit(application.fit_input);clock=Clock.model_validate(result['clock'])
    original=application.original_stream
    if original.clock.source_clock!=clock.source_clock:raise ValueError('Source clock name differs from fitted clock')
    start,end=result['source_interval_s']
    if not application.allow_extrapolation and any(not start<=f.source_time_s<=end for f in original.frames):raise ValueError('Observation times outside fit interval')
    return Stream.model_validate({**original.model_dump(),'clock':clock.model_dump()})
