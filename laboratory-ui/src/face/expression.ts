import type {Measurement} from './geometry';

/** Authored geometric hypotheses, not trained emotion/AU recognition. */
export const EXPRESSION_VERSION='face-expression-rules/0.1';
export const EXPRESSION_FEATURES=['browHeightL','browHeightR','innerSlopeL','innerSlopeR','cornerHeightL','cornerHeightR','cornerLiftL','cornerLiftR','eyeL','eyeR','mouth'] as const;
export type ExpressionFeature=typeof EXPRESSION_FEATURES[number];
export type ExpressionValues=Record<ExpressionFeature,number>;
export type ExpressionReference={schema:'face-expression-reference/v1';values:ExpressionValues;noise:ExpressionValues};
export type Evidence={description:string;features:ExpressionFeature[];points:number[]};
export type ExpressionId='joy'|'surprise'|'anger'|'sadness'|'rest'|'unclear'|'mixed'|'transition'|'unavailable';
export type ExpressionReading={id:ExpressionId;label:string;detail:string;evidence:Evidence[];delta:ExpressionValues|null};

export function expressionValues(m:Measurement):ExpressionValues|null{
 if(!m.ok)return null;
 const p=m.points;
 const result:ExpressionValues={
  browHeightL:-p[334].y,browHeightR:-p[105].y,
  innerSlopeL:p[300].y-p[336].y,innerSlopeR:p[70].y-p[107].y,
  cornerHeightL:-p[291].y,cornerHeightR:-p[61].y,
  cornerLiftL:p[13].y-p[291].y,cornerLiftR:p[13].y-p[61].y,
  eyeL:m.values.eyeL,eyeR:m.values.eyeR,mouth:m.values.mouth,
 };
 return EXPRESSION_FEATURES.every(k=>Number.isFinite(result[k]))?result:null;
}
const median=(v:number[])=>{const a=[...v].sort((a,b)=>a-b),i=Math.floor(a.length/2);return a.length%2?a[i]:(a[i-1]+a[i])/2;};
export function expressionReference(frames:ExpressionValues[]):ExpressionReference{
 if(frames.length<10||frames.some(f=>!EXPRESSION_FEATURES.every(k=>Number.isFinite(f[k]))))throw Error('Faltan lecturas para la referencia de expresión.');
 const values=Object.fromEntries(EXPRESSION_FEATURES.map(k=>[k,median(frames.map(f=>f[k]))])) as ExpressionValues;
 const noise=Object.fromEntries(EXPRESSION_FEATURES.map(k=>[k,median(frames.map(f=>Math.abs(f[k]-values[k])))])) as ExpressionValues;
 return {schema:'face-expression-reference/v1',values,noise};
}
export function validExpressionReference(r:ExpressionReference){
 return r?.schema==='face-expression-reference/v1'&&EXPRESSION_FEATURES.every(k=>Number.isFinite(r.values?.[k])&&Number.isFinite(r.noise?.[k])&&r.noise[k]>=0);
}
export const unavailable=(detail='Tomá una referencia en reposo para leer la expresión.'):ExpressionReading=>({id:'unavailable',label:'Sin lectura de expresión',detail,evidence:[],delta:null});
const labels={joy:'Alegría posible',surprise:'Sorpresa posible',anger:'Enojo posible',sadness:'Tristeza posible'};

export function suggestExpression(values:ExpressionValues|null,reference?:ExpressionReference):ExpressionReading{
 if(!values)return unavailable('Necesitamos una lectura reciente de un solo rostro de frente.');
 if(!reference||!validExpressionReference(reference))return unavailable();
 const d=Object.fromEntries(EXPRESSION_FEATURES.map(k=>[k,values[k]-reference.values[k]])) as ExpressionValues;
 const threshold=(k:ExpressionFeature,min:number)=>Math.max(min,3*reference.noise[k]);
 const up=(k:ExpressionFeature,min:number)=>d[k]>threshold(k,min);
 const down=(k:ExpressionFeature,min:number)=>-d[k]>threshold(k,min);
 const both=(a:ExpressionFeature,b:ExpressionFeature,sign:'up'|'down',min:number)=>[a,b].every(k=>sign==='up'?up(k,min):down(k,min));
 const candidates:{id:keyof typeof labels;detail:string;evidence:Evidence[]}[]=[];
 const cornersUp=both('cornerHeightL','cornerHeightR','up',.015)&&both('cornerLiftL','cornerLiftR','up',.018);
 const browsUp=both('browHeightL','browHeightR','up',.025);
 const browsDown=both('browHeightL','browHeightR','down',.014);
 if(cornersUp)candidates.push({id:'joy',detail:'Las dos comisuras suben y se curvan respecto del labio superior. Puede leerse como una sonrisa; no determina lo que sentís.',evidence:[{description:'Comisuras hacia arriba',features:['cornerHeightL','cornerHeightR','cornerLiftL','cornerLiftR'],points:[61,13,291]}]});
 if(browsUp&&both('eyeL','eyeR','up',.045)&&up('mouth',.10))candidates.push({id:'surprise',detail:'Suben ambas cejas y se abren ojos y boca. Es compatible con una expresión de sorpresa; también puede ser un gesto voluntario.',evidence:[{description:'Ambas cejas elevadas',features:['browHeightL','browHeightR'],points:[105,334,33,263]},{description:'Ojos y boca abiertos',features:['eyeL','eyeR','mouth'],points:[159,145,386,374,13,14]}]});
 if(browsDown&&both('innerSlopeL','innerSlopeR','down',.020))candidates.push({id:'anger',detail:'Bajan ambas cejas y sus extremos internos. Puede sugerir enojo o concentración; el contexto hace la diferencia.',evidence:[{description:'Cejas descendidas y fruncidas',features:['browHeightL','browHeightR','innerSlopeL','innerSlopeR'],points:[70,105,107,336,334,300]}]});
 if(both('cornerHeightL','cornerHeightR','down',.015)&&both('cornerLiftL','cornerLiftR','down',.018))candidates.push({id:'sadness',detail:'Descienden ambas comisuras respecto de tu referencia. Puede sugerir tristeza; la misma forma admite otras lecturas.',evidence:[{description:'Comisuras hacia abajo',features:['cornerHeightL','cornerHeightR','cornerLiftL','cornerLiftR'],points:[61,13,291]}]});
 if(candidates.length>1)return {id:'mixed',label:'Gesto mixto',detail:candidates.map(c=>labels[c.id]).join(' + ')+'. No elegimos una sola emoción.',evidence:candidates.flatMap(c=>c.evidence),delta:d};
 if(candidates.length===1){const c=candidates[0];return {...c,label:labels[c.id],delta:d};}
 const minima:ExpressionValues={browHeightL:.025,browHeightR:.025,innerSlopeL:.020,innerSlopeR:.020,cornerHeightL:.015,cornerHeightR:.015,cornerLiftL:.018,cornerLiftR:.018,eyeL:.045,eyeR:.045,mouth:.10};
 if(EXPRESSION_FEATURES.every(k=>Math.abs(d[k])<=threshold(k,minima[k])))return {id:'rest',label:'Sin cambio marcado',detail:'Cerca de tu referencia. No equivale a calma ni ausencia de emoción.',evidence:[],delta:d};
 return {id:'unclear',label:'Sin una sugerencia clara',detail:'El movimiento no coincide con uno de los cuatro patrones de esta prueba. No forzamos una emoción.',evidence:[],delta:d};
}

/** Require sustained evidence; never retain an emotion across missing/stale frames. */
export class ExpressionStabilizer{
 private id:ExpressionId|null=null;private since=0;private last=0;private frames=0;
 reset(){this.id=null;this.since=0;this.last=0;this.frames=0;}
 update(reading:ExpressionReading,time:number):ExpressionReading{
  if(reading.id==='unavailable'){this.reset();return reading;}
  if(reading.id!==this.id||time<=this.last||time-this.last>350){this.id=reading.id;this.since=time;this.frames=0;}
  this.last=time;this.frames++;
  if(this.frames<3||time-this.since<500)return {id:'transition',label:'Observando el gesto…',detail:'Sostené suavemente el gesto un momento.',evidence:[],delta:reading.delta};
  return reading;
 }
}
