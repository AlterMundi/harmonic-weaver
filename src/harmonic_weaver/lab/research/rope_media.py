"""Read-only R08 source binding to decoded video presentation timestamps."""
import json
import math
from pathlib import Path
from ..cache import sha256_file
from .rope_annotations import Annotation
from .rope_process import capture


def probe(path,*,cancel=None):
    path=Path(path)
    if path.is_symlink() or not path.is_file():raise ValueError('Regular local video required')
    before=sha256_file(path)
    command=['ffprobe','-v','error','-select_streams','v:0','-show_streams','-show_frames',
             '-show_entries','stream=width,height,sample_aspect_ratio:stream_tags=rotate:stream_side_data=rotation:frame=best_effort_timestamp_time,width,height',
             '-of','json',str(path)]
    output=capture(command,max_bytes=16_000_000,cancel=cancel)
    data=json.loads(output);streams=data.get('streams',[])
    if len(streams)!=1:raise ValueError('One selected video stream required')
    stream=streams[0]
    if stream.get('sample_aspect_ratio') not in ('1:1','N/A',None):raise ValueError('Non-square pixels require explicit display-coordinate adapter')
    rotations=[stream.get('tags',{}).get('rotate',0)]+[s.get('rotation',0) for s in stream.get('side_data_list',[])]
    if any(float(r)%360 for r in rotations):raise ValueError('Rotated media requires explicit display-coordinate adapter')
    width,height=stream['width'],stream['height'];frames=data.get('frames',[])
    if not frames or len(frames)>14400:raise ValueError('Video inventory requires 1–14400 decoded frames')
    times=[]
    for frame in frames:
        if frame.get('width')!=width or frame.get('height')!=height:raise ValueError('Variable video dimensions unsupported')
        value=float(frame['best_effort_timestamp_time'])
        if not math.isfinite(value):raise ValueError('Finite presentation timestamps required')
        times.append(value)
    origin=times[0];times=[t-origin for t in times]
    if any(b<=a for a,b in zip(times,times[1:])):raise ValueError('Strict decoded presentation clock required')
    if path.is_symlink() or sha256_file(path)!=before:raise ValueError('Media changed during frame probing')
    return {'schema_version':1,'media_sha256':before,'width_px':width,'height_px':height,
            'time_origin_pts_s':origin,'frame_times_s':times,
            'clock':'first_decoded_presentation_timestamp_zero',
            'limits':['No constant-fps timestamp fabrication','First video stream only; rotated/non-square-pixel sources refused',
                      'Local file integrity, not camera synchronization or identity']}


def bind(annotation,path):
    annotation=Annotation.model_validate(annotation);media=probe(path)
    if (annotation.media_sha256,annotation.width_px,annotation.height_px)!=(media['media_sha256'],media['width_px'],media['height_px']):
        raise ValueError('Rope annotation media identity/dimensions mismatch')
    for frame in annotation.frames:
        if frame.frame_index>=len(media['frame_times_s']) or abs(frame.time_s-media['frame_times_s'][frame.frame_index])>1e-6:
            raise ValueError('Rope frame differs from decoded presentation clock')
    return media


def frame_png(path,index,expected_sha256,*,cancel=None):
    """Exact decoded index, no approximate browser seek or persisted image copy."""
    return _frame_png(path,index,expected_sha256,probe(path,cancel=cancel),cancel=cancel)


def _frame_png(path,index,expected_sha256,media,*,cancel=None):
    if media['media_sha256']!=expected_sha256:raise ValueError('Video changed since editor preparation')
    if isinstance(index,bool) or not isinstance(index,int) or not 0<=index<len(media['frame_times_s']):
        raise ValueError('Frame index outside decoded inventory')
    output=capture(['ffmpeg','-v','error','-noautorotate','-i',str(path),'-map','0:v:0',
        '-vf',f'select=eq(n\\,{index})','-frames:v','1','-f','image2pipe','-c:v','png','pipe:1'],
        max_bytes=32_000_000,cancel=cancel)
    if not output.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Exact video frame decoding failed')
    if Path(path).is_symlink() or sha256_file(path)!=expected_sha256:raise ValueError('Video changed during frame decoding')
    return output
