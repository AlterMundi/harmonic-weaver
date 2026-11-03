import type {Point} from './geometry';
// Drawn teaching geometry, not a human recording or validated expression prototype.
export const EXAMPLES=[
 {id:'rest',label:'Reposo',instruction:'Dejá descansar la cara y observá la referencia.'},
 {id:'smile',label:'Sonrisa pequeña',instruction:'Mové suavemente las comisuras. Volvé al reposo.'},
 {id:'wide',label:'Sonrisa amplia',instruction:'Ampliá el gesto anterior sin forzarlo.'},
 {id:'contract',label:'Fruncir y soltar',instruction:'Acercá un poco las cejas y después aflojá.'},
 {id:'open',label:'Abrir cejas y ojos',instruction:'Abrí ambas cejas y los ojos; después dejá bajar una ceja.'},
 {id:'one',label:'Una sola ceja',instruction:'Cambiá una ceja manteniendo el resto lo más parecido posible.'},
] as const;
export function example(id:string='rest',amount=1):Point[]{
 const points:Point[]=Array.from({length:478},()=>({x:.5,y:.5,z:0}));
 const put=(i:number,x:number,y:number)=>points[i]={x,y,z:0};
 put(33,.28,.4);put(133,.43,.4);put(362,.57,.4);put(263,.72,.4);put(168,.5,.4);put(6,.5,.48);put(152,.5,.84);
 const smile=id==='smile'?.5*amount:id==='wide'?amount:0;
 const open=id==='open'?amount:0,contract=id==='contract'?amount:0;
 const left=id==='one'?amount:open, right=open;
 [70,63,105,66,107].forEach((n,i)=>put(n,.275+i*.04,.32-Math.sin(i*Math.PI/4)*(.025+open*.012)-right*.045+contract*.025*(i/4)));
 [336,296,334,293,300].forEach((n,i)=>put(n,.565+i*.04,.32-Math.sin(i*Math.PI/4)*(.025+left*.012)-left*.045+contract*.025*(1-i/4)));
 const r=[33,160,159,158,133,153,145,144],l=[362,385,386,387,263,373,374,380];
 const eye=(ids:number[],cx:number)=>ids.forEach((n,i)=>put(n,cx-.075*Math.cos(i*Math.PI/4),.4-(.02+open*.018)*Math.sin(i*Math.PI/4)));
 eye(r,.355);eye(l,.645);
 // Anatomical left-eye contour runs inner to outer, opposite its right counterpart.
 const mouth=[61,40,37,0,267,270,291,321,314,17,84,91];
 mouth.forEach((n,i)=>put(n,.5-(.12+smile*.025)*Math.cos(i*Math.PI/6),.64-(.018+smile*.018)*Math.sin(i*Math.PI/6)-smile*.035*Math.pow(Math.cos(i*Math.PI/6),2)));
 put(13,.5,.627-smile*.008);put(14,.5,.653+smile*.035+open*.07);
 return points;
}
