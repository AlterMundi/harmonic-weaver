"""Experimental passive complex resonators; never alters accepted live synthesis."""
from typing import Literal
import numpy as np
from scipy.linalg import expm
from pydantic import Field,model_validator
from ..contracts import Contract,Number


class Settings(Contract):
    fundamental_hz:Number=Field(default=40.4,gt=0,le=400)
    ratios:list[Number]=Field(default_factory=lambda:[1.,2.,3.,4.,5.,6.],min_length=6,max_length=32)
    sample_rate:int=Field(default=48000,ge=8000,le=96000)
    damping_per_s:list[Number]=Field(default_factory=lambda:[2.]*6,min_length=6,max_length=32)
    coupling_per_s:Number=Field(default=0,ge=0,le=100)
    topology:Literal['isolated','chain','ring','complete','custom']='isolated'
    adjacency:list[list[Number]]|None=None

    @model_validator(mode='after')
    def valid(self):
        n=len(self.ratios)
        if len(self.damping_per_s)!=n or any(v<0 or v>100 for v in self.damping_per_s):raise ValueError('Specify one damping in 0–100 per voice')
        if any(v<=0 or self.fundamental_hz*v>=self.sample_rate/2 for v in self.ratios):raise ValueError('Every frequency must be positive and below Nyquist')
        if self.topology=='custom':
            if self.adjacency is None:raise ValueError('Custom graph requires adjacency')
            a=np.asarray(self.adjacency,dtype=float)
            if a.shape!=(n,n) or not np.isfinite(a).all() or (a<0).any() or (a>1).any() or not np.array_equal(a,a.T) or np.any(np.diag(a)!=0):
                raise ValueError('Graph must be symmetric, nonnegative ≤1 and zero diagonal')
        elif self.adjacency is not None:raise ValueError('Adjacency only applies to custom graph')
        return self


def graph(settings):
    n=len(settings.ratios);a=np.zeros((n,n))
    if settings.topology=='custom':return np.array(settings.adjacency,dtype=float)
    if settings.topology=='complete':return np.ones((n,n))-np.eye(n)
    if settings.topology in ('chain','ring'):
        for i in range(n-1):a[i,i+1]=a[i+1,i]=1
        if settings.topology=='ring':a[0,-1]=a[-1,0]=1
    return a


class Resonators:
    """dz/dt=(iΩ−Γ−gL)z; declared sample impulses precede each exact step.

    Symmetric nonnegative graph L and damping ensure passive free evolution.
    ||z||² is an internal norm, not measured physical energy. Coupling can
    change effective modes; uncoupled carrier ratios remain an explicit option.
    """
    def __init__(self,settings):
        self.settings=Settings.model_validate(settings)
        a=graph(self.settings);laplacian=np.diag(a.sum(axis=1))-a
        generator=np.diag(2j*np.pi*self.settings.fundamental_hz*np.array(self.settings.ratios)-np.array(self.settings.damping_per_s))-self.settings.coupling_per_s*laplacian
        self.step=expm(generator/self.settings.sample_rate)
        self.state=np.zeros(len(self.settings.ratios),dtype=complex);self.sample_index=0

    def reset(self):
        self.state.fill(0);self.sample_index=0

    def render(self,impulses):
        impulses=np.asarray(impulses,dtype=float)
        n=len(self.state)
        if impulses.ndim!=2 or impulses.shape[1]!=n or not np.isfinite(impulses).all():raise ValueError('Finite frames × voice impulses required')
        if len(impulses)>self.settings.sample_rate*120:raise ValueError('Render at most 120 seconds per call')
        output=np.empty((len(impulses),n),dtype=float)
        quadrature=np.empty((len(impulses),n),dtype=float)
        norms=np.empty(len(impulses),dtype=float)
        for i,excitation in enumerate(impulses):
            self.state=self.step@(self.state+excitation)
            output[i]=self.state.imag
            quadrature[i]=self.state.real
            norms[i]=float(np.vdot(self.state,self.state).real)
            self.sample_index+=1
        return {'voices':output,'quadrature':quadrature,'sum':output.sum(axis=1),'state_norm_squared':norms,'sample_index':self.sample_index}
