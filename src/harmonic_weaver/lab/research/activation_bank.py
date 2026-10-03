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
from .activation_spectrum import Settings as SpectralProbe, Accumulator as SpectralAccumulator, support as spectral_support


class Settings(Contract):
    medium:Medium=Field(default_factory=Medium)
    medium_controls:list[Medium]|None=Field(default=None,min_length=1,max_length=4)
    replicate_seeds:list[int]|None=Field(default=None,min_length=1,max_length=8)
    phase_controls:list[list[Number]]|None=Field(default=None,min_length=1,max_length=4)
    spectral_probe:SpectralProbe|None=None
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
        if self.replicate_seeds is None:value.pop('replicate_seeds',None)
        if self.phase_controls is None:value.pop('phase_controls',None)
        if self.spectral_probe is None:value.pop('spectral_probe',None)
        return value

    @model_validator(mode='after')
    def capacity(self):
        if self.replicate_seeds is not None:
            seeds=self.replicate_seeds
            if len(set(seeds))!=len(seeds) or self.seed in seeds or any(s<0 or s>2147483647 for s in seeds):
                raise ValueError('Additional seeds must be unique, in range and different from primary seed')
        for phases in self.phase_controls or []:
            if len(phases)!=len(self.medium.ratios) or any(abs(p)>1000 for p in phases):
                raise ValueError('Specify one excitation phase in −1000..1000 rad per voice')
        for control in self.medium_controls or []:
            if any(getattr(control,key)!=getattr(self.medium,key) for key in ('fundamental_hz','ratios','sample_rate')):
                raise ValueError('Medium controls must preserve carriers, ratios and sample rate')
        total=math.ceil(self.excitation_span_s*self.medium.sample_rate)+math.ceil(self.tail_s*self.medium.sample_rate)
        if self.spectral_probe is not None:
            span=math.ceil(self.excitation_span_s*self.medium.sample_rate)
            first,last=spectral_support(self.spectral_probe,self.medium.sample_rate,span,total)
            work=(last-first)*len(self.spectral_probe.frequencies_hz)*(8 if self.interval_shuffle else 4)*(1+len(self.medium_controls or []))*(1+len(self.replicate_seeds or []))*(1+len(self.phase_controls or []))
            if work>64000000:raise ValueError('Reduce spectral window/frequencies/bank to at most 64000000 frequency-sample products')
        if math.ceil(total/self.trace_stride)+self.event_count+1>14400:
            raise ValueError('Select trace_stride for at most 14400 trace observations per condition')
        if self.replicate_seeds is not None or self.phase_controls is not None:
            points=(math.ceil(total/self.trace_stride)+self.event_count+1)*(8 if self.interval_shuffle else 4)*(1+len(self.medium_controls or []))*(1+len(self.replicate_seeds or []))*(1+len(self.phase_controls or []))
            if points>144000:raise ValueError('Increase trace_stride for aggregate bank limit of 144000 trace points')
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
        if len(set(indices))!=n:
            duplicates=sorted({i for i in indices if indices.count(i)>1})
            raise ValueError(f'Quantized {name} schedule collisions for seed {settings.seed} at samples {duplicates}; change span/count/seed')
        result[name]=indices
    if settings.interval_shuffle:
        for index,(name,indices) in enumerate(list(result.items())):
            rng=np.random.default_rng(np.random.SeedSequence([settings.seed,606,index]))
            gaps=rng.permutation(np.diff(indices))
            result[name+'_interval_shuffle']=[0]+np.cumsum(gaps).tolist()
    for seed in settings.replicate_seeds or []:
        schedules(settings.model_copy(update={'seed':seed,'replicate_seeds':None}))
    return result


def _probe_one(settings, excitation_phases_rad=None):
    settings=Settings.model_validate(settings);events=schedules(settings)
    sr=settings.medium.sample_rate;span=math.ceil(settings.excitation_span_s*sr)
    total=span+math.ceil(settings.tail_s*sr);voices=len(settings.medium.ratios)
    # Declared equal L2 vector and event count across conditions, not output leveling.
    vector=np.full(voices,settings.impulse_strength/math.sqrt(voices))
    dose=float(np.dot(vector,vector))*settings.event_count
    conditions={}
    for name,indices in events.items():
        kernel=Resonators(settings.medium);squares=peak=integral=0.;trace=[];tail_squares=0.
        spectral=SpectralAccumulator(settings.spectral_probe,sr,span,total) if settings.spectral_probe is not None else None
        event_set=set(indices)
        for start in range(0,total,settings.block_size):
            end=min(total,start+settings.block_size);impulses=np.zeros((end-start,voices))
            for index in indices:
                if start<=index<end:impulses[index-start]=vector
            block=kernel.render(impulses,excitation_phases_rad=excitation_phases_rad);summed=block['sum'];norm=block['state_norm_squared']
            if spectral is not None:spectral.add(start,summed)
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
        if spectral is not None:conditions[name]['spectral_probe']=spectral.finish(indices)
    return {**({'excitation_phases_rad':list(excitation_phases_rad)} if excitation_phases_rad is not None else {}),
        'schema_version':1,'line':'R06','settings':settings.model_dump(),
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


def _probe_seed(settings, excitation_phases_rad=None):
    settings=Settings.model_validate(settings)
    base=settings.model_copy(update={'medium_controls':None,'phase_controls':None})
    report=_probe_one(base, excitation_phases_rad)
    report['settings']=settings.model_dump()
    if settings.interval_shuffle:
        report['limits']+=['Optional interval shuffles preserve event count, dose, first/last event and exact digital inter-event interval multiset',
                           'Shuffles alter interval order, not interval histogram; do not preserve spectrum or higher-order temporal structure',
                           'Seeded permutations can be identical to the original, especially the uniform rational grid; no conditioning to force a difference']
    if settings.medium_controls is not None:
        controls=[]
        for index,medium in enumerate(settings.medium_controls):
            condition_report=_probe_one(base.model_copy(update={'medium':medium}), excitation_phases_rad)
            differences={}
            for name,condition in condition_report['conditions'].items():
                reference=report['conditions'][name]['metrics']
                differences[name]={key:(value-reference[key] if value is not None else None) for key,value in condition['metrics'].items()}
            controls.append({'index':index,'medium':medium.model_dump(),
                             'conditions':condition_report['conditions'],'metric_difference_vs_base':differences})
        report['medium_controls']=controls
        report['limits']+=['Optional medium controls preserve carrier frequencies/clock and identical event samples/dose',
                           'Medium differences change damping/coupling/graph only; metric deltas are control minus base, not efficacy scores']
    if settings.phase_controls is not None:
        controls=[]
        for index,phases in enumerate(settings.phase_controls):
            child=_probe_seed(settings.model_copy(update={'phase_controls':None}),phases)
            differences={name:{key:(value-report['conditions'][name]['metrics'][key] if value is not None else None)
                for key,value in condition['metrics'].items()} for name,condition in child['conditions'].items()}
            controls.append({'index':index,'phases_rad':phases,'report':child,'metric_difference_vs_base':differences})
        report['phase_controls']=controls
        report['limits']+=['Explicit fixed per-voice phases rotate each complex excitation, preserving magnitudes, events and input L2 norm',
            'Zero initial state and carriers unchanged; coupled medium response can depend on relative excitation phase',
            'This is an excitation-phase control, not estimated body phase, phase randomization of recorded EEG or a HIT test']
    return report


def replicate_summary(report):
    reports=[report]+[item['report'] for item in report.get('replicates',[])]
    result={}
    for index in range(-1,len(report.get('medium_controls',[]))):
        label='base' if index<0 else f'control_{index}'
        conditions=[r['conditions'] if index<0 else r['medium_controls'][index]['conditions'] for r in reports]
        result[label]={}
        for name in conditions[0]:
            result[label][name]={}
            for metric in conditions[0][name]['metrics']:
                values=[c[name]['metrics'][metric] for c in conditions if c[name]['metrics'][metric] is not None]
                mean=values[0]+math.fsum(v-values[0] for v in values)/len(values) if values else None
                result[label][name][metric]={'count':len(values),'mean':mean,'min':min(values) if values else None,
                    'max':max(values) if values else None,
                    'std_population':math.sqrt(math.fsum((v-mean)**2 for v in values)/len(values)) if values else None}
    return result


def probe(settings):
    settings=Settings.model_validate(settings);schedules(settings);primary=settings.model_copy(update={'replicate_seeds':None})
    report=_probe_seed(primary);report['settings']=settings.model_dump()
    if settings.replicate_seeds is not None:
        report['replicates']=[{'seed':seed,'report':_probe_seed(primary.model_copy(update={'seed':seed}))} for seed in settings.replicate_seeds]
        report['replicate_summary']=replicate_summary(report)
        if settings.phase_controls is not None:
            report['phase_replicate_summary']={str(index):replicate_summary({
                **report['phase_controls'][index]['report'],
                'replicates':[{'report':r['report']['phase_controls'][index]['report']} for r in report['replicates']]})
                for index in range(len(settings.phase_controls))}

        report['limits']+=['Explicit additional seeds are frozen, with primary and every replicate result retained',
                           'Descriptive population mean/range/std only; deterministic calendars may repeat across seeds',
                           'Seeds are not independent human trials or a null distribution; no p-value, ranking or HIT inference']
    return report


def run(settings,folder):
    report=probe(settings);folder=Path(folder);folder.mkdir(parents=True,mode=0o700,exist_ok=False)
    atomic_json(folder/'request.json',report['settings'])
    atomic_json(folder/'result.json',report)
    atomic_json(folder/'manifest.json',{'schema_version':1,'line':'R06','status':'complete',
        'input_hashes':{'request.json':sha256_file(folder/'request.json')},
        'output_sha256':sha256_file(folder/'result.json'),
        'code_hashes':{name:sha256_file(Path(__file__).with_name(name)) for name in ('activation_bank.py','resonators.py','activation_spectrum.py')},
        'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},'limits':report['limits']})
    return report


if __name__=='__main__':
    import argparse,json
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    run(json.loads(args.request.read_text()),args.output)
