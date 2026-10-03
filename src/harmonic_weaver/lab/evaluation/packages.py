"""Selected local review packages; never copy video or publish externally."""
import fcntl
import hashlib
import json
from pathlib import Path
import zipfile

from pydantic import Field, model_validator
from ..cache import atomic_json, sha256_file
from ..contracts import Contract, Preset
from ..routing import PreparedRoutes, signal_catalog
from ..store import validate_macros
from ..research.coincidence_service import CoincidenceService
from .runner import Request, canonical, digest


class Selection(Contract):
    run_indices: list[int] = Field(min_length=1, max_length=1024)
    include_requests: bool = False
    include_traces: bool = False
    include_pcm: bool = False
    max_mb: int = Field(default=64, ge=1, le=4096)

    @model_validator(mode='after')
    def unique(self):
        if len(set(self.run_indices)) != len(self.run_indices) or min(self.run_indices) < 0:
            raise ValueError('Choose unique nonnegative run indices')
        return self


class CreateRequest(Contract):
    selection: Selection
    preview_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')


def portable_preset(raw, index):
    """Remove free labels/IDs while retaining computational parameters."""
    preset = Preset.model_validate(raw)
    PreparedRoutes(preset)
    validate_macros(preset)
    value = preset.model_dump()
    value.update(id=f'preset-{index}', name=f'Preset {index+1}', favorite=False)
    for voice in value['voices']: voice['label'] = f"Voz {voice['id']}"
    for i, route in enumerate(value['routes']):
        route['id'] = f'route-{i}'
        for term in route['terms']:
            if term['source'] not in signal_catalog() or term['input_unit'] != signal_catalog()[term['source']]:
                raise ValueError('Summary export requires known signal names and units')
    for i, macro in enumerate(value['macros']): macro.update(id=f'macro-{i}', label=f'Macro {i+1}')
    return value


def plan(evaluation, ident, selection):
    selection = Selection.model_validate(selection)
    report = evaluation.report(ident)
    manifest = report['manifest']
    # Bind summary/recipes to the verified frozen request, not mutable UI drafts.
    evaluation.artifact(ident, 'request.json')
    inventory = manifest['runs']
    if max(selection.run_indices) >= len(inventory): raise ValueError('Run outside comparison')
    indices = sorted(selection.run_indices)
    sources = sorted({inventory[i]['source_index'] for i in indices})
    presets = sorted({inventory[i]['preset_index'] for i in indices})
    summary = {'format': 'weaver-selected-summary/v1',
        'limits': ['Derived movement results may remain sensitive; review before sharing',
                   'Summary omits original labels, paths, identities and source calibration',
                   'Only catalogued signals with matching units are summarized; omissions are counted',
                   'Common support belongs to the full original preset matrix, not a recomputed selection',
                   'No scientific, perceptual or physical synchronization validation implied',
                   'Video and tracking are not included; reproduction requires the original local inputs'],
        'clock': manifest['clock'], 'output_stage': manifest['output_stage'], 'audio_stage': manifest.get('audio_stage'),
        'control_hz': manifest['request']['control_hz'], 'preroll_s': manifest['request']['preroll_s'],
        'code': {k: manifest['code'].get(k) for k in ('head','replay_files','replay_sha256','python','packages')},
        'presets': [portable_preset(manifest['request']['presets'][pi], pi) for pi in presets],
        'sources': [{'index': si, 'start_s': manifest['request']['sources'][si]['start_s'],
                     'end_s': manifest['request']['sources'][si]['end_s'],
                     'calibration_present': manifest['request']['sources'][si].get('torso_scale') is not None} for si in sources],
        'runs': [], 'comparisons': []}
    documents = {}
    artifacts = []
    catalog = signal_catalog()
    for ordinal, index in enumerate(indices):
        entry = inventory[index]
        signals = {name: {key: value for key, value in stats.items() if key in
                   ('observed_count','mean_available','max_invalid_s_on_control_clock','observed_fraction_on_control_clock')}
                   | {'unit': catalog[name]} for name, stats in entry['signals'].items()
                   if name in catalog and stats['unit'] == catalog[name]}
        row = {key: entry[key] for key in ('source_index','preset_index','rows','sounding_fraction','mean_sum_target_gain')}
        row.update(run_index=index, signals=signals, omitted_signal_count=len(entry['signals'])-len(signals))
        if entry.get('pcm'):
            row['pcm'] = {k: entry['pcm'][k] for k in ('rms','peak','samples','sample_rate','stage') if k in entry['pcm']}
        summary['runs'].append(row)
        if selection.include_requests:
            request = Request.model_validate(manifest['request']).model_copy(deep=True)
            request.sources = [request.sources[entry['source_index']]]
            request.presets = [request.presets[entry['preset_index']]]
            documents[f'requests/run-{ordinal:04d}.json'] = request.model_dump()
        names = [(entry['file'], f'traces/run-{ordinal:04d}.jsonl', entry['sha256'])] if selection.include_traces else []
        if selection.include_pcm and entry.get('pcm'):
            names += [(entry['pcm']['file'], f'pcm/run-{ordinal:04d}.wav', entry['pcm']['sha256']),
                      (entry['pcm']['voice_frames'], f'pcm/run-{ordinal:04d}.voice-frames.jsonl', entry['pcm']['voice_frames_sha256'])]
        for original, destination, checksum in names:
            path = evaluation.artifact(ident, original)
            artifacts.append({'archive_name': destination, 'path': str(path),
                              'sha256': checksum, 'bytes': path.stat().st_size})
    for comparison in report['comparisons']:
        si = comparison['source_index']
        if si not in sources: continue
        pis = [inventory[i]['preset_index'] for i in indices if inventory[i]['source_index']==si]
        summary['comparisons'].append({'source_index': si, 'signals': {
            name: {'unit': stats['unit'], 'common_count': stats['common_count'],
                   'selected_preset_indices': pis, 'means_same_support': [stats['means_same_support'][pi] for pi in pis],
                   'support_matrix_preset_count': len(manifest['request']['presets'])}
            for name, stats in comparison['signals'].items() if name in catalog and stats['unit']==catalog[name]}})
    documents['summary.json'] = summary
    data = {'selection': selection.model_dump(), 'documents': documents, 'artifacts': artifacts}
    files = [{'archive_name': name, 'bytes': len((canonical(value)+'\n').encode()),
              'sha256': hashlib.sha256((canonical(value)+'\n').encode()).hexdigest()} for name,value in sorted(documents.items())]
    files += [{k:a[k] for k in ('archive_name','bytes','sha256')} for a in artifacts]
    data['inventory'] = sorted(files, key=lambda f:f['archive_name'])
    size = sum(f['bytes'] for f in files)
    if size > selection.max_mb*1024**2: raise ValueError('Package exceeds selected size budget')
    return data


def preview(evaluation, ident, selection):
    data = plan(evaluation, ident, selection)
    return {'preview_sha256': digest(data), 'files': data['inventory'],
            'payload_bytes': sum(f['bytes'] for f in data['inventory']),
            'private_context': bool(data['artifacts'] or any(name.startswith('requests/') for name in data['documents'])),
            'limits': data['documents']['summary.json']['limits']}


def run_frozen(folder):
    folder = Path(folder)
    if folder.is_symlink(): raise ValueError('Invalid package directory')
    with (folder/'worker.lock').open('a+b') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (folder/'manifest.json').exists(): raise ValueError('Package job already published')
        paths = [folder/name for name in ('request.json','input.json','job.json')]
        if any(p.is_symlink() for p in paths): raise ValueError('Invalid package input')
        hashes = {p.name:sha256_file(p) for p in paths[:2]}
        if json.loads(paths[2].read_text())['input_hashes'] != hashes: raise ValueError('Frozen package input changed')
        request = json.loads(paths[0].read_text()); data = json.loads(paths[1].read_text())
        if digest(data) != request['preview_sha256']: raise ValueError('Frozen package preview changed')
        job = {'schema_version':1,'status':'running','line':'EVAL-PACKAGE','input_hashes':hashes}
        atomic_json(folder/'manifest.json',job)
        try:
            with zipfile.ZipFile(folder/'.package.zip.partial','w',compression=zipfile.ZIP_STORED,allowZip64=True) as archive:
                def member(name):
                    info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.create_system=3;info.external_attr=0o100600<<16
                    return archive.open(info,'w',force_zip64=True)
                for name,value in sorted(data['documents'].items()):
                    with member(name) as out: out.write((canonical(value)+'\n').encode())
                for source in data['artifacts']:
                    path = Path(source['path'])
                    if path.is_symlink(): raise ValueError('Source artifact unavailable')
                    checksum=hashlib.sha256(); count=0
                    with path.open('rb') as inp, member(source['archive_name']) as out:
                        while chunk:=inp.read(1024**2):
                            count+=len(chunk);checksum.update(chunk);out.write(chunk)
                    if checksum.hexdigest()!=source['sha256'] or count!=source['bytes']:
                        raise ValueError('Source artifact changed during packaging')
                internal={'format':'weaver-selected-package/v1','selection':data['selection'],
                          'files':data['inventory'],'limits':data['documents']['summary.json']['limits']}
                with member('package-manifest.json') as out: out.write((canonical(internal)+'\n').encode())
            if any(sha256_file(folder/name)!=value for name,value in hashes.items()): raise ValueError('Package input changed')
            (folder/'.package.zip.partial').replace(folder/'package.zip')
            job.update(status='complete',output={'file':'package.zip','sha256':sha256_file(folder/'package.zip')},
                       file_count=len(data['inventory'])+1,bytes=(folder/'package.zip').stat().st_size)
            atomic_json(folder/'manifest.json',job)
        except Exception as exc:
            job.update(status='failed',error_type=type(exc).__name__);atomic_json(folder/'manifest.json',job);raise


class PackageService(CoincidenceService):
    line='EVAL-PACKAGE'
    module='harmonic_weaver.lab.evaluation.packages'
    artifacts=('manifest.json','package.zip')

    def start(self,evaluation,ident,request):
        request=CreateRequest.model_validate(request)
        data=plan(evaluation,ident,request.selection)
        if digest(data)!=request.preview_sha256: raise ValueError('Selection or results changed; refresh package preview')
        return self._start({'request.json':request.model_dump(),'input.json':data})

    def artifact(self,ident,name):
        if name not in self.artifacts:raise ValueError('Unknown package artifact')
        folder=self.folder(ident);report=self.report(ident);path=folder/name
        if path.is_symlink() or not path.is_file():raise ValueError('Package unavailable')
        if name=='manifest.json':return path
        if report['status']!='complete' or sha256_file(path)!=report['output']['sha256']:raise ValueError('Package incomplete or changed')
        return path


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--folder',type=Path,required=True)
    run_frozen(parser.parse_args().folder)
