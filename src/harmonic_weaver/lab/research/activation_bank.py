"""R06 synthetic activation controls on one declared R05 medium, not HIT proof."""
import math
import platform
from pathlib import Path
import numpy as np
import scipy
from pydantic import Field,model_validator,model_serializer
from ..contracts import Contract,Number
from ..cache import atomic_json,sha256_file
from .resonators import Settings as Medium,Resonators


class Settings(Contract):
    medium:Medium=Field(default_factory=Medium)
    medium_controls:list[Medium]|None=Field(default=None,min_length=1,max_length=4)
    interval_shuffle:bool=False
    event_count:int=Field(default=8,ge=4,le=32)
    excitation_span_s:Number=Field(default=1,ge=.05,le=5)
    tail_s:Number=Field(default=.5,ge=0,le=10)
    impulse_strength:Number=Field(default=1,gt=0,le=10)
    seed:int=Field(default=17,ge=0,le=2147483647)
    block_size:int=Field(default=256,ge=16,le=8192)
    trace_stride:int=Field(default=256,ge=1,le=8192)

    @model_serializer(mode='wrap')
    def portable(self,handler):
        value=handler(self)
        if self.medium_controls is None:value.pop('medium_controls',None)
        if not self.interval_shuffle:value.pop('interval_shuffle',None)
        return value

    @model_validator(mode='after')
    def capacity(self):
        for control in self.medium_controls or []:
            if any(getattr(control,key)!=getattr(self.medium,key) for key in ('fundamental_hz','ratios','sample_rate')):
                raise ValueError('Medium controls must preserve carriers, ratios and sample rate')
        total=math.ceil(self.excitation_span_s*self.medium.sample_rate)+math.ceil(self.tail_s*self.medium.sample_rate)
        if math.ceil(total/self.trace_stride)+self.event_count+1>14400:
            raise ValueError('Select trace_stride for at most 14400 trace observations per condition')
        return self


def schedules(settings):
    settings=Settings.model_validate(settings);n=settings.event_count
    span=math.ceil(settings.excitation_span_s*settings.medium.sample_rate)
    k=np.arange(n,dtype=float)
    positions={'phi':np.remainder(k*((math.sqrt(5)-1)/2),1),
               'sqrt2':np.remainder(k*(math.sqrt(2)-1),1),
               'random':np.r_[0.,np.random.default_rng(settings.seed).uniform(0,1,n-1)]}
    result={'rational':[(i*span)//n for i in range(n)]}
    for name,values in positions.items():
        indices=sorted(math.floor(float(t)*span) for t in values)
        if len(set(indices))!=n:raise ValueError('Quantized schedule collisions; change span/count/seed')
        result[name]=indices
    if settings.interval_shuffle:
        for index,(name,indices) in enumerate(list(result.items())):
            rng=np.random.default_rng(np.random.SeedSequence([settings.seed,606,index]))
            gaps=rng.permutation(np.diff(indices))
            result[name+'_interval_shuffle']=[0]+np.cumsum(gaps).tolist()
    return result


def _probe_one(settings):
    settings=Settings.model_validate(settings);events=schedules(settings)
    sr=settings.medium.sample_rate;span=math.ceil(settings.excitation_span_s*sr)
    total=span+math.ceil(settings.tail_s*sr);voices=len(settings.medium.ratios)
    # Declared equal L2 vector and event count across conditions, not output leveling.
    vector=np.full(voices,settings.impulse_strength/math.sqrt(voices))
    dose=float(np.dot(vector,vector))*settings.event_count
    conditions={}
    for name,indices in events.items():
        kernel=Resonators(settings.medium);squares=peak=integral=0.;trace=[];tail_squares=0.
        event_set=set(indices)
        for start in range(0,total,settings.block_size):
            end=min(total,start+settings.block_size);impulses=np.zeros((end-start,voices))
            for index in indices:
                if start<=index<end:impulses[index-start]=vector
            block=kernel.render(impulses);summed=block['sum'];norm=block['state_norm_squared']
            squares+=float(np.dot(summed,summed));peak=max(peak,float(np.abs(summed).max()))
            integral+=float(norm.sum())/sr
            tail=summed[max(0,span-start):];tail_squares+=float(np.dot(tail,tail))
            for i in range(end-start):
                index=start+i
                if index%settings.trace_stride==0 or index in event_set or index==total-1:
                    trace.append({'sample_index':index,'time_s':(index+1)/sr,'sum':float(summed[i]),
                                  'state_norm_squared':float(norm[i]),'instrument_tail':index>=span})
        conditions[name]={'event_samples':indices,'input_squared_norm':dose,
            'metrics':{'rms':math.sqrt(squares/total),'peak_abs':peak,
                'state_norm_time_integral':integral,'final_state_norm_squared':float(np.vdot(kernel.state,kernel.state).real),
                'tail_rms':math.sqrt(tail_squares/(total-span)) if total>span else None},'trace':trace}
    return {'schema_version':1,'line':'R06','settings':settings.model_dump(),
        'clock':{'sample_rate':sr,'excitation_frames':span,'total_frames':total},
        'impulse_vector':vector.tolist(),'conditions':conditions,
        'limits':['Synthetic timing patterns on identical declared complex resonator medium and zero initial state',
            'Equal event count and per-event input L2 norm; temporal distributions intentionally differ',
            'Rational condition is a uniform sample grid; phi/sqrt2 fractional rotations and seeded uniform timing are alternative constructions',
            'Digital quantization makes all event times rational sample indices; not exact irrational forcing',
            'Metric differences may reflect timing/clustering and this medium, not privileged phi or HIT confirmation',
            'State norm is internal model quantity, not measured physical energy or physiological efficacy',
            'Traces are visual decimation; metrics use all samples; no automatic output normalization',
            'No body data, sound acceptance, p-values, intention inference or physical cymatics']}


def probe(settings):
    settings=Settings.model_validate(settings)
    base=settings.model_copy(update={'medium_controls':None})
    report=_probe_one(base)
    report['settings']=settings.model_dump()
    if settings.interval_shuffle:
        report['limits']+=['Optional interval shuffles preserve event count, dose, first/last event and exact digital inter-event interval multiset',
                           'Shuffles alter interval order, not interval histogram; do not preserve spectrum or higher-order temporal structure',
                           'Seeded permutations can be identical to the original, especially the uniform rational grid; no conditioning to force a difference']
    if settings.medium_controls is not None:
        controls=[]
        for index,medium in enumerate(settings.medium_controls):
            condition_report=_probe_one(base.model_copy(update={'medium':medium}))
            differences={}
            for name,condition in condition_report['conditions'].items():
                reference=report['conditions'][name]['metrics']
                differences[name]={key:(value-reference[key] if value is not None else None) for key,value in condition['metrics'].items()}
            controls.append({'index':index,'medium':medium.model_dump(),
                             'conditions':condition_report['conditions'],'metric_difference_vs_base':differences})
        report['medium_controls']=controls
        report['limits']+=['Optional medium controls preserve carrier frequencies/clock and identical event samples/dose',
                           'Medium differences change damping/coupling/graph only; metric deltas are control minus base, not efficacy scores']
    return report


def run(settings,folder):
    report=probe(settings);folder=Path(folder);folder.mkdir(parents=True,mode=0o700,exist_ok=False)
    atomic_json(folder/'request.json',report['settings'])
    atomic_json(folder/'result.json',report)
    atomic_json(folder/'manifest.json',{'schema_version':1,'line':'R06','status':'complete',
        'input_hashes':{'request.json':sha256_file(folder/'request.json')},
        'output_sha256':sha256_file(folder/'result.json'),
        'code_hashes':{name:sha256_file(Path(__file__).with_name(name)) for name in ('activation_bank.py','resonators.py')},
        'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},'limits':report['limits']})
    return report


if __name__=='__main__':
    import argparse,json
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    run(json.loads(args.request.read_text()),args.output)
