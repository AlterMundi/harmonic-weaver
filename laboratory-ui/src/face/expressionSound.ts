import {validRegionalReference,type RegionalFeature,type RegionalValues,type RegionalReference} from './regions';
import type {Voice} from '../figure';
import {FACE_FUNDAMENTAL,validFundamental} from './tuning';

export const EXPRESSION_SOUND_VERSION='face-expression-axis/0.1';
export type ExpressionSoundSettings={joyH:number;angerH:number;depth:number;motion:'continuous'|'steps'};
export const DEFAULT_EXPRESSION_SOUND:ExpressionSoundSettings={joyH:1,angerH:11,depth:1,motion:'continuous'};
export type ExpressionAxis={joy:number|null;anger:number|null;ratio:number};
const finite=(x:unknown):x is number=>typeof x==='number'&&Number.isFinite(x);
const clip=(x:number)=>Math.max(0,Math.min(1,x));
export function validExpressionSound(x:unknown):x is ExpressionSoundSettings{
 const s=x as ExpressionSoundSettings;return !!s&&[s.joyH,s.angerH].every(v=>Number.isInteger(v)&&v>=1&&v<=16)&&finite(s.depth)&&s.depth>=0&&s.depth<=1&&['continuous','steps'].includes(s.motion);
}
/** Authored continuous cue strengths, not probabilities or discrete displayed labels. */
export function expressionAxis(delta:RegionalValues|null,reference:RegionalReference|undefined,settings:ExpressionSoundSettings=DEFAULT_EXPRESSION_SOUND,sensitivity=1):ExpressionAxis|null{
 if(!delta||!reference||!validRegionalReference(reference)||!validExpressionSound(settings)||!finite(sensitivity)||sensitivity<.25||sensitivity>3)return null;
 const strength=(cues:[RegionalFeature,number,number][],sign:number)=>{
  if(cues.some(([k])=>!finite(delta[k])||!finite(reference.noise[k])))return null;
  return Math.min(...cues.map(([k,floor,width])=>clip((sign*delta[k]!*sensitivity-Math.max(floor,3*reference.noise[k]!*sensitivity))/width)));
 };
 const joy=strength([['cornerHeightL',.008,.045],['cornerHeightR',.008,.045],['cornerLiftL',.010,.040],['cornerLiftR',.010,.040]],1);
 const anger=strength([['browHeightL',.014,.014],['browHeightR',.014,.014],['innerSlopeL',.020,.030],['innerSlopeR',.020,.030]],-1);
 if(joy===null&&anger===null)return null;
 const j=joy??0,a=anger??0,total=j+a,rest=(settings.joyH+settings.angerH)/2;
 const target=total?(j*settings.joyH+a*settings.angerH)/total:rest;
 const position=rest+(target-rest)*Math.max(j,a)*settings.depth;
 return {joy,anger,ratio:settings.motion==='steps'?Math.round(position):position};
}
/** Fixed f0 reference plus a moving voice. Sum of gains stays <=.22, not equal perceived loudness. */
export function expressionVoices(axis:ExpressionAxis|null,f0=FACE_FUNDAMENTAL):Voice[]{
 if(!axis||!validFundamental(f0)||!finite(axis.ratio)||axis.ratio<1||axis.ratio>16)return [];
 const moving=.82*clip((axis.ratio-1)/.5);
 return [{frequency_hz:f0,gain:.22*(1-moving),phase_rad:0,harmonic_n:1},{frequency_hz:f0*axis.ratio,gain:.22*moving,phase_rad:0,harmonic_n:axis.ratio}];
}
