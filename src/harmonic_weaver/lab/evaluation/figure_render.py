"""Raster display of every stored oscillator, using the web figure's phasor convention."""
import math
import numpy as np


def voices_at(blocks, seconds):
    from bisect import bisect_right
    if not blocks or not math.isfinite(seconds) or seconds < 0:return []
    sample=seconds*blocks[0]['sample_rate']
    index=bisect_right(blocks,sample,key=lambda b:b['audio_file_sample_start'])-1
    if index<0:return []
    block=blocks[index]
    if sample>=block['audio_file_sample_start']+block['crop_block_end']-block['crop_block_start']:return []
    offset=sample-block['audio_file_sample_start']+block['crop_block_start']
    fraction=min(1.,offset/max(1,block['block_frames']-1))
    return [{**v,'gain':v['gain']+(v.get('gain_end',v['gain'])-v['gain'])*fraction,
             'phase_rad':v['phase_rad']+2*math.pi*v['frequency_hz']*offset/block['sample_rate']
                +v.get('phase_offset_delta_rad',0)*fraction} for v in block['voices']]


def phasor_points(voices,samples,seconds,scale):
    points=np.zeros((samples,2),dtype=np.float64)
    times=np.linspace(0,seconds,samples)
    for voice in voices:
        phase=voice['phase_rad']+2*np.pi*voice['frequency_hz']*times
        points[:,0]+=voice['gain']*np.cos(phase)*scale
        points[:,1]+=voice['gain']*np.sin(phase)*scale
    return points


class RasterFigure:
    def __init__(self,width,height):
        self.width,self.height=width,height
        self.background=np.array([.045,.025,.015])*255 # BGR; web clear color RGB
        self.image=np.empty((height,width,3),dtype=np.float64);self.image[:]=self.background

    def draw(self,voices,visual,fundamental):
        import cv2
        self.image=self.image*visual.persistence+self.background*(1-visual.persistence)
        gain=sum(v['gain'] for v in voices)
        scale=.85*visual.scale/(max(gain,.02) if visual.auto_scale else 1.)
        palette={'ice':[1.,.85,.3],'gold':[.27,.7,1.],'violet':[1.,.5,.76]}
        color=np.array(palette[visual.color])*255
        groups=[([v],.15) for v in voices] if visual.components else []
        groups.append((voices,.9))
        for group,alpha in groups:
            if not any(v['gain']>0 for v in group):continue
            points=phasor_points(group,visual.samples,visual.window_periods/fundamental,scale)
            points[:,0]=self.width/2+points[:,0]*min(self.width,self.height)/2
            points[:,1]=self.height/2-points[:,1]*min(self.width,self.height)/2
            # Bound coordinates before integer rasterization; visual overflow clips, never wraps.
            points=np.clip(points,-100000,100000).round().astype(np.int32)
            mask=np.zeros((self.height,self.width),dtype=np.uint8)
            cv2.polylines(mask,[points],False,255,max(1,round(visual.line_width)),lineType=cv2.LINE_AA)
            opacity=(mask.astype(np.float64)/255*min(1.,alpha*visual.brightness))[:,:,None]
            self.image=self.image*(1-opacity)+color*opacity
        return np.clip(self.image,0,255).round().astype(np.uint8)
