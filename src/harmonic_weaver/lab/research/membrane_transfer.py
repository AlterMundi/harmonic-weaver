"""Explicit finite modal-resolution comparisons, not a convergence proof."""
import numpy as np
from pydantic import Field, model_validator
from ..contracts import Contract, Number
from .membrane import Settings, Membrane


class Resolution(Contract):
    modes_x: int = Field(ge=1, le=16)
    modes_y: int = Field(ge=1, le=16)


class Request(Contract):
    membrane: Settings = Field(default_factory=Settings)
    resolutions: list[Resolution] = Field(default_factory=lambda:[Resolution(modes_x=2,modes_y=2),Resolution(modes_x=4,modes_y=4),Resolution(modes_x=8,modes_y=8)],min_length=2,max_length=6)
    frequencies_hz: list[Number] = Field(default_factory=lambda:[20.,40.4,80.8,121.2,161.6,202.,242.4],min_length=1,max_length=256)
    x: list[Number] = Field(default_factory=lambda:[.25,.5,.75],min_length=1,max_length=64)
    y: list[Number] = Field(default_factory=lambda:[.25,.5,.75],min_length=1,max_length=64)

    @model_validator(mode='after')
    def valid(self):
        if len(self.x)!=len(self.y) or any(v<0 or v>1 for v in self.x+self.y):
            raise ValueError('Paired normalized observation points required')
        if self.membrane.damping_per_s<=0:
            raise ValueError('Positive damping required for attracting steady response')
        if any(v<0 or v>=self.membrane.sample_rate/2 for v in self.frequencies_hz):
            raise ValueError('Frequencies must be nonnegative below Nyquist')
        pairs=[(r.modes_x,r.modes_y) for r in self.resolutions]
        if len(set(pairs))!=len(pairs):raise ValueError('Distinct resolutions required')
        if any(b[0]<a[0] or b[1]<a[1] for a,b in zip(pairs,pairs[1:])):
            raise ValueError('Nested nondecreasing resolutions required')
        for r in self.resolutions:
            Settings.model_validate({**self.membrane.model_dump(),**r.model_dump()})
        return self


def compare(request):
    request=Request.model_validate(request)
    rows=[];previous=None
    for resolution in request.resolutions:
        model=Membrane({**request.membrane.model_dump(),**resolution.model_dump()})
        value=model.transfer_response(request.frequencies_hz,request.x,request.y)
        delta=None if previous is None else value-previous
        phase=None if previous is None else np.angle(value*np.conjugate(previous))
        # Phase is undefined at exact zero response; never invent its angle.
        phase_rows=None if phase is None else [[None if value[i,j]==0 or previous[i,j]==0 else float(phase[i,j])
            for j in range(value.shape[1])] for i in range(value.shape[0])]
        rows.append({'resolution':resolution.model_dump(),'real':value.real.tolist(),'imag':value.imag.tolist(),
                     'magnitude':np.abs(value).tolist(),
                     'difference_magnitude_vs_previous':None if delta is None else np.abs(delta).tolist(),
                     'phase_difference_rad_vs_previous':phase_rows})
        previous=value
    return {'schema_version':1,'line':'R07','kind':'modal_transfer_comparison',
            'request':request.model_dump(),'conditions':rows,
            'limits':['Same geometry, damping, forcing location, sample rate and observation points',
                      'Exact discrete held-input stationary unit forcing; not transient PCM',
                      'Nested finite resolutions do not prove convergence to continuum',
                      'Raw complex differences; no normalization or physical calibration',
                      'Phase at exact zero response is undefined; near-zero phase may be unstable']}
