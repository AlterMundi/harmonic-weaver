import {test,expect} from '@playwright/test';
import {projectFace,measure,calibrate,changes,INDICES,FEATURES,type Point} from '../src/face/geometry';
import {example} from '../src/face/examples';
import {arcShape,regionalValues,regionalReference,readRegions,RegionalTracker,REGIONAL_VERSION} from '../src/face/regions';
import {expressionValues,expressionReference,suggestExpression} from '../src/face/expression';
import {contourVoices} from '../src/face/contourSound';
import {documentFor,validateSession,csv,V5_PROTOCOL} from '../src/face/research';
const values=(mesh=example())=>regionalValues(projectFace(mesh,800,800,'eyes','head-aligned'))!;
const ref=()=>regionalReference(Array.from({length:20},()=>values()));
const read=(mesh=example(),r=ref())=>readRegions(values(mesh),r);
test('arc deflection and oriented turn preserve reversal/similarity; no fake ear/iris reference',()=>{
 const points=[{x:-1,y:0},{x:0,y:-.3},{x:1,y:0}],center={x:0,y:-1},a=arcShape(points,center)!;expect(a.bend).toBeGreaterThan(0);expect(a.turn).toBeGreaterThan(0);expect(arcShape([...points].reverse(),center)).toEqual(a);
 const f=(p:Point)=>({x:3+2*(p.x*Math.cos(.4)-p.y*Math.sin(.4)),y:-4+2*(p.x*Math.sin(.4)+p.y*Math.cos(.4))});const b=arcShape(points.map(f),f(center))!;expect(b.bend).toBeCloseTo(a.bend,10);expect(b.turn).toBeCloseTo(a.turn,10);
 expect(arcShape([points[0],points[0],points[2]],center)).toBeNull();const rest=values();expect(rest.eyeLBend).not.toBeNull();expect(rest.eyeRBend).not.toBeNull();
 const mesh=example('wide');for(let i=468;i<478;i++)mesh[i]={x:NaN,y:NaN,z:NaN};expect(read(mesh).composite.id).toBe('joy');
});
test('brows and eyes support surprise with a relaxed mouth; mouth opening alone stays local',()=>{
 expect(read(example('eyes-brows')).composite.id).toBe('surprise');
 const m=measure(example('eyes-brows'),800,800);const old=expressionReference(Array.from({length:20},()=>expressionValues(measure(example(),800,800))!));expect(suggestExpression(expressionValues(m),old).id).toBe('unclear');
 const only=read(example('mouth-open'));expect(only.regions[0].label).toBe('Boca abierta');expect(only.composite.id).toBe('unclear');
});
test('independent mouth/brow contributions produce a mixed gesture rather than cancel each other',()=>{
 expect(read(example('wide')).composite.id).toBe('joy');expect(read(example('down')).composite.id).toBe('sadness');expect(read(example('contract')).composite.id).toBe('anger');
 const mixed=read(example('mixed'));expect(mixed.composite.id).toBe('mixed');expect(mixed.composite.detail).toContain('Alegría posible');expect(mixed.composite.detail).toContain('Enojo posible');
 const mesh=example('wide'),one=example('one');for(const i of INDICES.browL)mesh[i]=one[i];expect(read(mesh).composite.id).toBe('joy');expect(read(mesh).regions[2].label).toBe('Ceja izquierda elevada');
});
test('missing regional points do not zero or erase other regions; decorative vertices do not gate sound',()=>{
 const mesh=example('mixed');mesh[13]={x:NaN,y:NaN};const r=read(mesh);expect(r.regions[0].coverage).toBe('partial');expect(r.values!.cornerLiftL).toBeNull();expect(r.composite.id).toBe('anger');expect(measure(mesh,800,800).ok).toBe(false);
 const decorative=example('wide');decorative[37]={x:NaN,y:NaN};const m=measure(decorative,800,800,'eyes','head-aligned');expect(m.ok).toBe(true);expect(read(decorative).values!.mouthBend).toBeNull();expect(read(decorative).composite.id).toBe('joy');if(m.ok){const b=calibrate(Array.from({length:20},(_,i)=>({time:i*100,values:m.values})),'eyes');expect(contourVoices(changes(m.values,b))[0].frequency_hz).toBe(40.4);}
 decorative[33]={x:NaN,y:NaN};expect(read(decorative).composite.id).toBe('unavailable');
});
test('head-relative regional geometry remains invariant under moderate yaw/pitch',()=>{
 const mesh=example('wide'),original=values(mesh);const turn=mesh.map(p=>{const x=p.x-.5,y=p.y-.5,z=p.z||0,xx=x*Math.cos(.6)+z*Math.sin(.6),zz=-x*Math.sin(.6)+z*Math.cos(.6);return {x:xx+.5,y:y*Math.cos(.18)-zz*Math.sin(.18)+.5,z:y*Math.sin(.18)+zz*Math.cos(.18)};});
 const result=values(turn);for(const k of Object.keys(original) as (keyof typeof original)[])if(original[k]!==null)expect(result[k]!).toBeCloseTo(original[k]!,7);expect(read(turn).composite.id).toBe('joy');
});
test('regional persistence is independent, bounded and clears missing contributors immediately',()=>{
 const f=new RegionalTracker(),r=ref();for(const t of [1000,1100,1200,1300])f.update(read(example('wide'),r),t);
 expect(f.update(read(example('wide'),r),1400).composite.id).toBe('joy');const mixed=f.update(read(example('mixed'),r),1500);expect(mixed.composite.id).toBe('joy');expect(mixed.regions[2].pending).toBe(true);
 expect(f.update(read(example('mixed'),r),1800).composite.id).toBe('mixed');const missing=example('mixed');missing[13]={x:NaN,y:NaN};expect(f.update(read(missing,r),1900).composite.id).toBe('anger');
 expect(f.update(readRegions(null,r),2000).composite.id).toBe('unavailable');expect(f.update(read(example('wide'),r),2100).composite.id).toBe('transition');
 const blank={schema:'face-regional-reference/v1' as const,values:Object.fromEntries(Object.keys(r.values).map(k=>[k,null])) as typeof r.values,noise:Object.fromEntries(Object.keys(r.noise).map(k=>[k,null])) as typeof r.noise};expect(readRegions(values(),blank).regions.every(r=>r.coverage==='none')).toBe(true);
});
test('v6 records regional nulls, reference and method; historical v5 does not acquire invented regional data',async()=>{
 const m=measure(example(),800,800);if(!m.ok)throw Error();const baseline=calibrate(Array.from({length:20},(_,i)=>({time:i*100,values:m.values})),'eyes');baseline.regionalReference=ref();
 const v=values(),trial:any={id:'regions',origin:'synthetic',task:'rest',startedAt:new Date().toISOString(),geometryMode:'projected',center:'eyes',baseline,durationMs:1000,complete:true,endReason:null,soundEnabled:false,audioEvents:[],sensitivity:1,fundamental:40.4,volume:.25,mapping:{id:'contour',richness:1,detune:.8},expressionReadout:{version:REGIONAL_VERSION,enabledBeforeTrial:true,suggestionSeenBeforeTrial:false,labelsDuringTrial:false},samples:[{timeMs:0,values:m.values,delta:changes(m.values,baseline),regionalValues:{...v,mouthBend:null,eyeLBend:0}}],reflection:{felt:'',perceived:'',tension:null,pleasantness:null}};
 const d=await documentFor([trial]);expect(d.schema).toBe('face-mirror-session/v6');expect(validateSession(d)[0].samples[0].regionalValues!.mouthBend).toBeNull();expect(csv([trial])).toContain('"region_eyeLBend"');
 expect(()=>validateSession({...d,trials:[{...trial,samples:[{...trial.samples[0],regionalValues:{...v,mouth:NaN}}]}]})).toThrow();
 const old={...trial,expressionReadout:undefined,baseline:{...baseline,regionalReference:undefined},samples:[{...trial.samples[0],regionalValues:undefined}]};const imported=validateSession({...d,schema:'face-mirror-session/v5',protocol:V5_PROTOCOL,trials:[old]});expect(imported[0].baseline.regionalReference).toBeUndefined();expect(validateSession(await documentFor(imported))[0].samples[0].regionalValues).toBeUndefined();
});
test('three regional cards and hidden contours keep the composite visible; narrow/fullscreen and trial hiding',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.goto('./?mode=face');await page.getByRole('button',{name:'Tomar referencia',exact:true}).click();await expect(page.getByRole('button',{name:'Activar sonido',exact:true})).toBeEnabled();await expect(page.locator('[data-face-region]')).toHaveCount(3);
 await page.getByLabel('Gesto del ejemplo').selectOption('eyes-brows');await expect(page.locator('.face-expression-label')).toHaveText('Sorpresa posible');await expect(page.locator('[data-face-region=mouth]>strong')).toHaveText('Cerca del reposo');
 await page.getByText('Ajustar el instrumento · f₀ 40,4 Hz',{exact:true}).click();await page.getByLabel('Mostrar curvas y puntos',{exact:true}).uncheck();await expect(page.locator('.face-contours')).toHaveCount(0);await expect(page.locator('.face-expression-label')).toHaveText('Sorpresa posible');
 await page.getByLabel('Gesto del ejemplo').selectOption('mixed');await expect(page.locator('.face-expression-label')).toHaveText('Gesto mixto');await expect(page.locator('[data-face-region=mouth]>strong')).toHaveText('Sonrisa posible');await expect(page.locator('[data-face-region=brows]>strong')).toContainText('Frunce');
 await page.getByLabel('Mostrar curvas y puntos',{exact:true}).check();
 if(process.env.FACE_QA_SCREENS)await page.screenshot({path:process.env.FACE_QA_SCREENS+'/regions-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await expect(page.locator('.face-region-chips')).toBeHidden();
 if(process.env.FACE_QA_SCREENS)await page.screenshot({path:process.env.FACE_QA_SCREENS+'/regions-narrow.png',fullPage:true});
 await page.getByRole('button',{name:'Ampliar espejo',exact:true}).click();await expect(page.locator('[data-region-chip]')).toHaveCount(3);await expect(page.locator('.face-region-chips')).toBeVisible();await page.keyboard.press('Escape');await page.setViewportSize({width:320,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.getByLabel('Mostrar lectura orientativa').uncheck();await expect(page.locator('[data-face-region]')).toHaveCount(0);await expect(page.locator('[data-region-chip]')).toHaveCount(0);expect(errors).toEqual([]);
});
