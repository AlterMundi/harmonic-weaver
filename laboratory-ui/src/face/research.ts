import {FEATURES,GEOMETRY_VERSION,type Values,type Baseline,type Center,type GeometryMode,HEAD_GEOMETRY_VERSION} from './geometry';
import {SOUND_VERSION} from './sound';
import {validMapping,type MappingSettings} from './contourSound';
import {EXPRESSION_VERSION,EXPRESSION_FEATURES,validExpressionReference,type ExpressionValues} from './expression';
export const MODEL_SHA='64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff';
export const LEGACY_PROTOCOL={schema:'face-mirror-protocol/v1',geometry:GEOMETRY_VERSION,sound:SOUND_VERSION,model_sha256:MODEL_SHA,sdk:'@mediapipe/tasks-vision@1.2.0',
 sample_clock:'Main-thread receipt performance.now; not physical camera/audio synchronization.',
 measurement:'Projected2D, aspect-corrected, eye-width normalized, translation/scale/roll removed. Frontal face only; inferred3D is not measured surface curvature.',
 mapping:'Six sine voices; radial/brow/aperture changes affect gain, signed bend/asymmetry changes affect partial frequencies. This is a designed exploratory map, not a natural emotion-to-frequency law.',
 scope:'Exploratory feasibility. No emotion/sincerity/health classifier. No participant results from software examples.',
 consent:'Adult voluntary local use. Metrics and reference remain in page memory; only explicit export creates a file. No raw image/audio recording in this version. Delete/withdraw clears local records; previously exported copies require deletion by their holder.',
 questions:['¿Qué sentiste al hacer este gesto?','¿Qué te transmite al verlo o escucharlo?'],
 controls:'First collect silent video perceptions independently. Later compare video, sound and matched/unmatched AV with level/timbre controls and a prospective frozen mapping. This interface records practitioner trials; it does not claim to implement the full observer experiment.',
 research_plan:'docs/laboratory/face/RESEARCH_PLAN.md',
} as const;
export const V2_PROTOCOL={...LEGACY_PROTOCOL,schema:'face-mirror-protocol/v2',sound:'face-contour-series/0.2',
 mapping:'Contour geometry only: signed mouth bend and brow/eye opening enrich a three-to-eight partial series; brow contraction displaces upper partials on the intended f0/2 grid. Legacy six-voice mode remains available. No emotion classifier or skin-fold segmentation.',
 sound_maps:['face-contour-series/0.2','face-six-sines/0.1'],
} as const;
export const V3_PROTOCOL={...V2_PROTOCOL,schema:'face-mirror-protocol/v3',
 scope:'Exploratory feasibility with optional authored expression suggestions. No validation of emotion, sincerity or health. No participant results from software examples.',
 expression_readout:{version:EXPRESSION_VERSION,method:'Four authored geometric prototypes relative to a personal resting reference, MAD noise floors and 500ms persistence. No trained emotion/AU model; no probabilities. Sound does not use these labels.',
 exposure:'Hidden throughout trials and stays hidden afterward until explicitly enabled. Trial metadata retains prior enablement and previously seen suggestions; old imports have unknown exposure, not a claim of blinding.',
 samples:'Optional expressionValues contain point-derived heights, slopes, corner offsets and apertures. Personal expression reference is a separate optional baseline field. No image pixels.'},
} as const;
export const PROTOCOL={...V3_PROTOCOL,schema:'face-mirror-protocol/v4',geometry:HEAD_GEOMETRY_VERSION,geometry_modes:['projected','head-aligned'],measurement:'Legacy projected2D or head-aligned relative3D estimates using eye corners and nasal bridge; no iris/pupil-center gate. Moderate yaw only, no measured3D or profile accuracy claim. Trial and baseline identify the selected mode.'} as const;
export type Sample={timeMs:number;values:Values|null;delta:Values|null;reason?:string;expressionValues?:ExpressionValues|null};
export type Reflection={felt:string;perceived:string;tension:number|null;pleasantness:number|null};
export type Trial={geometryMode?:GeometryMode;expressionReadout?:{version:typeof EXPRESSION_VERSION;enabledBeforeTrial:boolean;suggestionSeenBeforeTrial:boolean;labelsDuringTrial:false};mapping?:MappingSettings;id:string;origin:'camera'|'synthetic';startedAt:string;durationMs:number;complete:boolean;endReason:string|null;center:Center;baseline:Baseline;sensitivity:number;fundamental:number;volume:number;soundEnabled:boolean;audioEvents:{timeMs:number;enabled:boolean}[];task:string;samples:Sample[];reflection:Reflection};
export function canonical(value:unknown):string{
 if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';
 if(value!==null&&typeof value==='object')return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical((value as Record<string,unknown>)[k])).join(',')+'}';
 return JSON.stringify(value);
}
export async function digest(value:unknown){return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(canonical(value)))),v=>v.toString(16).padStart(2,'0')).join('');}
export async function documentFor(trials:Trial[]){return {schema:'face-mirror-session/v4',protocol:PROTOCOL,protocol_sha256:await digest(PROTOCOL),exportedAt:new Date().toISOString(),trials};}
const cell=(v:unknown)=>{let s=v==null?'':String(v);if(typeof v==='string'&&/^[=+@\-\t\r]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';};
export function csv(trials:Trial[]){
 const header=['trial_id','origin','task','time_ms','valid','gap_reason','center',...FEATURES,...FEATURES.map(k=>'delta_'+k),'felt','perceived','tension','pleasantness','mapping_id','richness_depth','detune_depth','expression_readout_version','readout_enabled_before_trial','suggestion_seen_before_trial','labels_during_trial',...EXPRESSION_FEATURES.map(k=>'expression_'+k),'geometry_mode'];
 const rows=trials.flatMap(t=>t.samples.map(s=>[t.id,t.origin,t.task,s.timeMs,!!s.values,s.reason,t.center,...FEATURES.map(k=>s.values?.[k]??null),...FEATURES.map(k=>s.delta?.[k]??null),t.reflection.felt,t.reflection.perceived,t.reflection.tension,t.reflection.pleasantness,t.mapping?.id??'legacy',t.mapping?.richness??1,t.mapping?.detune??1,t.expressionReadout?.version,t.expressionReadout?.enabledBeforeTrial,t.expressionReadout?.suggestionSeenBeforeTrial,t.expressionReadout?.labelsDuringTrial,...EXPRESSION_FEATURES.map(k=>s.expressionValues?.[k]??null),t.geometryMode??'projected'].map(cell).join(',')));
 return [header.map(cell).join(','),...rows].join('\r\n');
}
export function validateSession(raw:unknown):Trial[]{
 const d=raw as {schema?:string;protocol?:unknown;protocol_sha256?:string;trials?:Trial[]};
 const legacy=d?.schema==='face-mirror-session/v1'&&canonical(d.protocol)===canonical(LEGACY_PROTOCOL);
 const v2=d?.schema==='face-mirror-session/v2'&&canonical(d.protocol)===canonical(V2_PROTOCOL);
 const v3=d?.schema==='face-mirror-session/v3'&&canonical(d.protocol)===canonical(V3_PROTOCOL);
 if(!(legacy||v2||v3||d?.schema==='face-mirror-session/v4'&&canonical(d.protocol)===canonical(PROTOCOL))||!Array.isArray(d.trials)||d.trials.length>50)throw Error('Archivo de sesión incompatible.');
 const ids=new Set();
 for(const t of d.trials){
  if(t.geometryMode!==undefined&&!['projected','head-aligned'].includes(t.geometryMode))throw Error('Comparación geométrica inválida.');
  if(!legacy&&!validMapping(t.mapping))throw Error('Mapeo de ensayo inválido.');
  if(typeof t.complete!=='boolean'||!(t.endReason===null||typeof t.endReason==='string'&&t.endReason.length<=300)||typeof t.soundEnabled!=='boolean'||!Array.isArray(t.audioEvents)||t.audioEvents.length>200||t.audioEvents.some(e=>!Number.isFinite(e.timeMs)||e.timeMs<0||e.timeMs>t.durationMs+500||typeof e.enabled!=='boolean'))throw Error('Estado de ensayo inválido.');
  if(typeof t.id!=='string'||ids.has(t.id)||!['camera','synthetic'].includes(t.origin)||!['bridge','eyes'].includes(t.center)||!t.baseline||t.baseline.center!==t.center||t.baseline.schema!=='face-baseline/v1'||!Array.isArray(t.samples)||t.samples.length>1200||!Number.isFinite(t.durationMs)||t.durationMs<0||t.durationMs>30000||typeof t.task!=='string'||t.task.length>300)throw Error('Ensayo inválido.');ids.add(t.id);
  if(!Number.isFinite(t.sensitivity)||t.sensitivity<.25||t.sensitivity>3||!Number.isFinite(t.fundamental)||t.fundamental<55||t.fundamental>220||!Number.isFinite(t.volume)||t.volume<0||t.volume>1)throw Error('Mapeo inválido.');
  if(t.baseline.geometryMode!==undefined&&t.baseline.geometryMode!==(t.geometryMode??'projected'))throw Error('La referencia no coincide con la comparación geométrica.');
  if(!FEATURES.every(k=>Number.isFinite(t.baseline.values[k])&&Number.isFinite(t.baseline.noise[k])))throw Error('Referencia inválida.');
  if(t.baseline.expressionReference!==undefined&&!validExpressionReference(t.baseline.expressionReference))throw Error('Referencia de expresión inválida.');
  const e=t.expressionReadout;if(e&&(e.version!==EXPRESSION_VERSION||typeof e.enabledBeforeTrial!=='boolean'||typeof e.suggestionSeenBeforeTrial!=='boolean'||e.labelsDuringTrial!==false))throw Error('Contexto de lectura inválido.');
  let time=-1;for(const s of t.samples){
   if(s.expressionValues!==undefined&&s.expressionValues!==null&&(!s.values||!t.baseline.expressionReference||!EXPRESSION_FEATURES.every(k=>Number.isFinite(s.expressionValues![k]))))throw Error('Medidas de expresión inválidas.');
   if(!Number.isFinite(s.timeMs)||s.timeMs<time||s.timeMs>t.durationMs+500||s.timeMs<0||!((s.values===null&&s.delta===null)||(s.values&&s.delta&&FEATURES.every(k=>Number.isFinite(s.values![k])&&Number.isFinite(s.delta![k])&&Math.abs((s.values![k]-t.baseline.values[k])-s.delta![k])<1e-6))))throw Error('Lectura inválida.');time=s.timeMs;
  }
  const r=t.reflection;if(!r||typeof r.felt!=='string'||typeof r.perceived!=='string'||r.felt.length>2000||r.perceived.length>2000||![r.tension,r.pleasantness].every(v=>v===null||Number.isFinite(v)&&v>=0&&v<=100))throw Error('Respuesta inválida.');
 }
 return d.trials.map(t=>({...t,mapping:legacy?{id:'legacy',richness:1,detune:1}:t.mapping}));
}
