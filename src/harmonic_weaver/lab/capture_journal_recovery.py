"""Salvage complete recorded JSONL rows, preserving raw files and unknown tails."""
import json
import math
from pathlib import Path
from uuid import uuid4

from .cache import atomic_json, sha256_file


def reject_constant(value):
    raise ValueError('nonfinite_json')


def recover_journal(folder):
    folder=Path(folder)
    output=folder/'journal-recovered'/uuid4().hex
    output.mkdir(mode=0o700,parents=True)
    report={'schema_version':1,'status':'partial','directory':str(output),'files':{},
            'limits':['Only valid complete recorded rows preserved; no missing observations invented',
                      'No exact end cursor or interval coverage claim',
                      'SQLite journal may contain more events; no automatic inclusion of later events']}
    for name in ('events.jsonl','timeline.jsonl'):
        source=folder/name
        entry={'rows':0,'stop_reason':'end_of_file','source_sha256':None,'output_sha256':None}
        report['files'][name]=entry
        if not source.is_file() or source.is_symlink():
            entry['stop_reason']='unavailable';continue
        entry['source_sha256']=sha256_file(source)
        previous=None
        with source.open('rb') as handle, (output/name).open('w') as target:
            while True:
                raw=handle.readline()
                if not raw:break
                try:line=raw.decode('utf-8')
                except UnicodeError:entry['stop_reason']='invalid_encoding';break
                try:
                    if not line.endswith('\n'):raise ValueError('partial_row')
                    row=json.loads(line,parse_constant=reject_constant)
                    if not isinstance(row,dict):raise ValueError('invalid_row')
                    if name=='timeline.jsonl':
                        stamp=row['sampled_monotonic_s']
                        if type(stamp) not in (int,float) or not math.isfinite(stamp) or stamp<0 or not isinstance(row['state'],dict):
                            raise ValueError('invalid_observation')
                        if previous is not None and stamp<previous:raise ValueError('nonmonotonic_observation')
                        previous=stamp
                    else:
                        sequence=row['sequence']
                        if type(sequence) is not int or sequence<1 or not isinstance(row['event'],dict):
                            raise ValueError('invalid_event')
                        if previous is not None and sequence!=previous+1:raise ValueError('discontinuous_events')
                        previous=sequence
                    target.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n');entry['rows']+=1
                except (ValueError,KeyError,TypeError) as exc:entry['stop_reason']=str(exc);break
        if sha256_file(source)!=entry['source_sha256']:
            raise ValueError('Raw journal changed during recovery')
        entry['output_sha256']=sha256_file(output/name)
    atomic_json(output/'manifest.json',report)
    return report
