import type {Playback} from './videoFollower';
// Audio zero is the selected source crop start. Instrument tail has no video.
export function sourcePlayback(time:number,playing:boolean,start:number,end:number,epoch:number):Playback {
 if (![time,start,end].every(Number.isFinite) || time<0 || end<=start)
  throw Error('Invalid source/audio clock');
 return {position:Math.min(end,start+time),playing:playing && time<end-start,epoch};
}
