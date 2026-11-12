import {bulge,type Point,type ProjectedFace} from './geometry';
import {unavailable,type Evidence,type ExpressionReading,type ExpressionValues} from './expression';

/** Authored regional cues; scores are design weights, never emotion probabilities. */
export const REGIONAL_VERSION='face-expression-regions/0.1';
export const REGIONAL_FEATURES=['cornerHeightL','cornerHeightR','cornerLiftL','cornerLiftR','mouth','mouthBend','mouthTurn','eyeL','eyeR','eyeLBend','eyeLTurn','eyeRBend','eyeRTurn','browHeightL','browHeightR','innerSlopeL','innerSlopeR','browLBend','browLTurn','browRBend','browRTurn'] as const;
export type RegionalFeature=typeof REGIONAL_FEATURES[number];
export type RegionalValues=Record<RegionalFeature,number|null>;
export type RegionalReference={schema:'face-regional-reference/v1';values:RegionalValues;noise:RegionalValues};
export type RegionId='mouth'|'eyes'|'brows';
type Cue='joy'|'sadness'|'anger'|'surprise';
export type RegionReading={id:RegionId;name:string;pattern:string;label:string;detail:string;coverage:'full'|'partial'|'none';pending:boolean;votes:Partial<Record<Cue,number>>;evidence:Evidence[];arcs:{label:string;bend:number|null;change:number|null;turn:number|null;points:number[]}[];metrics:{label:string;value:number|null}[]};
export type RegionalReading={regions:RegionReading[];composite:ExpressionReading;values:RegionalValues|null;delta:RegionalValues|null;referenceReady:boolean};
const labels:Record<Cue,string>={joy:'Alegría posible',sadness:'Tristeza posible',anger:'Enojo posible',surprise:'Sorpresa posible'};
const finite=(v:unknown):v is number=>typeof v==='number'&&Number.isFinite(v);
const midpoint=(v:number[])=>{const a=[...v].sort((a,b)=>a-b),i=Math.floor(a.length/2);return a.length%2?a[i]:(a[i-1]+a[i])/2;};
export function validRegionalValues(v:RegionalValues){return !!v&&REGIONAL_FEATURES.every(k=>v[k]===null||finite(v[k]));}
export function validRegionalReference(r:RegionalReference){return r?.schema==='face-regional-reference/v1'&&validRegionalValues(r.values)&&validRegionalValues(r.noise)&&REGIONAL_FEATURES.every(k=>(r.values[k]===null)===(r.noise[k]===null)&&(r.noise[k]===null||r.noise[k]!>=0));}
export function regionalReference(frames:RegionalValues[]):RegionalReference{
 if(frames.length<10||frames.some(v=>!validRegionalValues(v)))throw Error('Faltan lecturas regionales de referencia.');
 const values={} as RegionalValues,noise={} as RegionalValues;
 for(const k of REGIONAL_FEATURES){const a=frames.map(v=>v[k]).filter(finite);values[k]=a.length>=10?midpoint(a):null;noise[k]=values[k]===null?null:midpoint(a.map(v=>Math.abs(v-values[k]!)));}
 return {schema:'face-regional-reference/v1',values,noise};
}
/** Mean chord deflection/local width and total oriented turn (radians), not skin/3D curvature. */
export function arcShape(points:Point[],center:Point){
 if(points.length<3||points.some(p=>!p||![p.x,p.y].every(Number.isFinite)))return null;
 const first=points[0],last=points.at(-1)!,span=Math.hypot(last.x-first.x,last.y-first.y),side=Math.sign(bulge(first,center,last));
 if(span<1e-6||!side)return null;
 let turn=0;
 for(let i=1;i<points.length-1;i++){const a={x:points[i].x-points[i-1].x,y:points[i].y-points[i-1].y},b={x:points[i+1].x-points[i].x,y:points[i+1].y-points[i].y};if(Math.hypot(a.x,a.y)<1e-6||Math.hypot(b.x,b.y)<1e-6)return null;turn+=Math.atan2(a.x*b.y-a.y*b.x,a.x*b.x+a.y*b.y);}
 return {bend:points.slice(1,-1).reduce((s,p)=>s+bulge(first,p,last)*side/span,0)/(points.length-2),turn:-turn*side};
}
const ARC={mouth:[61,40,37,0,267,270,291],eyeL:[362,385,386,387,263],eyeR:[33,160,159,158,133],browL:[336,296,334,293,300],browR:[70,63,105,66,107]};
export function regionalValues(frame:ProjectedFace):RegionalValues|null{
 if(!frame.ok)return null;const p=frame.points,r=Object.fromEntries(REGIONAL_FEATURES.map(k=>[k,null])) as RegionalValues;
 const value=(ids:number[],fn:()=>number)=>ids.every(i=>p[i])?fn():null;
 const gap=(a:number,b:number,c:number,d:number)=>value([a,b,c,d],()=>{const width=Math.hypot(p[c].x-p[d].x,p[c].y-p[d].y);return width>1e-6?Math.hypot(p[a].x-p[b].x,p[a].y-p[b].y)/width:NaN;});
 r.cornerHeightL=value([291],()=>-p[291].y);r.cornerHeightR=value([61],()=>-p[61].y);r.cornerLiftL=value([13,291],()=>p[13].y-p[291].y);r.cornerLiftR=value([13,61],()=>p[13].y-p[61].y);r.mouth=gap(13,14,61,291);
 r.browHeightL=value([334],()=>-p[334].y);r.browHeightR=value([105],()=>-p[105].y);r.innerSlopeL=value([300,336],()=>p[300].y-p[336].y);r.innerSlopeR=value([70,107],()=>p[70].y-p[107].y);r.eyeL=gap(386,374,362,263);r.eyeR=gap(159,145,33,133);
 for(const [name,ids] of Object.entries(ARC)){const a=ids.every(i=>p[i])?arcShape(ids.map(i=>p[i]),name.startsWith('eye')?(p[6]||frame.center):frame.center):null;r[(name+'Bend') as RegionalFeature]=a?.bend??null;r[(name+'Turn') as RegionalFeature]=a?.turn??null;}
 for(const k of REGIONAL_FEATURES)if(!finite(r[k]))r[k]=null;
 return r;
}
function compose(regions:RegionReading[],values:RegionalValues|null,delta:RegionalValues|null,referenceReady:boolean):RegionalReading{
 if(!values||!referenceReady)return {regions,values,delta,referenceReady,composite:unavailable(values?'Tomá una referencia en reposo para comparar cada zona.':'Necesitamos un rostro reciente y anclas visibles.')};
 const usable=regions.filter(r=>r.coverage!=='none'),scores:Record<Cue,number>={joy:0,sadness:0,anger:0,surprise:0};
 for(const r of usable)for(const [key,n] of Object.entries(r.votes))scores[key as Cue]+=n!;
 const candidates=(Object.keys(scores) as Cue[]).filter(k=>scores[k]>=(k==='surprise'?1:.7));
 const supporting=usable.filter(r=>candidates.some(k=>(r.votes[k]||0)>0));const pending=supporting.some(r=>r.pending);
 const oldKeys=['browHeightL','browHeightR','innerSlopeL','innerSlopeR','cornerHeightL','cornerHeightR','cornerLiftL','cornerLiftR','eyeL','eyeR','mouth'] as const;
 const d=delta&&oldKeys.every(k=>finite(delta[k]))?Object.fromEntries(oldKeys.map(k=>[k,delta[k]])) as ExpressionValues:null;
 let composite:ExpressionReading;
 if(candidates.length){const id=candidates.length>1?'mixed':candidates[0];composite={id,label:(id==='mixed'?'Gesto mixto':labels[id as Cue])+(pending?' · cambiando':''),detail:(id==='mixed'?candidates.map(k=>labels[k]).join(' + ')+'. ':'')+'Aportes: '+supporting.map(r=>r.name).join(' + ')+'. '+usable.length+'/3 zonas con medidas. No exige una coincidencia de toda la cara.',evidence:supporting.flatMap(r=>r.evidence),delta:d};}
 else if(usable.some(r=>r.pending))composite={id:'transition',label:'Observando el gesto…',detail:'Cada zona se confirma por separado.',evidence:[],delta:d};
 else if(usable.length&&usable.every(r=>r.pattern==='rest'))composite={id:'rest',label:'Sin cambio marcado',detail:'Cerca del reposo en las zonas con lectura; no equivale a calma.',evidence:[],delta:d};
 else composite={id:'unclear',label:usable.length?'Indicios por zonas':'Sin lectura de expresión',detail:'Las zonas pueden mostrar gestos distintos o incompletos. Mirá sus aportes sin forzar una emoción total.',evidence:[],delta:d};
 return {regions,composite,values,delta,referenceReady};
}
export function readRegions(values:RegionalValues|null,reference?:RegionalReference):RegionalReading{
 const ready=!!reference&&validRegionalReference(reference);const delta=values&&ready?Object.fromEntries(REGIONAL_FEATURES.map(k=>[k,values[k]===null||reference!.values[k]===null?null:values[k]!-reference!.values[k]!])) as RegionalValues:null;
 const up=(k:RegionalFeature,min:number)=>finite(delta?.[k])&&delta![k]!>Math.max(min,3*(reference?.noise[k]||0));
 const down=(k:RegionalFeature,min:number)=>finite(delta?.[k])&&-delta![k]!>Math.max(min,3*(reference?.noise[k]||0));
 const pair=(a:RegionalFeature,b:RegionalFeature,sign:'up'|'down',min:number)=>sign==='up'?up(a,min)&&up(b,min):down(a,min)&&down(b,min);
 const regions:RegionReading[]=(['mouth','eyes','brows'] as RegionId[]).map(id=>{
  const core:RegionalFeature[]=id==='mouth'?['cornerHeightL','cornerHeightR','cornerLiftL','cornerLiftR','mouth']:id==='eyes'?['eyeL','eyeR']:['browHeightL','browHeightR','innerSlopeL','innerSlopeR'];
  const seen=core.filter(k=>finite(ready?delta?.[k]:values?.[k])).length;const coverage=seen===core.length?'full':seen?'partial':'none';
  const arcs=id==='mouth'?[['Labio superior','mouth']]:id==='eyes'?[['Párpado izq.','eyeL'],['Párpado der.','eyeR']]:[['Ceja izq.','browL'],['Ceja der.','browR']];
  const row:RegionReading={id,name:{mouth:'Boca',eyes:'Ojos',brows:'Cejas'}[id],pattern:coverage==='none'?'missing':ready?'rest':'reference',label:coverage==='none'?'Sin medidas locales':ready?'Cerca del reposo':'Tomá referencia',detail:coverage==='partial'?'Lectura parcial; faltan medidas.':'',coverage,pending:false,votes:{},evidence:[],arcs:arcs.map(([label,key])=>({label,bend:values?.[(key+'Bend') as RegionalFeature]??null,change:delta?.[(key+'Bend') as RegionalFeature]??null,turn:values?.[(key+'Turn') as RegionalFeature]??null,points:ARC[key as keyof typeof ARC]})),metrics:core.map(k=>({label:({cornerHeightL:'Comisura izq. ↑',cornerHeightR:'Comisura der. ↑',cornerLiftL:'Arco comisura izq.',cornerLiftR:'Arco comisura der.',mouth:'Apertura boca',eyeL:'Apertura ojo izq.',eyeR:'Apertura ojo der.',browHeightL:'Altura ceja izq.',browHeightR:'Altura ceja der.',innerSlopeL:'Pendiente interna izq.',innerSlopeR:'Pendiente interna der.'} as Record<string,string>)[k],value:delta?.[k]??null}))};
  if(!ready||coverage==='none')return row;
  const evidence=(description:string,features:Evidence['features'],points:number[])=>row.evidence.push({description,features,points});
  if(id==='mouth'){
   if(pair('cornerHeightL','cornerHeightR','up',.008)&&pair('cornerLiftL','cornerLiftR','up',.010)){row.pattern='smile';row.label='Sonrisa posible';row.votes.joy=pair('cornerHeightL','cornerHeightR','up',.015)&&pair('cornerLiftL','cornerLiftR','up',.018)?1:.7;evidence('Comisuras hacia arriba',['cornerHeightL','cornerHeightR','cornerLiftL','cornerLiftR'],[61,13,291]);}
   else if(pair('cornerHeightL','cornerHeightR','down',.008)&&pair('cornerLiftL','cornerLiftR','down',.010)){row.pattern='down';row.label='Comisuras bajas · tristeza posible';row.votes.sadness=1;evidence('Comisuras hacia abajo',['cornerHeightL','cornerHeightR','cornerLiftL','cornerLiftR'],[61,13,291]);}
   else if(up('mouth',.10)){row.pattern='open';row.label='Boca abierta';row.detail+=' También aparece al hablar o bostezar.';row.votes.surprise=.5;evidence('Boca abierta',['mouth'],[61,13,14,291]);}
   else if(['cornerHeightL','cornerHeightR','cornerLiftL','cornerLiftR'].some(k=>up(k as RegionalFeature,.012)||down(k as RegionalFeature,.012))){row.pattern='asymmetric';row.label='Comisuras cambiantes o asimétricas';}
  }else if(id==='eyes'){
   const opened=['eyeL','eyeR'].filter(k=>up(k as RegionalFeature,.045)),closed=['eyeL','eyeR'].filter(k=>down(k as RegionalFeature,.045));
   if(opened.length){row.pattern='open-'+opened.join('-');row.label=opened.length===2?'Ojos más abiertos':'Un ojo más abierto';row.votes.surprise=opened.length===2?.5:.25;evidence('Apertura de párpados',opened as Evidence['features'],opened.flatMap(k=>k==='eyeL'?[362,386,374,263]:[33,159,145,133]));}
   else if(closed.length){row.pattern='closed-'+closed.join('-');row.label=closed.length===2?'Párpados más cerrados':'Parpadeo o asimetría';}
  }else{
   if(pair('browHeightL','browHeightR','down',.014)&&pair('innerSlopeL','innerSlopeR','down',.020)){row.pattern='furrow';row.label='Frunce · enojo o concentración posibles';row.votes.anger=1;evidence('Cejas descendidas y fruncidas',['browHeightL','browHeightR','innerSlopeL','innerSlopeR'],[70,105,107,336,334,300]);}
   else if(pair('browHeightL','browHeightR','up',.025)){row.pattern='raised';row.label='Cejas elevadas';row.votes.surprise=.5;evidence('Ambas cejas elevadas',['browHeightL','browHeightR'],[105,334,33,263]);}
   else if(up('browHeightL',.025)||up('browHeightR',.025)){row.pattern='one-up';row.label=up('browHeightL',.025)?'Ceja izquierda elevada':'Ceja derecha elevada';}
   else if(down('browHeightL',.014)||down('browHeightR',.014)){row.pattern='lower';row.label='Una o ambas cejas más bajas';}
  }
  const curveKeys:RegionalFeature[]=id==='mouth'?['mouthBend','mouthTurn']:id==='eyes'?['eyeLBend','eyeLTurn','eyeRBend','eyeRTurn']:['browLBend','browLTurn','browRBend','browRTurn'];
  if(row.pattern==='rest'&&curveKeys.some(k=>up(k,k.endsWith('Turn')?.10:.012)||down(k,k.endsWith('Turn')?.10:.012))){row.pattern='curve';row.label='Cambio de curvatura local';}
  return row;
 });
 return compose(regions,values,delta,ready);
}
/** Independent persistence, bounded transition grace; missing data clears that region immediately. */
export class RegionalTracker{
 private last=0;private state=new Map<RegionId,{candidate:string;since:number;frames:number;stable:RegionReading|null;pendingSince:number|null}>();
 reset(){this.last=0;this.state.clear();}
 update(reading:RegionalReading,time:number){
  if(!reading.referenceReady||!reading.values){this.reset();return reading;}
  if(time<=this.last||time-this.last>500)this.reset();this.last=time;
  const regions=reading.regions.map(row=>{
   if(row.coverage==='none'){this.state.delete(row.id);return row;}
   let s=this.state.get(row.id);if(!s){s={candidate:row.pattern,since:time,frames:0,stable:null,pendingSince:time};this.state.set(row.id,s);}
   if(s.candidate!==row.pattern){s.candidate=row.pattern;s.since=time;s.frames=0;s.pendingSince??=time;}
   if(s.stable?.evidence.some(e=>e.features.some(k=>!finite(reading.delta?.[k]))))s.stable=null;
   s.frames++;
   if(s.frames>=2&&time-s.since>=250){s.stable=row;s.pendingSince=null;return row;}
   if(s.stable?.pattern===row.pattern){s.pendingSince=null;return row;}
   const previous=s.stable&&time-(s.pendingSince??time)<=350?s.stable:null;
   return {...row,pending:true,votes:previous?.votes||{},evidence:previous?.evidence||[]};
  });
  return compose(regions,reading.values,reading.delta,reading.referenceReady);
 }
}
