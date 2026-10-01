"""Verify frozen typed annotations before a single-source R03 comparison."""
from hashlib import sha256
import json
import math


def verified_marks(snapshot,*,source_id,person_id,session_id,observed_epoch,category):
    if not all(isinstance(v,str) and v for v in (source_id,person_id,session_id)):
        raise ValueError('Explicit source, person and session required')
    if type(observed_epoch) is not int or observed_epoch<0:raise ValueError('Explicit observed epoch required')
    if category not in ('note','preparation','deployment','release','experience'):raise ValueError('Unknown annotation category')
    content={k:v for k,v in snapshot.items() if k!='content_sha256'}
    encoded=json.dumps(content,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    if snapshot.get('schema_version')!=1 or sha256(encoded).hexdigest()!=snapshot.get('content_sha256'):
        raise ValueError('Frozen annotation content changed')
    cursor=snapshot.get('through_sequence')
    if type(cursor) is not int or cursor<0:raise ValueError('Invalid annotation cursor')
    rows=snapshot.get('marks')
    if not isinstance(rows,list) or len(rows)>500:raise ValueError('Select at most 500 annotations')
    result=[];previous=0
    for row in rows:
        sequence=row['sequence'];event=row['event'];payload=event['payload']
        if type(sequence) is not int or not previous<sequence<=cursor:raise ValueError('Invalid annotation sequence')
        previous=sequence
        if event.get('kind')!='mark' or event.get('session_id')!=session_id or any(
            payload.get(key)!=value for key,value in {'source_id':source_id,'person_id':person_id,
            'observed_epoch':observed_epoch,'annotation_category':category,'annotation_origin':'human_button'}.items()):
            raise ValueError('Annotation context differs; freeze an explicit matching selection')
        # Pending seek marks combine clocks: refuse rather than select a convenient one.
        if payload.get('transport_epoch')!=observed_epoch:raise ValueError('Annotation was recorded across a pending discontinuity')
        stamp=event.get('source_time_s')
        if type(stamp) not in (int,float) or not math.isfinite(stamp) or stamp<0:raise ValueError('Unknown annotation source time')
        result.append({'sequence':sequence,'time_s':stamp,'frame_time_s':payload.get('frame_time_s')})
    return {'annotations':result,'input_sha256':snapshot['content_sha256'],'through_sequence':cursor,
            'context':{'source_id':source_id,'person_id':person_id,'session_id':session_id,
                       'observed_epoch':observed_epoch,'category':category},
            'limits':['Hash verifies content, not provenance attestation',
                      'Button/source clock is not corrected for reaction or physical AV latency']}
