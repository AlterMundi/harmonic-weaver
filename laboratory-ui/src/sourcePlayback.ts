import type {Playback} from './videoFollower';
// Audio zero is the selected source crop start. Instrument tail has no video.
export function sourcePlayback(time:number,playing:boolean,start:number,end:number,epoch:number,offset=0):Playback {
 if (![time,start,end,offset].every(Number.isFinite) || time<0 || end<=start)
  throw Error('Invalid source/audio clock');
 const duration=end-start,shifted=Math.min(time,duration)+offset;
 return {position:Math.max(start,Math.min(end,start+shifted)),playing:playing && time<duration && shifted>=0 && shifted<duration,epoch};
}
