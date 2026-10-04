"""Read-only R06 integrity and declared clock/support contracts; not signed custody."""
import json
import math
from pathlib import Path
from ..cache import sha256_file
from .activation_bank import Settings,schedules
from .activation_spectrum import validate_probe


def verify(folder):
    folder=Path(folder)
    if folder.is_symlink() or not folder.is_dir():raise ValueError('Regular R06 directory required')
    names=('manifest.json','request.json','result.json')
    for name in names:
        if (folder/name).is_symlink() or not (folder/name).is_file():raise ValueError('Regular R06 artifacts required')
    manifest_hash=sha256_file(folder/'manifest.json');manifest=json.loads((folder/'manifest.json').read_text())
    if (manifest.get('schema_version'),manifest.get('line'),manifest.get('status'))!=(1,'R06','complete'):
        raise ValueError('Completed R06 manifest required')
    if set(manifest.get('input_hashes',{}))!={'request.json'}:raise ValueError('Exact R06 input inventory required')
    if 'output' in manifest:
        if set(manifest['output'])!={'file','sha256'} or manifest['output']['file']!='result.json':raise ValueError('Exact R06 output required')
        expected=manifest['output']['sha256']
    else:expected=manifest['output_sha256']
    hashes={**manifest['input_hashes'],'result.json':expected,'manifest.json':manifest_hash}
    for name,digest in hashes.items():
        if sha256_file(folder/name)!=digest:raise ValueError('R06 artifact hash mismatch')
    settings=Settings.model_validate_json((folder/'request.json').read_text())
    report=json.loads((folder/'result.json').read_text())
    validate_report(report,settings)
    for name,digest in hashes.items():
        if (folder/name).is_symlink() or sha256_file(folder/name)!=digest:raise ValueError('R06 artifact changed during verification')
    return manifest


def validate_report(report,settings, *, excitation_phases_rad=None):
    if report.get('schema_version')!=1 or report.get('line')!='R06' or report['settings']!=settings.model_dump():
        raise ValueError('R06 report differs from frozen configuration')
    if excitation_phases_rad is None:
        if 'excitation_phases_rad' in report:raise ValueError('Unexpected excitation phases')
    elif report.get('excitation_phases_rad')!=excitation_phases_rad:
        raise ValueError('Excitation phases differ from frozen control')
    sr=settings.medium.sample_rate;span=math.ceil(settings.excitation_span_s*sr);total=span+math.ceil(settings.tail_s*sr)
    if report['clock']!={'sample_rate':sr,'excitation_frames':span,'total_frames':total}:raise ValueError('R06 clock mismatch')
    events=schedules(settings)
    if set(report['conditions'])!=set(events):raise ValueError('R06 conditions mismatch')
    vector=[settings.impulse_strength/math.sqrt(len(settings.medium.ratios))]*len(settings.medium.ratios)
    if report['impulse_vector']!=vector:raise ValueError('R06 impulse vector mismatch')
    for name,indices in events.items():
        condition=report['conditions'][name]
        if any(type(v) is not int for v in condition['event_samples']) or type(condition['input_squared_norm']) not in (int,float):
            raise ValueError('Invalid R06 dose/calendar types')
        if condition['event_samples']!=indices or not math.isclose(condition['input_squared_norm'],sum(v*v for v in vector)*settings.event_count,rel_tol=1e-14):
            raise ValueError('R06 input dose/calendar mismatch')
        if settings.spectral_probe is not None:
            validate_probe(condition.get('spectral_probe',{}),settings.spectral_probe,sr,span,total,indices)
        elif 'spectral_probe' in condition:raise ValueError('Unexpected spectral probe')
        metrics=condition['metrics']
        if set(metrics)!={'rms','peak_abs','state_norm_time_integral','final_state_norm_squared','tail_rms'}:raise ValueError('R06 metric inventory mismatch')
        for key,value in metrics.items():
            if key=='tail_rms' and total==span:
                if value is not None:raise ValueError('Empty tail requires null metric')
            elif type(value) not in (int,float) or not math.isfinite(value) or value<0:raise ValueError('Invalid R06 metric')
        expected_indices=sorted(set(range(0,total,settings.trace_stride))|set(indices)|{total-1})
        trace=condition['trace']
        if [r['sample_index'] for r in trace]!=expected_indices:raise ValueError('R06 trace support mismatch')
        for row in trace:
            if type(row['sample_index']) is not int or type(row['time_s']) not in (int,float) or row['time_s']!=(row['sample_index']+1)/sr or type(row['instrument_tail']) is not bool or row['instrument_tail']!=(row['sample_index']>=span):
                raise ValueError('R06 trace clock mismatch')
            if not all(type(row[k]) in (int,float) and math.isfinite(row[k]) for k in ('sum','state_norm_squared')) or row['state_norm_squared']<0:
                raise ValueError('Invalid R06 trace values')
    controls=settings.medium_controls
    if settings.circular_shift_controls is not None:
        from .activation_shifts import validate as validate_shifts
        validate_shifts(report.get('circular_shift_controls',[]),settings,events,report['conditions'])
    elif 'circular_shift_controls' in report:raise ValueError('Unexpected circular shifts')
    if controls is None:
        if 'medium_controls' in report:raise ValueError('Unexpected medium controls')
    else:
        outputs=report.get('medium_controls',[])
        if len(outputs)!=len(controls):raise ValueError('Medium control inventory mismatch')
        for index,(medium,output) in enumerate(zip(controls,outputs)):
            if type(output['index']) is not int or output['index']!=index or output['medium']!=medium.model_dump():
                raise ValueError('Medium control differs from frozen configuration')
            child=settings.model_copy(update={'medium':medium,'medium_controls':None,'replicate_seeds':None,'phase_controls':None})
            validate_report({**({'excitation_phases_rad':excitation_phases_rad} if excitation_phases_rad is not None else {}),
                'schema_version':1,'line':'R06','settings':child.model_dump(),
                'clock':report['clock'],'impulse_vector':report['impulse_vector'],'conditions':output['conditions'],
                **({'circular_shift_controls':output.get('circular_shift_controls',[])} if settings.circular_shift_controls is not None else {})},child,excitation_phases_rad=excitation_phases_rad)
            expected={name:{key:(value-report['conditions'][name]['metrics'][key] if value is not None else None)
                for key,value in condition['metrics'].items()} for name,condition in output['conditions'].items()}
            if output['metric_difference_vs_base']!=expected:raise ValueError('Medium control metric differences mismatch')
    if settings.phase_controls is None:
        if 'phase_controls' in report:raise ValueError('Unexpected phase controls')
    else:
        outputs=report.get('phase_controls',[])
        if len(outputs)!=len(settings.phase_controls):raise ValueError('Phase control inventory mismatch')
        for index,(phases,output) in enumerate(zip(settings.phase_controls,outputs)):
            if type(output['index']) is not int or output['index']!=index or output['phases_rad']!=phases:
                raise ValueError('Phase control differs from frozen configuration')
            child=settings.model_copy(update={'phase_controls':None,'replicate_seeds':None})
            validate_report(output['report'],child,excitation_phases_rad=phases)
            expected={name:{key:(value-report['conditions'][name]['metrics'][key] if value is not None else None)
                for key,value in condition['metrics'].items()} for name,condition in output['report']['conditions'].items()}
            if output['metric_difference_vs_base']!=expected:raise ValueError('Phase control metric differences mismatch')
    seeds=settings.replicate_seeds
    if seeds is None:
        if 'replicates' in report or 'replicate_summary' in report or 'phase_replicate_summary' in report:raise ValueError('Unexpected replicate bank')
    else:
        outputs=report.get('replicates',[])
        if [item['seed'] for item in outputs]!=seeds or any(type(item['seed']) is not int for item in outputs):
            raise ValueError('Replicate seed inventory differs from frozen bank')
        for item in outputs:
            validate_report(item['report'],settings.model_copy(update={'seed':item['seed'],'replicate_seeds':None}))
        from .activation_bank import replicate_summary
        if report.get('replicate_summary')!=replicate_summary(report):raise ValueError('Replicate descriptive summary mismatch')
        if settings.phase_controls is not None:
            expected={str(index):replicate_summary({**report['phase_controls'][index]['report'],
                'replicates':[{'report':r['report']['phase_controls'][index]['report']} for r in report['replicates']]})
                for index in range(len(settings.phase_controls))}
            if report.get('phase_replicate_summary')!=expected:raise ValueError('Phase replicate summary mismatch')
        elif 'phase_replicate_summary' in report:raise ValueError('Unexpected phase replicate summary')
