import {FEATURES,type Values} from './geometry';
import type {Voice} from '../figure';
export const CONTOUR_SOUND_VERSION='face-contour-series/0.2';
export type MappingSettings={id:'contour'|'legacy';richness:number;detune:number};
export const DEFAULT_MAPPING:MappingSettings={id:'contour',richness:1,detune:.8};
const clip=(x:number,a=0,b=1)=>Math.max(a,Math.min(b,x));
/** Explicit geometric drives. These are neither emotion probabilities nor FACS labels. */
export function contourDrive(delta:Values,sensitivity=1){
 if(!FEATURES.every(k=>Number.isFinite(delta[k]))||!Number.isFinite(sensitivity)||sensitivity<.25||sensitivity>3)return null;
 const cornerCurve=clip(-delta.mouthCurve*sensitivity/.06);
 const brows=(delta.browL+delta.browR)/2,eyes=(delta.eyeL+delta.eyeR)/2;
 const browOpening=clip(brows*sensitivity/.08),eyeOpening=clip(eyes*sensitivity/.24);
 const opening=clip(.65*browOpening+.35*eyeOpening);
 const contraction=clip(-brows*sensitivity/.028);
 return {cornerCurve,browOpening,eyeOpening,opening,contraction,spread:Math.max(cornerCurve,opening)};
}
export function validMapping(value:unknown):value is MappingSettings{
 const m=value as MappingSettings;return !!m&&['contour','legacy'].includes(m.id)&&[m.richness,m.detune].every(x=>Number.isFinite(x)&&x>=0&&x<=1);
}
/** Richness changes partial weights; contraction changes placement on Nico's f0/2 grid. */
export function contourVoices(delta:Values,sensitivity=1,f0=110,mapping:MappingSettings=DEFAULT_MAPPING):Voice[]{
 const d=contourDrive(delta,sensitivity);
 if(!d||!validMapping(mapping)||!Number.isFinite(f0)||f0<55||f0>220)return [];
 const richness=d.spread*mapping.richness;
 const deviation=d.contraction*(1-d.spread)*mapping.detune;
 const offsets=[0,.65,-.55,.35,-.50,.40,-.30,.25];
 const weights=offsets.map((_,i)=>(i+1)**(-.8)*(i<3?1:richness));
 const norm=Math.sqrt(weights.reduce((sum,w)=>sum+w*w,0));
 return weights.map((weight,i)=>({frequency_hz:f0*(i+1+offsets[i]*deviation/2),gain:.22*weight/norm,phase_rad:0,harmonic_n:i+1}));
}
