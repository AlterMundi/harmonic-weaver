"""Verify recovered export inputs without upgrading partial captures to complete."""
from pathlib import Path
import json

from .cache import sha256_file


def verified_file(folder, name, expected):
    folder=Path(folder)
    path=folder/name
    if folder.is_symlink() or path.is_symlink() or not path.is_file():
        raise ValueError(f'Recovered artifact unavailable: {name}')
    if not isinstance(expected,str) or len(expected)!=64 or sha256_file(path)!=expected:
        raise ValueError(f'Recovered artifact changed: {name}')
    return path


def recovered_input(capture):
    """Return verified PCM and journal paths; never read failed raw tails."""
    if capture.get('status') not in ('failed','interrupted'):
        raise ValueError('Choose an interrupted or failed capture')
    recovery=capture.get('recovery') or {}
    pcm=recovery.get('result') or {}
    driver_id=(capture.get('shaper') or {}).get('id')
    if not driver_id or pcm.get('status')!='recovered' or pcm.get('capture_id')!=driver_id:
        raise ValueError('Recovered PCM identity is not confirmed')
    hashes=pcm.get('hashes') or {}
    audio=verified_file(pcm['directory'],'audio.wav',hashes.get('audio.wav'))
    blocks=verified_file(pcm['directory'],'blocks.jsonl',hashes.get('blocks.jsonl'))
    journal=recovery.get('journal') or {}
    if journal.get('status')!='partial':
        raise ValueError('Recovered journal is unavailable')
    files=journal.get('files') or {}
    paths={}
    for name in ('events.jsonl','timeline.jsonl'):
        entry=files.get(name) or {}
        paths[name]=verified_file(journal['directory'],name,entry.get('output_sha256'))
    import soundfile as sf
    info=sf.info(audio)
    if type(pcm.get('recovered_samples')) is not int or info.frames!=pcm['recovered_samples'] or info.frames<=0:
        raise ValueError('Recovered PCM sample count disagrees')
    with blocks.open() as handle:
        rows=[json.loads(line) for line in handle if line.strip()]
    from .capture_timeline import frame_plan
    try:
        next(frame_plan(rows,[],fps=1))
        if rows[0]['sample_rate']!=info.samplerate or sum(row['capture_frames'] for row in rows)!=info.frames:
            raise ValueError('Recovered blocks and PCM disagree')
    except (KeyError,TypeError,StopIteration) as exc:
        raise ValueError('Recovered block clock is invalid') from exc
    return {'status':'verified_partial','capture_id':capture['id'],
            'audio':str(audio),'blocks':str(blocks),'journal':{k:str(v) for k,v in paths.items()},
            'sample_rate':info.samplerate,'samples':info.frames,
            'input_hashes':{'audio.wav':hashes['audio.wav'],'blocks.jsonl':hashes['blocks.jsonl'],
                            **{name:files[name]['output_sha256'] for name in paths}},
            'limits':['Verified recovered prefixes only; capture remains incomplete',
                      'No guarantee of journal coverage through the PCM endpoint',
                      'Camera prefix requires independent verification before rendering']}
