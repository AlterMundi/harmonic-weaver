"""Seeded sound-only transient controls; no bodily labels or measurements."""
import numpy as np
from pydantic import Field,model_validator
from ..contracts import Contract,Number
from .membrane import Settings,Membrane,FieldWindow


class Request(Contract):
    membrane:Settings=Field(default_factory=lambda:Settings(sample_rate=8000))
    duration_samples:int=Field(default=8000,ge=16,le=96000)
    forcing_samples:int=Field(default=4000,ge=1,le=96000)
    amplitude:Number=Field(default=1,ge=0,le=10)
    frequencies_hz:list[Number]=Field(default_factory=lambda:[40.4*i for i in range(1,7)],min_length=1,max_length=32)
    weights:list[Number]=Field(default_factory=lambda:[1.]*6,min_length=1,max_length=32)
    phases_rad:list[Number]=Field(default_factory=lambda:[0.]*6,min_length=1,max_length=32)
    seed:int=Field(default=17,ge=0,le=2147483647)
    x:list[Number]=Field(default_factory=lambda:[0.,.25,.5,.75,1.],min_length=1,max_length=64)
    y:list[Number]=Field(default_factory=lambda:[.5]*5,min_length=1,max_length=64)
    block_size:int=Field(default=1024,ge=16,le=8192)

    @model_validator(mode='after')
    def valid(self):
        if self.forcing_samples>self.duration_samples:raise ValueError('Forcing exceeds observation duration')
        if len(self.weights)!=len(self.frequencies_hz) or len(self.phases_rad)!=len(self.weights):raise ValueError('One weight/phase per component required')
        if any(f<=0 or f>=self.membrane.sample_rate/2 for f in self.frequencies_hz):raise ValueError('Positive component frequencies below Nyquist required')
        if any(abs(v)>100 for v in self.weights+self.phases_rad):raise ValueError('Weights/phases bounded within ±100')
        if len(self.x)!=len(self.y) or any(v<0 or v>1 for v in self.x+self.y):raise ValueError('Paired normalized points required')
        if self.duration_samples*self.membrane.modes_x*self.membrane.modes_y>8_000_000:raise ValueError('Control bank exceeds modal element budget')
        return self


def signals(request):
    request=Request.model_validate(request)
    n=request.duration_samples;active=request.forcing_samples
    values={name:np.zeros(n) for name in ('impulse','pulse','multisine','seeded_noise')}
    values['impulse'][0]=request.amplitude
    values['pulse'][:active]=request.amplitude
    t=np.arange(active)/request.membrane.sample_rate
    for f,w,p in zip(request.frequencies_hz,request.weights,request.phases_rad):
        values['multisine'][:active]+=request.amplitude*w*np.sin(2*np.pi*f*t+p)
    values['seeded_noise'][:active]=request.amplitude*np.random.default_rng(request.seed).standard_normal(active)
    return values


def compare(request):
    request=Request.model_validate(request);rows={}
    for name,pcm in signals(request).items():
        model=Membrane(request.membrane);window=FieldWindow(model)
        final_energy=0.
        for start in range(0,len(pcm),request.block_size):
            result=model.render(pcm[start:start+request.block_size])
            window.append(result['modal_displacement'],start)
            final_energy=float(result['modal_energy_proxy'][-1])
        field=window.report(request.x,request.y)
        field['rms']=field['rms'].tolist()
        rows[name]={'input_sum_squares':float(np.dot(pcm,pcm)),
                    'input_peak_abs':float(np.max(np.abs(pcm))),
                    'field':field,'final_modal_energy_proxy':final_energy}
    return {'schema_version':1,'line':'R07','kind':'transient_control_bank',
            'request':request.model_dump(),'conditions':rows,'limits':[
                'Same medium and zero initial state; all declared multisine components summed',
                'Inputs have different measured digital doses; no equal-energy normalization',
                'Impulse is one held sample, not an ideal Dirac force',
                'Noise is seeded Gaussian, not physically bandlimited pressure',
                'Finite modal/point/time support, no sand/water/physical-energy interpretation']}
