"""Immutable local R08 annotation revisions; never copies participant media."""
import json
import re
from pathlib import Path
from ..cache import atomic_json,sha256_file
from .rope_annotations import Annotation,report
from .rope_media import bind


def run(annotation,media_path,folder,*,parent=None):
    annotation=Annotation.model_validate(annotation)
    media=bind(annotation,media_path)
    parent_hash=None
    if parent is not None:
        previous=verify(parent)
        if previous['media_sha256']!=annotation.media_sha256:raise ValueError('Revision must retain source media identity')
        parent_hash=sha256_file(Path(parent)/'manifest.json')
    folder=Path(folder);folder.mkdir(mode=0o700,parents=True,exist_ok=False)
    atomic_json(folder/'annotation.json',annotation.model_dump())
    atomic_json(folder/'media.json',media)
    atomic_json(folder/'result.json',report(annotation))
    if bind(annotation,media_path)!=media:
        raise ValueError('Source changed while storing annotation revision')
    manifest={'schema_version':1,'line':'R08','status':'complete','media_sha256':annotation.media_sha256,
              'parent_manifest_sha256':parent_hash,
              'input_hashes':{name:sha256_file(folder/name) for name in ('annotation.json','media.json')},
              'output':{'file':'result.json','sha256':sha256_file(folder/'result.json')},
              'code_hashes':{name:sha256_file(Path(__file__).with_name(name)) for name in ('rope_annotations.py','rope_media.py','rope_run.py')},
              'limits':['Local annotation revision, not signed custody or human validation',
                        'Media binding verified at creation; current source requires explicit rebind',
                        'Parent hash records lineage, not source path or participant identity']}
    atomic_json(folder/'manifest.json',manifest)
    return manifest


def verify(folder):
    folder=Path(folder)
    if folder.is_symlink() or not folder.is_dir():raise ValueError('Regular annotation revision required')
    names=('annotation.json','media.json','result.json','manifest.json')
    for name in names:
        if (folder/name).is_symlink() or not (folder/name).is_file():raise ValueError('Regular annotation artifacts required')
    snapshot={name:sha256_file(folder/name) for name in names}
    manifest=json.loads((folder/'manifest.json').read_text())
    if (manifest.get('schema_version'),manifest.get('line'),manifest.get('status'))!=(1,'R08','complete'):raise ValueError('Complete annotation revision required')
    if manifest.get('input_hashes')!={n:snapshot[n] for n in ('annotation.json','media.json')} or manifest.get('output')!={'file':'result.json','sha256':snapshot['result.json']}:
        raise ValueError('Annotation artifact inventory/hash mismatch')
    annotation=Annotation.model_validate_json((folder/'annotation.json').read_text())
    parent_hash=manifest.get('parent_manifest_sha256')
    if parent_hash is not None and (not isinstance(parent_hash,str) or not re.fullmatch('[a-f0-9]{64}',parent_hash)):
        raise ValueError('Valid parent manifest hash required')
    media=json.loads((folder/'media.json').read_text())
    if (media.get('media_sha256'),media.get('width_px'),media.get('height_px'))!=(annotation.media_sha256,annotation.width_px,annotation.height_px) or manifest['media_sha256']!=annotation.media_sha256:
        raise ValueError('Annotation media binding mismatch')
    times=media['frame_times_s']
    import math
    if not times or len(times)>14400 or any(type(t) not in (int,float) or not math.isfinite(t) or t<0 for t in times) or times[0]!=0 or any(b<=a for a,b in zip(times,times[1:])):
        raise ValueError('Invalid decoded media clock')
    for frame in annotation.frames:
        if frame.frame_index>=len(times) or abs(frame.time_s-times[frame.frame_index])>1e-6:raise ValueError('Annotation frame clock mismatch')
    if json.loads((folder/'result.json').read_text())!=report(annotation):raise ValueError('Annotation report differs from frozen curves')
    for name,digest in snapshot.items():
        if (folder/name).is_symlink() or sha256_file(folder/name)!=digest:raise ValueError('Annotation revision changed during verification')
    return manifest
