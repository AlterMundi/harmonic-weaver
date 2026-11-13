import {test,expect} from '@playwright/test';
import {projectFace,measure,calibrate,changes} from '../src/face/geometry';
import {example} from '../src/face/examples';
import {regionalValues,regionalReference,readRegions,REGIONAL_FEATURES} from '../src/face/regions';
import {expressionAxis,expressionVoices,DEFAULT_EXPRESSION_SOUND as config} from '../src/face/expressionSound';
import {DEFAULT_MAPPING,contourVoices,validMapping} from '../src/face/contourSound';
import {documentFor,validateSession,csv,V6_PROTOCOL} from '../src/face/research';
const values=(id='rest',amount=1)=>regionalValues(projectFace(example(id,amount),800,800,'eyes','head-aligned'))!;
const reference=()=>regionalReference(Array.from({length:20},()=>values()));
const axis=(id='rest',amount=1,c=config)=>{const ref=reference();return expressionAxis(readRegions(values(id,amount),ref).delta,ref,c)!;};

test('joy converges on f0 and anger on H11, while rest/sadness/surprise stay intermediate',()=>{
 expect(axis('wide')).toEqual({joy:1,anger:0,ratio:1});expect(axis('contract')).toEqual({joy:0,anger:1,ratio:11});
 for(const id of ['rest','down','eyes-brows','mouth-open'])expect(axis(id).ratio).toBe(6);
 const voices=expressionVoices(axis('contract'));expect(voices[0].frequency_hz).toBe(40.4);expect(voices[1].frequency_hz).toBeCloseTo(444.4,10);
 const joy=expressionVoices(axis('wide'));expect(joy[0].gain).toBe(.22);expect(joy[1].gain).toBe(0);
});
test('continuous strength, depth and reversible destinations change position without hard label switches',()=>{
 for(const id of ['wide','contract']){let previous=6;for(const amount of [0,.1,.3,.5,.7,1]){const a=axis(id,amount);if(id==='wide')expect(a.ratio).toBeLessThanOrEqual(previous);else expect(a.ratio).toBeGreaterThanOrEqual(previous);previous=a.ratio;}}
 expect(axis('wide',1,{...config,depth:0}).ratio).toBe(6);expect(axis('contract',1,{...config,angerH:7}).ratio).toBe(7);
 expect(axis('wide',1,{...config,joyH:11,angerH:1}).ratio).toBe(11);expect(axis('rest',1,{...config,angerH:12,motion:'steps'}).ratio).toBe(7);
});
test('mixed cues combine, missing cues remain null, noise floors do not manufacture intensity',()=>{
 expect(axis('mixed')).toEqual({joy:1,anger:1,ratio:6});const ref=reference(),d=readRegions(values('wide'),ref).delta!;
 expect(expressionAxis({...d,browHeightL:null},ref)).toEqual({joy:1,anger:null,ratio:1});
 expect(expressionAxis(Object.fromEntries(REGIONAL_FEATURES.map(k=>[k,null])) as typeof d,ref)).toBeNull();
 const noisy={...ref,noise:Object.fromEntries(REGIONAL_FEATURES.map(k=>[k,1])) as typeof ref.noise};expect(expressionAxis(d,noisy)?.joy).toBe(0);
 expect(expressionAxis(null,ref)).toBeNull();expect(expressionAxis(d,undefined)).toBeNull();expect(expressionVoices(null)).toEqual([]);
});
test('amplitude is bounded and malformed settings cannot silently fall back to contour sound',()=>{
 for(const ratio of [1,1.01,1.5,6,11,16])for(const f0 of [40.4,110,220]){const v=expressionVoices({joy:0,anger:1,ratio},f0);expect(v.reduce((s,n)=>s+n.gain,0)).toBeCloseTo(.22,10);expect(v.every(n=>Number.isFinite(n.frequency_hz)&&n.gain>=0)).toBe(true);}
 for(const c of [{...config,angerH:NaN},{...config,joyH:0},{...config,angerH:17},{...config,depth:2},{...config,motion:'bad'}])expect(validMapping({...DEFAULT_MAPPING,id:'expression',expression:c})).toBe(false);
 expect(validMapping({...DEFAULT_MAPPING,id:'expression'})).toBe(false);expect(expressionVoices({joy:0,anger:1,ratio:Infinity})).toEqual([]);
 const m=measure(example(),800,800);if(!m.ok)throw Error();const zero=changes(m.values,calibrate(Array.from({length:20},(_,i)=>({time:i*100,values:m.values})),'eyes'));
 expect(contourVoices(zero).reduce((s,v)=>s+v.gain*v.gain,0)).toBeCloseTo(.22**2,10);expect(contourVoices(zero,1,40.4,{...DEFAULT_MAPPING,id:'expression',expression:config})).toEqual([]);
});
test('v7 records and validates actual axis settings/drive; v6 stays historical',async()=>{
 const rest=measure(example(),800,800,'eyes','head-aligned'),m=measure(example('contract'),800,800,'eyes','head-aligned');if(!m.ok||!rest.ok)throw Error();
 const baseline=calibrate(Array.from({length:20},(_,i)=>({time:i*100,values:rest.values})),'eyes');baseline.geometryMode='head-aligned';baseline.regionalReference=reference();
 const trial:any={id:'axis',origin:'synthetic',task:'contract',startedAt:new Date().toISOString(),center:'eyes',geometryMode:'head-aligned',baseline,durationMs:1000,complete:true,endReason:null,soundEnabled:true,audioEvents:[],sensitivity:1,fundamental:40.4,volume:.25,mapping:{...DEFAULT_MAPPING,id:'expression',expression:{...config}},samples:[{timeMs:0,values:m.values,delta:changes(m.values,baseline),regionalValues:values('contract'),expressionAxis:axis('contract')}],reflection:{felt:'',perceived:'',tension:null,pleasantness:null}};
 const doc=await documentFor([trial]);expect(doc.schema).toBe('face-mirror-session/v7');expect(validateSession(doc)[0].samples[0].expressionAxis?.ratio).toBe(11);expect(csv([trial])).toContain('axis_frequency_hz');expect(csv([trial])).toContain('444.4');
 for(const a of [undefined,{...axis('contract'),ratio:6},{...axis('contract'),anger:NaN}])expect(()=>validateSession({...doc,trials:[{...trial,samples:[{...trial.samples[0],expressionAxis:a}]}]})).toThrow();
 expect(()=>validateSession({...doc,schema:'face-mirror-session/v6',protocol:V6_PROTOCOL})).toThrow();
 const old={...trial,mapping:{...DEFAULT_MAPPING},samples:[{...trial.samples[0],expressionAxis:undefined}]};const imported=validateSession({...doc,schema:'face-mirror-session/v6',protocol:V6_PROTOCOL,trials:[old]});expect(imported[0].mapping?.id).toBe('contour');expect(validateSession(await documentFor(imported))[0].samples[0].expressionAxis).toBeUndefined();
});
test('browser selects the sibling mode, moves real oscillators, preserves old maps and exports its trial',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await page.addInitScript(()=>{const Original=window.AudioContext;(window as any).__axisOsc=[];(window as any).__axisGain=[];window.AudioContext=class extends Original{createOscillator(){const o=super.createOscillator();(window as any).__axisOsc.push(o);return o;}createGain(){const g=super.createGain();(window as any).__axisGain.push(g);return g;}};});
 await page.goto('./?mode=face');await expect(page.getByLabel('Mapeo de contornos')).toHaveValue('contour');await page.getByRole('button',{name:'Tomar referencia',exact:true}).click();await expect(page.getByRole('button',{name:'Activar sonido',exact:true})).toBeEnabled();
 await page.getByLabel('Mapeo de contornos').selectOption('legacy');await page.getByRole('button',{name:'Emoción · eje expresivo',exact:true}).click();await expect(page.getByLabel('Armónico de alegría')).toHaveValue('1');await expect(page.getByLabel('Armónico de enojo')).toHaveValue('11');
 await page.getByLabel('Gesto del ejemplo').selectOption('contract');await expect(page.locator('[data-expression-ratio]')).toHaveAttribute('data-expression-ratio','11');await page.getByRole('button',{name:'Activar sonido',exact:true}).click();await page.waitForFunction(()=>Math.abs((window as any).__axisOsc[1].frequency.value-444.4)<.1);
 await page.getByLabel('Gesto del ejemplo').selectOption('wide');await expect(page.locator('[data-expression-ratio]')).toHaveAttribute('data-expression-ratio','1');await page.waitForFunction(()=>Math.abs((window as any).__axisOsc[1].frequency.value-40.4)<.1&&(window as any).__axisGain[2].gain.value<.0001);
 await page.getByLabel('Gesto del ejemplo').selectOption('contract');await page.getByLabel('Armónico de enojo').fill('7');await expect(page.locator('[data-expression-ratio]')).toHaveAttribute('data-expression-ratio','7');await page.getByLabel('Armónico de enojo').fill('11');
 await page.getByRole('button',{name:'Contornos actuales',exact:true}).click();await expect(page.getByLabel('Mapeo de contornos')).toHaveValue('legacy');await page.getByRole('button',{name:'Emoción · eje expresivo',exact:true}).click();
 if(process.env.FACE_QA_SCREENS){await page.getByLabel('Configuración del eje expresivo').scrollIntoViewIfNeeded();await page.screenshot({path:process.env.FACE_QA_SCREENS+'/axis-desktop.png',fullPage:true});}
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);if(process.env.FACE_QA_SCREENS)await page.screenshot({path:process.env.FACE_QA_SCREENS+'/axis-narrow.png',fullPage:true});
 await page.getByRole('button',{name:'Investigación',exact:true}).click();await page.getByText('Autorizo conservar medidas y respuestas en esta pestaña para exportarlas.',{exact:true}).click();await page.getByRole('button',{name:'Guardar ensayo de10 segundos',exact:true}).click();await expect(page.getByLabel('Armónico de enojo')).toBeDisabled();await expect(page.getByLabel('Respuesta del eje expresivo')).toHaveCount(0);await expect(page.getByRole('heading',{name:'Ensayo 01'})).toBeVisible({timeout:15000});
 const [download]=await Promise.all([page.waitForEvent('download'),page.getByRole('button',{name:'Exportar sesión JSON',exact:true}).click()]);const stream=await download.createReadStream();let content='';for await(const chunk of stream!)content+=chunk;const doc=JSON.parse(content);expect(validateSession(doc)[0].samples.some(s=>s.expressionAxis?.ratio===11)).toBe(true);expect(doc.trials[0].mapping.expression).toEqual(config);expect(doc.trials[0].soundEnabled).toBe(true);expect(errors).toEqual([]);
});
