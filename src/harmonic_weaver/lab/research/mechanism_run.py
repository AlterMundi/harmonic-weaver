"""One frozen R05 comparison, two raw PCM arms and an explicit paired report."""
import json
from pathlib import Path
from ..cache import atomic_json,sha256_file
from .mechanism_compare import compare
from .resonator_run import run as run_excited
from .parameter_run import run as run_mapped
from .resonator_artifacts import verify as verify_arm


def run(document,request,folder):
    if set(request)-{'resonators','excitation','mapping','render'}:
        raise ValueError('Unknown mechanism comparison field')
    report=compare(document,request.get('resonators',{}),request.get('excitation',{}),
                   request.get('mapping',{}),request.get('render',{}))
    folder=Path(folder);folder.mkdir(mode=0o700,parents=True,exist_ok=False)
    atomic_json(folder/'input.json',document);atomic_json(folder/'request.json',request)
    manifest={'schema_version':1,'line':'R05','kind':'mechanism_comparison','status':'running',
        'input_hashes':{name:sha256_file(folder/name) for name in ('input.json','request.json')},
        'limits':report['limits']+['Raw WAV levels differ; no loudness matching applied',
            'Report render and persisted arms are separate deterministic traversals',
            'Local hash integrity, not signed custody or human validation']}
    atomic_json(folder/'manifest.json',manifest)
    try:
        run_excited(document,{'resonators':report['resonator_preparation']['resonators'],
            'excitation':report['resonator_preparation']['excitation']['settings'],
            'render':report['resonator_preparation']['render']},folder/'excited')
        run_mapped(document,{'carriers':report['mapping_preparation']['carriers'],
            'mapping':report['mapping_preparation']['mapping'],
            'render':report['mapping_preparation']['render']},folder/'mapped')
        arms={name:verify_arm(folder/name) for name in ('excited','mapped')}
        if arms['excited']['pcm']!=arms['mapped']['pcm'] or arms['excited']['levels']['frames']!=arms['mapped']['levels']['frames']:
            raise ValueError('Persisted comparison clocks differ')
        for name,digest in manifest['input_hashes'].items():
            if (folder/name).is_symlink() or sha256_file(folder/name)!=digest:
                raise ValueError('Frozen comparison input changed')
        atomic_json(folder/'result.json',report)
        manifest.update(status='complete',output={'file':'result.json','sha256':sha256_file(folder/'result.json')},
            arm_manifest_hashes={name:sha256_file(folder/name/'manifest.json') for name in arms},
            code_hashes={name:sha256_file(Path(__file__).with_name(name))
                         for name in ('mechanism_run.py','mechanism_compare.py')},
            environment=arms['excited']['environment'])
        atomic_json(folder/'manifest.json',manifest)
    except Exception as exc:
        manifest.update(status='failed',error_type=type(exc).__name__)
        manifest.pop('output',None);manifest.pop('arm_manifest_hashes',None)
        atomic_json(folder/'manifest.json',manifest);raise
    return manifest


def verify(folder):
    folder=Path(folder)
    if folder.is_symlink() or not folder.is_dir():raise ValueError('Regular comparison folder required')
    for name in ('manifest.json','input.json','request.json','result.json'):
        if (folder/name).is_symlink() or not (folder/name).is_file():raise ValueError('Comparison artifact unavailable')
    manifest_sha=sha256_file(folder/'manifest.json');manifest=json.loads((folder/'manifest.json').read_text())
    if manifest.get('schema_version')!=1 or manifest.get('status')!='complete' or manifest.get('kind')!='mechanism_comparison' or manifest.get('line')!='R05':
        raise ValueError('Complete comparison required')
    if set(manifest['input_hashes'])!={'input.json','request.json'} or set(manifest['arm_manifest_hashes'])!={'excited','mapped'} or manifest['output']['file']!='result.json':
        raise ValueError('Comparison inventory invalid')
    hashes={**manifest['input_hashes'],'result.json':manifest['output']['sha256']}
    for name,digest in hashes.items():
        if sha256_file(folder/name)!=digest:raise ValueError('Comparison hash mismatch')
    report=json.loads((folder/'result.json').read_text());arms={}
    from .resonator_render import Render as ExcitedRender
    from .parameter_render import Render as MappedRender
    document=json.loads((folder/'input.json').read_text());request=json.loads((folder/'request.json').read_text())
    if set(request)-{'resonators','excitation','mapping','render'}:raise ValueError('Unknown comparison field')
    excited=ExcitedRender(document,request.get('resonators',{}),request.get('excitation',{}),request.get('render',{}))
    carriers={**excited.resonators.model_dump(),'coupling_per_s':0.,'topology':'isolated','adjacency':None}
    mapped=MappedRender(document,carriers,request.get('mapping',{}),excited.settings.model_dump())
    if report['resonator_preparation']!=excited.manifest or report['mapping_preparation']!=mapped.manifest:
        raise ValueError('Frozen comparison request differs from preparation')
    for name,digest in manifest['arm_manifest_hashes'].items():
        if sha256_file(folder/name/'manifest.json')!=digest:raise ValueError('Comparison arm manifest changed')
        arms[name]=verify_arm(folder/name)
        if arms[name]['input_hashes']['input.json']!=manifest['input_hashes']['input.json']:
            raise ValueError('Comparison arms do not share frozen input')
    if report['resonator_preparation']!=arms['excited']['preparation'] or report['mapping_preparation']!=arms['mapped']['preparation']:
        raise ValueError('Comparison preparation differs from PCM arms')
    if arms['excited']['pcm']!=arms['mapped']['pcm'] or report['clock']['total_frames']!=arms['excited']['levels']['frames'] or report['clock']['total_frames']!=arms['mapped']['levels']['frames']:
        raise ValueError('Comparison PCM clocks differ')
    for name,digest in {**hashes,'manifest.json':manifest_sha}.items():
        if (folder/name).is_symlink() or sha256_file(folder/name)!=digest:raise ValueError('Comparison changed during verification')
    return manifest
