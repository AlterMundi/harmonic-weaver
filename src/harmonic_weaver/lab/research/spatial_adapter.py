"""Loss-aware adapter from laboratory MotionFrames; no coordinate invention."""
from pydantic import Field
from ..contracts import Contract,MotionFrame
from .spatial_observations import Clock,Stream


class Request(Contract):
    frames:list[MotionFrame]=Field(min_length=1,max_length=14400)
    person_id:str=Field(min_length=1,max_length=80)
    clock:Clock


def convert(request):
    request=Request.model_validate(request);first=request.frames[0]
    expected=(first.source_id,first.stream_id,first.coordinate_frame,first.unit,
              first.dimensions,first.width,first.height,first.timestamp_origin)
    if (first.dimensions,first.coordinate_frame,first.unit)!=(2,'camera_isotropic','frame_height'):
        raise ValueError('Adapter requires existing camera-isotropic 2D frame-height observations')
    frames=[]
    for frame in request.frames:
        if (frame.source_id,frame.stream_id,frame.coordinate_frame,frame.unit,frame.dimensions,
            frame.width,frame.height,frame.timestamp_origin)!=expected:
            raise ValueError('Adapter requires one homogeneous source stream/clock/image geometry')
        person=next((p for p in frame.persons if p.person_id==request.person_id),None)
        joints={j.index:j for j in person.joints} if person else {}
        points=[]
        for index in range(17):
            joint=joints.get(index)
            if joint is None or joint.state=='missing':
                points.append({'label':f'joint-{index}','state':'missing','cause':
                    'person_slot_absent' if person is None else 'joint_not_present' if joint is None else 'source_joint_missing'})
            else:
                points.append({'label':f'joint-{index}','state':joint.state,
                    'position':joint.position,'confidence':joint.confidence})
        frames.append({'index':frame.sequence,'source_time_s':frame.source_time_s,'points':points})
    stream=Stream.model_validate({'source_id':first.source_id,'subject_slot':request.person_id,
        'provider':'image_pose','dimensions':2,'coordinate_frame':first.coordinate_frame,
        'units':'frame_height','clock':request.clock.model_dump(),'frames':frames})
    result={'schema_version':1,'line':'R09','request':request.model_dump(),'stream':stream.model_dump(),
        'common_times_s':[request.clock.common_time(f.source_time_s) for f in request.frames],
        'coverage':{state:sum(p.state==state for f in stream.frames for p in f.points) for state in ('observed','held','inferred','missing')},
        'timestamp_origin':first.timestamp_origin,'source_stream_id':first.stream_id,
        'image_geometry':{'width':first.width,'height':first.height},
        'limits':['Preserves camera-isotropic frame-height coordinates; not metres or inferred depth',
                  'Subject slot is an explicit tracking generation, not biometric identity',
                  'Absent joints/person remain missing; held is preserved, never upgraded to observed',
                  'Affine clock mapping is caller-declared; adapter does not measure synchronization',
                  'Sequence gaps are retained; no interpolation, calibration transfer or source switching']}

    Contract.finite_tree(result)
    return result
