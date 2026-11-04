/** Discrete projected curve descriptors for research; no AU/emotion classifier. */
export const CURVE_VERSION='projected-curve-profile/0.1';
const cross=(a,b)=>a.x*b.y-a.y*b.x;
const dot=(a,b)=>a.x*b.x+a.y*b.y;
const sub=(a,b)=>({x:a.x-b.x,y:a.y-b.y});
const norm=a=>Math.hypot(a.x,a.y);
const finite=p=>p&&Number.isFinite(p.x)&&Number.isFinite(p.y);

export function bendToward(a,b,c,center){
 if(![a,b,c,center].every(finite))return null;
 const chord=sub(c,a),length=norm(chord);
 if(length<1e-9)return null;
 const side=cross(chord,sub(center,a));
 return Math.abs(side)<1e-12?null:cross(chord,sub(b,a))/length*Math.sign(side);
}

/** Inputs are ordered samples in a common frame, preferably eye-span normalized. */
export function curveProfile(points,center=null,{turnTolerance=1e-3}={}){
 if(!Array.isArray(points)||points.length<3||!points.every(finite)||center!==null&&!finite(center)||!Number.isFinite(turnTolerance)||turnTolerance<0||turnTolerance>=Math.PI)return {ok:false,reason:'Invalid curve, center or tolerance'};
 const edges=points.slice(1).map((p,i)=>norm(sub(p,points[i])));
 if(edges.some(d=>d<1e-9||!Number.isFinite(d)))return {ok:false,reason:'Repeated or invalid adjacent sample'};
 const samples=[];let totalAbsoluteTurn=0,totalWeight=0,weightedMagnitude=0,weightedCenter=0,centerWeight=0,previousSign=0,inflections=0;
 for(let i=1;i<points.length-1;i++){
  const q=points[i],u=sub(points[i-1],q),v=sub(points[i+1],q);
  if(norm(sub(points[i+1],points[i-1]))<1e-9)return {ok:false,reason:'Folded/repeated triple'};
  // Circumcenter relative to q: (A,B)/(2 det). K=(O-q)/|O-q|^2.
  // This algebra also yields exactly zero K for distinct collinear samples.
  const uu=dot(u,u),vv=dot(v,v),det=cross(u,v),A=uu*v.y-vv*u.y,B=u.x*vv-v.x*uu,den=A*A+B*B;
  if(!(den>0)||!Number.isFinite(den))return {ok:false,reason:'Ill-conditioned triple'};
  const curvatureVector={x:2*det*A/den,y:2*det*B/den},magnitude=norm(curvatureVector);
  const incoming={x:-u.x,y:-u.y},turn=Math.atan2(cross(incoming,v),dot(incoming,v));
  const signedCurvature=2*cross(incoming,v)/(norm(u)*norm(v)*norm(sub(points[i+1],points[i-1])));
  const weight=(edges[i-1]+edges[i])/2;
  let centerProjection=null;
  if(center){const radial=sub(center,q),distance=norm(radial);if(distance>1e-9)centerProjection=dot(curvatureVector,radial)/distance;}
  if(![magnitude,turn,signedCurvature,weight].every(Number.isFinite)||centerProjection!==null&&!Number.isFinite(centerProjection))return {ok:false,reason:'Nonfinite derived geometry'};
  totalAbsoluteTurn+=Math.abs(turn);totalWeight+=weight;weightedMagnitude+=weight*magnitude;
  if(centerProjection!==null){weightedCenter+=weight*centerProjection;centerWeight+=weight;}
  const sign=Math.abs(turn)>turnTolerance?Math.sign(turn):0;
  if(sign){if(previousSign&&previousSign!==sign)inflections++;previousSign=sign;}
  samples.push({index:i,point:{x:q.x,y:q.y},curvatureVector,magnitude,signedCurvature,turn,centerProjection,weight});
 }
 const length=edges.reduce((a,b)=>a+b,0),chord=norm(sub(points.at(-1),points[0]));
 return {ok:true,schema:CURVE_VERSION,turnTolerance,length,chord,arcChordRatio:chord>1e-9?length/chord:null,totalAbsoluteTurn,inflections,
  meanCurvature:weightedMagnitude/totalWeight,maxCurvature:Math.max(...samples.map(s=>s.magnitude)),meanCenterProjection:centerWeight?weightedCenter/centerWeight:null,samples};
}

/** Teaching counterexample: same endpoints/midpoint, b changes the local shape. */
export function controlCurve(a=.15,b=0,lift=0,count=65){
 return Array.from({length:count},(_,i)=>{const x=-1+2*i/(count-1);return {x,y:lift+a*(1-x*x)+b*x*(1-x*x)};});
}
