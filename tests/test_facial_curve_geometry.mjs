import test from 'node:test';
import assert from 'node:assert/strict';
import {curveProfile,controlCurve,bendToward} from '../research/laboratory/facial_curves/geometry.mjs';
const near=(a,b,eps=1e-9)=>assert.ok(Math.abs(a-b)<eps,`${a} != ${b}`);
const valid=(p,c=null)=>{const r=curveProfile(p,c);assert.equal(r.ok,true,r.reason);return r;};

test('circle curvature is 1/R with its geometric vector pointing to the circle center, including unequal sampling',()=>{
 for(const radius of [.3,1,2.7]){
  const p=[-.8,-.51,-.12,0,.03,.44,.7].map(t=>({x:radius*Math.cos(t)+.4,y:radius*Math.sin(t)-.2}));
  for(const s of valid(p).samples){near(s.magnitude,1/radius);near(s.curvatureVector.x,(.4-s.point.x)/(radius*radius));near(s.curvatureVector.y,(-.2-s.point.y)/(radius*radius));}
 }
});
test('a straight line has zero curvature while degenerate/missing geometry stays invalid',()=>{
 const r=valid([{x:-1,y:0},{x:0,y:0},{x:1,y:0}],{x:0,y:1});near(r.meanCurvature,0);near(r.totalAbsoluteTurn,0);near(r.arcChordRatio,1);
 for(const p of [[],[{x:0,y:0},{x:0,y:0},{x:1,y:0}],[{x:0,y:0},{x:1,y:0},{x:0,y:0}],[{x:0,y:0},{x:NaN,y:0},{x:1,y:0}]])assert.equal(curveProfile(p).ok,false);
 assert.equal(curveProfile(controlCurve(),null,{turnTolerance:-1}).ok,false);
 assert.equal(bendToward(undefined,{x:0,y:0},{x:1,y:0},{x:0,y:1}),null);
});
test('moving or omitting the reference center leaves every center-independent descriptor unchanged',()=>{
 const p=controlCurve(.15,.25),a=valid(p,{x:0,y:1}),b=valid(p,{x:0,y:-1}),c=valid(p);
 for(const key of ['meanCurvature','maxCurvature','arcChordRatio','inflections','totalAbsoluteTurn']){near(a[key],b[key]);near(a[key],c[key]);}
 assert.notEqual(a.meanCenterProjection,b.meanCenterProjection);assert.equal(c.meanCenterProjection,null);
 const hit=valid(p,p[32]);assert.equal(hit.samples.find(s=>s.index===32).centerProjection,null);
});
test('reversing sample order changes path sign but preserves the vector, magnitude and center relation',()=>{
 const p=controlCurve(.15,.25),a=valid(p,{x:0,y:1}),b=valid([...p].reverse(),{x:0,y:1});
 near(a.meanCurvature,b.meanCurvature);assert.equal(a.inflections,b.inflections);
 a.samples.forEach((s,i)=>{const t=b.samples[b.samples.length-1-i];near(s.magnitude,t.magnitude);near(s.signedCurvature,-t.signedCurvature);near(s.curvatureVector.x,t.curvatureVector.x);near(s.curvatureVector.y,t.curvatureVector.y);near(s.centerProjection,t.centerProjection);});
});
test('rotation, reflection and scale obey curvature covariance; dimensionless shape survives resizing',()=>{
 const p=controlCurve(.15,.25),c={x:.1,y:1},a=valid(p,c);
 for(const factor of [.6,1.7])for(const mirror of [-1,1]){
  const angle=.5,transform=q=>({x:factor*(mirror*q.x*Math.cos(angle)-q.y*Math.sin(angle))+2,y:factor*(mirror*q.x*Math.sin(angle)+q.y*Math.cos(angle))-3});
  const b=valid(p.map(transform),transform(c));near(b.meanCurvature,a.meanCurvature/factor);near(b.meanCenterProjection,a.meanCenterProjection/factor);near(b.arcChordRatio,a.arcChordRatio);near(b.meanCurvature*b.chord,a.meanCurvature*a.chord);assert.equal(a.inflections,b.inflections);
 }
});
test('equal endpoint/midpoint deflection and equal aperture can conceal different curvature and inflections',()=>{
 const a=controlCurve(.15,0),b=controlCurve(.15,.35),center={x:0,y:1};
 assert.deepEqual(a[0],b[0]);assert.deepEqual(a[32],b[32]);assert.deepEqual(a[64],b[64]);near(bendToward(a[0],a[32],a[64],center),bendToward(b[0],b[32],b[64],center));
 assert.equal(valid(a).inflections,0);assert.ok(valid(b).inflections>=1);assert.ok(Math.abs(valid(a).maxCurvature-valid(b).maxCurvature)>.2);
 const shifted=controlCurve(.15,.35,.3);near(valid(b).meanCurvature,valid(shifted).meanCurvature);near(valid(b).totalAbsoluteTurn,valid(shifted).totalAbsoluteTurn);
});
test('midpoint bulging toward the center and curvature bending toward it are different constructs',()=>{
 const p=controlCurve(.15,0),c={x:0,y:1},r=valid(p,c);assert.ok(bendToward(p[0],p[32],p[64],c)>0);assert.ok(r.samples.find(s=>s.index===32).centerProjection<0);
});
