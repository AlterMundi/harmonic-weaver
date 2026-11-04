/** Projected, similarity-normalized facial geometry. No emotion classification. */
import type {ExpressionReference} from './expression';
export type Point = {x:number;y:number;z?:number};
export type Center = 'bridge'|'eyes';
export const GEOMETRY_VERSION='face-geometry/0.1';
export const INDICES={
  browR:[70,63,105,66,107],browL:[336,296,334,293,300],
  eyeR:[33,160,159,158,133,153,145,144],eyeL:[362,385,386,387,263,373,374,380],
  mouth:[61,40,37,0,267,270,291,321,314,17,84,91],
  lip:[61,13,291,14],anchors:[33,263,168,6,152],
} as const;
export const SELECTED=[...new Set(Object.values(INDICES).flat())];
export const FEATURES=['radial','browL','browR','eyeL','eyeR','mouth','mouthCurve','browCurveL','browCurveR','asymmetry'] as const;
export type Feature = typeof FEATURES[number];
export type Values=Record<Feature,number>;
export type Measurement={ok:true;values:Values;points:Record<number,Point>;center:Point;scale:number;yawProxy:number;roll:number}|{ok:false;reason:string};
const distance=(a:Point,b:Point)=>Math.hypot(a.x-b.x,a.y-b.y);
const middle=(a:Point,b:Point):Point=>({x:(a.x+b.x)/2,y:(a.y+b.y)/2});
/** Signed midpoint distance from a fixed ordered chord, in aligned face-width units. */
export function bulge(a:Point,b:Point,c:Point){
 const d=distance(a,c);return d>1e-6?((c.x-a.x)*(b.y-a.y)-(c.y-a.y)*(b.x-a.x))/d:NaN;
}
/** Bend toward the center is positive. Zero means the reference cannot orient the chord. */
export function inwardBend(a:Point,b:Point,c:Point,center:Point){
 const sign=Math.sign(bulge(a,center,c));return sign?bulge(a,b,c)*sign:0;
}
export function measure(mesh:Point[],width:number,height:number,reference:Center='bridge'):Measurement{
 if(!Number.isFinite(width)||!Number.isFinite(height)||width<=0||height<=0)return {ok:false,reason:'Dimensiones inválidas'};
 if(SELECTED.some(i=>!mesh[i]||![mesh[i].x,mesh[i].y,mesh[i].z??0].every(Number.isFinite)))return {ok:false,reason:'Faltan puntos válidos'};
 const pixel=(i:number)=>({x:mesh[i].x*width,y:mesh[i].y*height});
 const a=pixel(33),b=pixel(263),scale=distance(a,b);
 if(scale<width*.08)return {ok:false,reason:'Acercá el rostro a la cámara'};
 const yawProxy=Math.abs((mesh[263].z??0)-(mesh[33].z??0))*width/scale;
 if(yawProxy>.55)return {ok:false,reason:'Mirá un poco más de frente'};
 const x={x:(b.x-a.x)/scale,y:(b.y-a.y)/scale},y={x:-x.y,y:x.x},origin=middle(a,b);
 const normalize=(p:Point):Point=>({x:((p.x-origin.x)*x.x+(p.y-origin.y)*x.y)/scale,y:((p.x-origin.x)*y.x+(p.y-origin.y)*y.y)/scale});
 const points=Object.fromEntries(SELECTED.map(i=>[i,normalize(pixel(i))]));
 const center=reference==='bridge'?points[168]:{x:0,y:0};
 const gap=(upper:number,lower:number,outer:number,inner:number)=>distance(points[upper],points[lower])/distance(points[outer],points[inner]);
 const browL=points[386].y-points[334].y,browR=points[159].y-points[105].y;
 const radial=[105,334,159,386,61,291,13,14,152].reduce((s,i)=>s+distance(points[i],center),0)/9;
 const values:Values={radial,browL,browR,eyeL:gap(386,374,362,263),eyeR:gap(159,145,33,133),mouth:gap(13,14,61,291),
  mouthCurve:inwardBend(points[61],points[13],points[291],center),
  browCurveL:inwardBend(points[336],points[334],points[300],center),browCurveR:inwardBend(points[70],points[105],points[107],center),
  asymmetry:browL-browR};
 if(!FEATURES.every(k=>Number.isFinite(values[k])))return {ok:false,reason:'Geometría degenerada'};
 return {ok:true,values,points,center,scale,yawProxy,roll:Math.atan2(x.y,x.x)};
}
export type Baseline={schema:'face-baseline/v1';center:Center;values:Values;noise:Values;frames:number;durationMs:number;expressionReference?:ExpressionReference};
const median=(v:number[])=>{const a=[...v].sort((a,b)=>a-b);return a.length%2?a[(a.length-1)/2]:(a[a.length/2-1]+a[a.length/2])/2;};
export function calibrate(frames:{time:number;values:Values}[],center:Center):Baseline{
 if(frames.length<10||frames.at(-1)!.time-frames[0].time<1200)throw Error('Necesitamos al menos1,2s y10 lecturas válidas.');
 if(frames.some((f,i)=>!FEATURES.every(k=>Number.isFinite(f.values[k]))||i>0&&(f.time<=frames[i-1].time||f.time-frames[i-1].time>500)))throw Error('La referencia tuvo una interrupción. Volvé a tomarla.');
 const values=Object.fromEntries(FEATURES.map(k=>[k,median(frames.map(f=>f.values[k]))])) as Values;
 const noise=Object.fromEntries(FEATURES.map(k=>[k,median(frames.map(f=>Math.abs(f.values[k]-values[k])))])) as Values;
 if(noise.browL>.012||noise.browR>.012||noise.mouth>.035)throw Error('Hubo demasiado movimiento. Aflojá el gesto y repetí la referencia.');
 return {schema:'face-baseline/v1',center,values,noise,frames:frames.length,durationMs:frames.at(-1)!.time-frames[0].time};
}
export function changes(values:Values,baseline:Baseline):Values{
 return Object.fromEntries(FEATURES.map(k=>[k,values[k]-baseline.values[k]])) as Values;
}
