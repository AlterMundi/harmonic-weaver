"""User-seeded candidate pixel path; no inferred rope identity or gap bridging."""
from collections import deque
import numpy as np
from pydantic import Field
from ..contracts import Contract
from .rope_annotations import Point
from .rope_mask_contract import Result


class Settings(Contract):
    component_id:int=Field(ge=1)
    start:Point
    stop:Point
    max_visited:int=Field(default=100000,ge=1,le=4_000_000)
    max_points:int=Field(default=4096,ge=2,le=4096)


def propose(mask,settings):
    mask=Result.model_validate(mask);settings=Settings.model_validate(settings)
    component=next((c for c in mask.candidate_components if c.component_id==settings.component_id),None)
    if component is None:raise ValueError('Selected mask component unavailable')
    width,height=mask.width_px,mask.height_px
    region=np.zeros((height,width),dtype=bool)
    for y,start,stop in component.runs_y_x_start_x_stop_exclusive:region[y,start:stop]=True
    def pixel(point):return min(height-1,int(point.y*height)),min(width-1,int(point.x*width))
    start=pixel(settings.start);stop=pixel(settings.stop)
    result={'schema_version':1,'line':'R08','method':'user_seeded_four_neighbor_shortest_candidate',
            'settings':settings.model_dump(),'media_sha256':mask.media_sha256,'frame_index':mask.frame_index,'time_s':mask.time_s,
            'supported':False,'cause':None,'points':[],'visited_pixels':0,
            'limits':['Shortest pixel path inside selected color region, not a verified rope centerline',
                      'Seeds are declared by the user; no endpoint identity inferred',
                      'No snapping, gap filling or connection across mask components',
                      'Wide blobs or crossings can yield arbitrary geometry; review before using',
                      'Budget exhaustion is unavailable support, never proof of absent rope']}
    if not region[start] or not region[stop]:result['cause']='seed_outside_selected_component';return result
    if start==stop:result['cause']='seeds_coincide';return result
    parents={start:None};queue=deque([start]);found=False
    while queue:
        current=queue.popleft()
        if current==stop:found=True;break
        y,x=current
        for other in ((y-1,x),(y,x-1),(y,x+1),(y+1,x)):
            yy,xx=other
            if 0<=yy<height and 0<=xx<width and region[other] and other not in parents:
                if len(parents)>=settings.max_visited:
                    result.update(cause='visited_budget_exhausted',visited_pixels=len(parents));return result
                parents[other]=current;queue.append(other)
    result['visited_pixels']=len(parents)
    if not found:result['cause']='no_connected_path';return result
    path=[];current=stop
    while current is not None:
        path.append(current)
        if len(path)>settings.max_points:result['cause']='curve_point_budget_exhausted';return result
        current=parents[current]
    result.update(supported=True,points=[{'x':(x+.5)/width,'y':(y+.5)/height} for y,x in reversed(path)])
    return result
