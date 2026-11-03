import type {Values} from './geometry';
import type {Voice} from '../figure';
export const SOUND_VERSION='face-six-sines/0.1';
const clip=(x:number,a:number,b:number)=>Math.max(a,Math.min(b,x));
export function voicesFor(delta:Values,sensitivity=1,fundamental=110):Voice[]{
 const moves=[delta.radial*3,delta.browL*7,delta.browR*7,delta.eyeL*2,delta.eyeR*2,delta.mouth*1.2];
 const curves=[0,delta.browCurveL*5,delta.browCurveR*5,delta.asymmetry*4,-delta.asymmetry*4,delta.mouthCurve*6];
 return moves.map((v,i)=>({frequency_hz:clip(fundamental*(i+1)*2**clip(curves[i]*sensitivity,-.2,.2),55,1600),
  gain:(i===0?.13:.045)+clip(Math.abs(v*sensitivity),0,1)*.075,phase_rad:0,harmonic_n:i+1}));
}
/** Sample-clock gain lease, also exercised with the browser OfflineAudioContext. */
export function leaseGain(parameter:AudioParam,target:number,now:number){
 parameter.cancelAndHoldAtTime(now);parameter.linearRampToValueAtTime(target,now+.04);
 parameter.setValueAtTime(target,now+.28);parameter.linearRampToValueAtTime(0,now+.42);
}
/** Native oscillators run on the audio thread. Every update carries a finite gain lease. */
export class FaceSound{
 readonly context=new AudioContext({latencyHint:'interactive'});
 readonly master=this.context.createGain();readonly destination=this.context.createMediaStreamDestination();
 private nodes:{osc:OscillatorNode;gain:GainNode}[]=[];
 enabled=false;volume=.25;last:Voice[]=[];
 constructor(){
  const compressor=this.context.createDynamicsCompressor();compressor.threshold.value=-15;compressor.ratio.value=8;
  this.master.gain.value=this.volume;this.master.connect(compressor);compressor.connect(this.context.destination);compressor.connect(this.destination);
  this.nodes=Array.from({length:6},()=>{const osc=this.context.createOscillator(),gain=this.context.createGain();gain.gain.value=0;osc.type='sine';osc.connect(gain);gain.connect(this.master);osc.start();return {osc,gain};});
 }
 async start(){await this.context.resume();if(this.context.state!=='running')throw Error('Tocá Activar sonido para habilitar el audio.');this.enabled=true;}
 setVolume(v:number){this.volume=clip(v,0,1);this.master.gain.setTargetAtTime(this.volume,this.context.currentTime,.025);}
 update(voices:Voice[]){
  this.last=voices;const now=this.context.currentTime;
  this.nodes.forEach(({osc,gain},i)=>{
   const v=voices[i];osc.frequency.setTargetAtTime(v?.frequency_hz||110,now,.04);
   const target=this.enabled?(v?.gain||0):0;leaseGain(gain.gain,target,now);
  });
 }
 silence(){const now=this.context.currentTime;this.nodes.forEach(({gain})=>{gain.gain.cancelAndHoldAtTime(now);gain.gain.linearRampToValueAtTime(0,now+.04);});this.last=[];}
 mute(){this.enabled=false;this.silence();}
 async close(){this.mute();this.nodes.forEach(({osc})=>osc.stop());await this.context.close();}
}
