"""R05 paired raw-PCM metrics; no inference about bodily efficacy or agency."""
import math
from itertools import zip_longest
import numpy as np
from .resonator_render import Render as ResonatorRender
from .parameter_render import Render as ParameterRender
from .coincidence import content_hash


class Metrics:
    def __init__(self):self.frames=0;self.squares=0.;self.peak=0.;self.over=0
    def push(self,values):
        if not len(values):return
        if not np.isfinite(values).all():raise ValueError('Nonfinite comparison PCM')
        self.frames+=len(values);self.squares+=float(np.dot(values,values))
        self.peak=max(self.peak,float(np.abs(values).max()))
        self.over+=int(np.count_nonzero(np.abs(values)>1))
    def report(self):
        return {'frames':self.frames,'rms':math.sqrt(self.squares/self.frames) if self.frames else None,
                'peak_abs':self.peak if self.frames else None,'samples_over_full_scale':self.over}


def compare(document,resonators,excitation,mapping,render=None):
    excited=ResonatorRender(document,resonators,excitation,render)
    # Frequencies/sr/ratios shared; this arm deliberately has no resonator graph.
    carriers={**excited.resonators.model_dump(),'coupling_per_s':0.,'topology':'isolated','adjacency':None}
    mapped=ParameterRender(document,carriers,mapping,excited.settings.model_dump())
    if (excited.segment_frames,excited.total_frames)!=(mapped.segment_frames,mapped.total_frames):
        raise ValueError('Comparison arms must share exact sample clock')
    sr=excited.resonators.sample_rate;origin=excited.excitation['selection']['start_s']
    gap=min(excited.excitation['settings']['max_gap_s'],mapped.mapping.max_hold_s)
    rows=document['rows'];support=[]
    def observed(row):
        return row.get('valid',True) is True and type(row.get('value')) in (int,float) and math.isfinite(row['value'])
    for a,b in zip(rows,rows[1:]):
        if observed(a) and observed(b) and b['time_s']-a['time_s']<=gap:
            start=math.ceil((a['time_s']-origin)*sr);end=math.ceil((b['time_s']-origin)*sr)
            if end>start:
                if support and start==support[-1][1]:support[-1][1]=end
                else:support.append([start,end])
    stats={name:{region:Metrics() for region in ('segment','common_observed','unsupported_segment','tail')}
           for name in ('excited_resonators','amplitude_mapping')}
    difference=Metrics();support_index=0
    for left,right in zip_longest(excited.blocks(),mapped.blocks()):
        if left is None or right is None or left['start_sample']!=right['start_sample'] or len(left['sum'])!=len(right['sum']):
            raise ValueError('Comparison block clocks differ')
        start=left['start_sample'];end=start+len(left['sum']);indices=np.arange(start,end)
        segment=indices<excited.segment_frames;common=np.zeros(len(indices),dtype=bool)
        while support_index<len(support) and support[support_index][1]<=start:support_index+=1
        j=support_index
        while j<len(support) and support[j][0]<end:
            a,b=support[j];common |= (indices>=a)&(indices<b);j+=1
        for name,block in (('excited_resonators',left),('amplitude_mapping',right)):
            values=block['sum']
            for region,mask in (('segment',segment),('common_observed',common),
                                ('unsupported_segment',segment & ~common),('tail',~segment)):
                stats[name][region].push(values[mask])
        difference.push((left['sum']-right['sum'])[common])
    reports={name:{region:metric.report() for region,metric in regions.items()} for name,regions in stats.items()}
    a=reports['excited_resonators']['common_observed']['rms'];b=reports['amplitude_mapping']['common_observed']['rms']
    return {'schema_version':1,'input_sha256':content_hash(document),'provenance':document.get('provenance'),
        'input_unit':document['unit'],'resonator_preparation':excited.manifest,'mapping_preparation':mapped.manifest,
        'clock':{'sample_rate':sr,'segment_frames':excited.segment_frames,'total_frames':excited.total_frames,
                 'source_start_s':origin,'common_observed_sample_intervals':support,'common_max_gap_s':gap},
        'metrics':reports,'paired_difference':difference.report(),
        'suggested_mapping_gain_for_equal_common_rms':a/b if a and b else None,
        'limits':['Both arms consume identical frozen observations; neither is the accepted Shaper',
            'Common support uses adjacent valid observations within both declared gap limits, no extrapolation',
            'Output clocks use upward quantization and identical sample counts; envelope/detector latencies remain different',
            'Raw PCM comparison; equal-RMS gain is diagnostic only and never applied automatically',
            'Unsupported segment/tail may contain instrument activity; not measured body organization',
            'PCM difference is not quality, efficacy, agency, musical interest or statistical evidence',
            'Carrier phase, internal resonator phase and observed body timing are distinct',
            'Metrics use block reductions; tiny floating-point differences across block sizes are possible']}
