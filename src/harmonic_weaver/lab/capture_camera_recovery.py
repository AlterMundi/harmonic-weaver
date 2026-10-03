"""Verify an inactive camera journal prefix without changing or copying images."""
import fcntl
import json
import math
from pathlib import Path
import re
from uuid import uuid4

from .cache import atomic_json,sha256_file


def recover_camera(folder):
    root=Path(folder);camera=root/'camera'
    if camera.is_symlink() or not camera.is_dir():raise ValueError('No camera journal available')
    paths={name:camera/name for name in ('writer.lock','frames.jsonl','manifest.json')}
    if any(path.is_symlink() or not path.is_file() for path in paths.values()):
        raise ValueError('Camera recovery requires writer lock and original journal metadata')
    with paths['writer.lock'].open('rb') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:raise ValueError('Camera writer is active') from exc
        manifest=json.loads(paths['manifest.json'].read_text())
        if manifest.get('status')=='complete':raise ValueError('Camera capture is already complete')
        before={name:sha256_file(paths[name]) for name in ('frames.jsonl','manifest.json')}
        rows=[];reason='end_of_journal';last=None
        with paths['frames.jsonl'].open('rb') as handle:
            for raw in handle:
                if not raw.endswith(b'\n'):reason='truncated_row';break
                try:
                    row=json.loads(raw)
                    if not re.fullmatch(r'[0-9]{8}\.jpg',row['file']) or not re.fullmatch(r'[a-f0-9]{64}',row['sha256']):raise ValueError('Invalid image reference')
                    if row['file']!=f'{len(rows):08d}.jpg':raise ValueError('Nonconsecutive image index')
                    if not isinstance(row['stream_id'],str) or not row['stream_id']:raise ValueError('Invalid stream')
                    if type(row['sequence']) is not int or row['sequence']<0:raise ValueError('Invalid sequence')
                    clocks=[row[key] for key in ('captured_monotonic_s','available_monotonic_s','collector_monotonic_s')]
                    if any(type(value) not in (int,float) or not math.isfinite(value) or value<0 for value in clocks):raise ValueError('Invalid clock')
                    if last and (row['collector_monotonic_s']<last['collector_monotonic_s'] or
                        (row['stream_id']==last['stream_id'] and row['sequence']<=last['sequence'])):raise ValueError('Nonmonotonic camera journal')
                    image=camera/row['file']
                    if image.is_symlink() or not image.is_file() or sha256_file(image)!=row['sha256']:raise ValueError('Missing or changed image')
                    rows.append(row);last=row
                except (KeyError,TypeError,ValueError,UnicodeDecodeError,OSError) as exc:
                    reason=f'invalid_row: {exc}';break
        after={name:sha256_file(paths[name]) for name in before}
        if before!=after:raise ValueError('Camera journal changed during recovery')
        output=root/'camera-recovered'/uuid4().hex;output.mkdir(parents=True,mode=0o700)
        index=output/'frames.jsonl'
        index.write_text(''.join(json.dumps(row,sort_keys=True,allow_nan=False)+'\n' for row in rows))
        result={'status':'recovered','directory':str(output),'frame_root':str(camera),
            'verified_frames':len(rows),'stop_reason':reason,'source_hashes':before,'index_sha256':sha256_file(index),
            'limits':['Verified prefix only; not a complete capture','Images remain at original paths and must be reverified when consumed','No inferred frames, clock synchronization or audiovisual export']}
        atomic_json(output/'manifest.json',result);return result
