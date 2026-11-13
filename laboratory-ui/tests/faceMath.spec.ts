import {test,expect} from '@playwright/test';
import {measure,bulge,inwardBend,calibrate,changes,FEATURES} from '../src/face/geometry';
import {example} from '../src/face/examples';
import {voicesFor} from '../src/face/sound';
import {csv,validateSession,PROTOCOL,V5_PROTOCOL,V4_PROTOCOL,V2_PROTOCOL,V3_PROTOCOL,LEGACY_PROTOCOL} from '../src/face/research';
const baseline=()=>calibrate(Array.from({length:20},(_,i)=>({time:i*100,values:(measure(example(),800,800) as any).values})),'bridge');
test('similarity transforms preserve ratios and relative bend in the image plane',()=>{
 const original=measure(example('smile'),800,800);expect(original.ok).toBe(true);if(!original.ok)return;
 for(const angle of [-.6,.2,.7]){
  const a=.9,c=Math.cos(angle),s=Math.sin(angle);const mesh=example('smile').map(p=>({x:.5+a*((p.x-.5)*c-(p.y-.5)*s)+.04,y:.5+a*((p.x-.5)*s+(p.y-.5)*c)-.03,z:0}));
  const transformed=measure(mesh,800,800);expect(transformed.ok).toBe(true);if(transformed.ok)for(const k of FEATURES)expect(transformed.values[k]).toBeCloseTo(original.values[k],7);
 }
});
test('aspect correction gives the same geometry for equivalent pixel positions',()=>{
 const square=measure(example('wide'),800,800),portrait=measure(example('wide').map(p=>({...p,y:p.y/2})),800,1600);
 expect(square.ok&&portrait.ok).toBe(true);if(square.ok&&portrait.ok)for(const k of FEATURES)expect(square.values[k]).toBeCloseTo(portrait.values[k],8);
});
test('unilateral brow movement changes its own side and asymmetry',()=>{
 const b=baseline(),m=measure(example('one'),800,800);expect(m.ok).toBe(true);if(m.ok){const d=changes(m.values,b);expect(d.browL).toBeGreaterThan(.08);expect(Math.abs(d.browR)).toBeLessThan(1e-8);expect(d.asymmetry).toBeGreaterThan(.08);}
});
test('curvature has a documented directed sign while inward bend is order invariant',()=>{
 const a={x:-1,y:0},b={x:0,y:-.2},c={x:1,y:0},center={x:0,y:-1};expect(bulge(a,b,c)).toBeCloseTo(-.2);expect(bulge(c,b,a)).toBeCloseTo(.2);expect(inwardBend(a,b,c,center)).toBeCloseTo(.2);expect(inwardBend(c,b,a,center)).toBeCloseTo(.2);
});
test('missing and degenerate geometry is invalid rather than zero movement',()=>{
 const mesh=example();mesh[13]={x:NaN,y:.5};expect(measure(mesh,800,800).ok).toBe(false);expect(measure([],800,800).ok).toBe(false);expect(measure(example(),0,800).ok).toBe(false);expect(measure(example().map(()=>({x:.5,y:.5})),800,800).ok).toBe(false);
});
test('substantial out-of-plane rotation is rejected',()=>{
 const mesh=example();mesh[33].z=-.3;mesh[263].z=.3;expect(measure(mesh,800,800)).toMatchObject({ok:false,reason:'Mirá un poco más de frente'});
});
test('reference requires enough contiguous duration and rejects movement',()=>{
 const values=(measure(example(),800,800) as any).values;
 expect(()=>calibrate([{time:0,values}],'bridge')).toThrow();
 expect(()=>calibrate(Array.from({length:20},(_,i)=>({time:i*100+(i>10?900:0),values})),'bridge')).toThrow();
 expect(()=>calibrate(Array.from({length:20},(_,i)=>({time:i*100,values:{...values,browL:i%2?.2:0}})),'bridge')).toThrow();
 expect(baseline().noise.browL).toBe(0);
});
test('personal reference yields zero change, not an emotion label',()=>{
 const b=baseline(),d=changes(b.values,b);for(const k of FEATURES)expect(d[k]).toBe(0);expect(Object.keys(d)).toEqual([...FEATURES]);
});
test('sound is a finite bounded six-voice map for all example changes',()=>{
 const b=baseline();for(const id of ['rest','smile','wide','contract','open','one']){const m=measure(example(id),800,800);expect(m.ok).toBe(true);if(!m.ok)continue;for(const sensitivity of [.25,1,3]){const voices=voicesFor(changes(m.values,b),sensitivity,220);expect(voices).toHaveLength(6);for(const v of voices){expect(Number.isFinite(v.frequency_hz)).toBe(true);expect(v.frequency_hz).toBeGreaterThanOrEqual(55);expect(v.frequency_hz).toBeLessThanOrEqual(1600);expect(v.gain).toBeGreaterThan(0);expect(v.gain).toBeLessThanOrEqual(.205);}}}
});
test('CSV preserves missing/zero and escapes spreadsheet formulas in free text',()=>{
 const b=baseline(),trial:any={id:'a',origin:'synthetic',task:'one',center:'bridge',samples:[{timeMs:0,values:b.values,delta:changes(b.values,b)}],reflection:{felt:'=HYPERLINK("x")',perceived:'',tension:0,pleasantness:null}};
 const output=csv([trial]);expect(output).toContain("'=HYPERLINK");expect(output).toContain('"0"');expect(output).toContain('""');
});
test('import rejects repeated identities, bad deltas and malformed numeric responses',()=>{
 const b=baseline(),trial:any={id:'a',origin:'synthetic',task:'one',center:'bridge',baseline:b,durationMs:10000,complete:true,endReason:null,soundEnabled:false,audioEvents:[],sensitivity:1,fundamental:110,volume:.25,samples:[{timeMs:0,values:b.values,delta:changes(b.values,b)}],reflection:{felt:'',perceived:'',tension:null,pleasantness:0}};
 trial.mapping={id:'contour',richness:1,detune:.8};const session:any={schema:'face-mirror-session/v7',protocol:PROTOCOL,trials:[trial]};expect(validateSession(session)).toHaveLength(1);expect(validateSession({...session,schema:'face-mirror-session/v5',protocol:V5_PROTOCOL})).toHaveLength(1);expect(validateSession({...session,schema:'face-mirror-session/v4',protocol:V4_PROTOCOL})).toHaveLength(1);expect(validateSession({...session,schema:'face-mirror-session/v3',protocol:V3_PROTOCOL})).toHaveLength(1);expect(validateSession({...session,schema:'face-mirror-session/v2',protocol:V2_PROTOCOL})).toHaveLength(1);expect(validateSession({...session,schema:'face-mirror-session/v1',protocol:LEGACY_PROTOCOL,trials:[{...trial,mapping:undefined}]} )[0].mapping?.id).toBe('legacy');expect(()=>validateSession({...session,trials:[trial,trial]})).toThrow();
 expect(()=>validateSession({...session,trials:[{...trial,samples:[{...trial.samples[0],delta:{...trial.samples[0].delta,mouth:20}}]}]})).toThrow();
 expect(()=>validateSession({...session,trials:[{...trial,reflection:{...trial.reflection,tension:101}}]})).toThrow();
});
