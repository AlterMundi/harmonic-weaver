"""Explicit application of a verified saved fit to declared observations."""
import json
from pydantic import Field
from ..contracts import Contract
from ..cache import sha256_file
from .spatial_observations import Stream,Clock


class Request(Contract):
    fit_id:str=Field(pattern=r'^[a-f0-9]{32}$')
    stream:Stream
    allow_extrapolation:bool=False


def apply(service,request):
    request=Request.model_validate(request)
    manifest=service.artifact(request.fit_id,'manifest.json');digest=sha256_file(manifest)
    fit=json.loads(service.artifact(request.fit_id,'result.json').read_text())
    clock=Clock.model_validate(fit['clock'])
    if request.stream.clock.source_clock!=clock.source_clock:raise ValueError('Source clock name differs from fitted clock')
    start,end=fit['source_interval_s']
    outside=[frame.index for frame in request.stream.frames if not start<=frame.source_time_s<=end]
    if outside and not request.allow_extrapolation:raise ValueError('Observation times outside fit interval; extrapolation requires explicit opt-in')
    changed=request.stream.model_copy(update={'clock':clock})
    stream=Stream.model_validate(changed.model_dump())
    if sha256_file(service.artifact(request.fit_id,'manifest.json'))!=digest:raise ValueError('Clock fit changed during application')
    result={'schema_version':1,'line':'R09','stream':stream.model_dump(),'previous_clock':request.stream.clock.model_dump(),
        'common_times_s':[clock.common_time(frame.source_time_s) for frame in stream.frames],
        'clock_fit_provenance':{'id':request.fit_id,'manifest_sha256':digest},
        'source_interval_s':[start,end],'extrapolated_frame_indices':outside,'allow_extrapolation':request.allow_extrapolation,
        'limits':fit['limits']+['Clock replaced explicitly; original frame timestamps/coordinates/states preserved',
        'Application does not authenticate source clock names or physical synchronization; imported stream remains declared']}
    Contract.finite_tree(result)
    return result
