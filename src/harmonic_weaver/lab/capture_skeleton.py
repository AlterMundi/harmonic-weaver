"""Draw only observed joints bound to the sampled video reference."""
from .contracts import MotionFrame

EDGES = ((5,6),(5,7),(7,9),(6,8),(8,10),(5,11),(6,12),
         (11,12),(11,13),(13,15),(12,14),(14,16))


def draw_skeleton(image, row, observation, settings, *, source_size=None):
    import cv2
    def omit(reason):
        return {'status':'omitted','reason':reason}
    source = row.get('source')
    if not source or not observation:
        return omit('video_gap')
    state = observation['state']
    raw = state.get('motion_frame')
    if raw is None:
        return omit('pose_not_recorded')
    try:
        pose = MotionFrame.model_validate(raw)
    except ValueError:
        return omit('invalid_pose')
    if pose.coordinate_frame != 'camera_isotropic' or pose.unit != 'frame_height':
        return omit('projection_unavailable')
    runtime = state.get('runtime') or {}
    if runtime.get('observed_epoch') != runtime.get('epoch') or runtime.get('epoch') is None:
        return omit('epoch_unconfirmed')
    if source['kind'] == 'camera':
        if pose.stream_id != source['stream_id'] or pose.sequence != source['sequence']:
            return omit('camera_frame_mismatch')
        width, height = source.get('source_width'), source.get('source_height')
    else:
        job = (state.get('source') or {}).get('job') or {}
        if pose.source_id != source.get('media_id') or pose.stream_id != job.get('id'):
            return omit('file_identity_mismatch')
        if abs(pose.source_time_s-source['position_s']) > settings.skeleton_max_offset_s + 1e-9:
            return omit('pose_video_offset')
        width, height = pose.width, pose.height
    if (width,height) != (pose.width,pose.height):
        return omit('image_geometry_mismatch')
    if source_size and abs(source_size[0]/source_size[1]-width/height) > 1e-3:
        return omit('image_aspect_mismatch')
    selected = (state.get('session') or {}).get('person_id')
    people = [p for p in pose.persons if settings.skeleton_people == 'all' or p.person_id == selected]
    if not people:
        return omit('person_not_observed')
    h,w = image.shape[:2]
    scale = min(w/width,h/height)
    rw,rh = max(1,round(width*scale)),max(1,round(height*scale))
    x,y = (w-rw)//2,(h-rh)//2
    joints = 0
    identities = []
    for person in people:
        points = {}
        for joint in person.joints:
            if joint.state != 'observed' or joint.confidence < settings.skeleton_confidence:
                continue
            px,py = joint.position[:2]
            # Ignore coordinates outside the recorded image; never bridge them.
            if not 0 <= px <= width/height or not 0 <= py <= 1:
                continue
            points[joint.index] = (x+round(px*rw/(width/height)),y+round(py*rh))
        color = (255,255,0) if person.person_id == selected else (0,200,255)
        for a,b in EDGES:
            if a in points and b in points:
                cv2.line(image,points[a],points[b],color,settings.skeleton_line_px,cv2.LINE_AA)
        for point in points.values():
            cv2.circle(image,point,settings.skeleton_line_px+1,color,-1,cv2.LINE_AA)
        if points:
            joints += len(points)
            identities.append(person.person_id)
    if not joints:
        return omit('no_observed_joints')
    return {'status':'drawn','persons':identities,'joints':joints,
            'sequence':pose.sequence,'source_time_s':pose.source_time_s}
