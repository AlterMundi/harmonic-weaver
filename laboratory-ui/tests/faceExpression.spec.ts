import {test,expect} from '@playwright/test';
import {measure,calibrate,changes} from '../src/face/geometry';
import {example} from '../src/face/examples';
import {expressionValues,expressionReference,suggestExpression,ExpressionStabilizer,EXPRESSION_VERSION} from '../src/face/expression';
import {documentFor,validateSession,csv,V2_PROTOCOL} from '../src/face/research';

const probes=(id='rest')=>expressionValues(measure(example(id),800,800))!;
const reference=()=>expressionReference(Array.from({length:20},()=>probes()));
test('four authored hypotheses come from geometry and include their supporting points',()=>{
 const r=reference();
 for(const [id,label] of [['wide','joy'],['smile','joy'],['open','surprise'],['contract','anger'],['down','sadness'],['rest','rest'],['one','unclear']]){
  const result=suggestExpression(probes(id),r);expect(result.id,id).toBe(label);
  if(label!=='rest'&&label!=='unclear'){expect(result.evidence.length).toBeGreaterThan(0);expect(result.evidence.flatMap(e=>e.points).length).toBeGreaterThan(2);}
 }
 expect(suggestExpression(probes('smile'),r).evidence[0].points).toEqual([61,13,291]);
});
test('mouth opening, eyelid movement, lower upper lip and one brow do not become smile or anger',()=>{
 const r=reference(),rest=example();
 const variants=[()=>{rest[14].y+=.08;},()=>{rest[159].y-=.03;rest[386].y-=.03;},()=>{rest[13].y+=.035;}];
 for(const change of variants){change();const result=suggestExpression(expressionValues(measure(rest,800,800)),r);expect(['joy','anger','surprise','sadness']).not.toContain(result.id);}
 const one=suggestExpression(probes('one'),r);expect(one.id).toBe('unclear');
});
test('mixed evidence, reference noise, missing/reference-free input and transforms are explicit',()=>{
 const r=reference(),smile=probes('wide'),frown=probes('contract');
 expect(suggestExpression({...smile,browHeightL:frown.browHeightL,browHeightR:frown.browHeightR,innerSlopeL:frown.innerSlopeL,innerSlopeR:frown.innerSlopeR},r).id).toBe('mixed');
 const noisy={...r,noise:Object.fromEntries(Object.keys(r.noise).map(k=>[k,1])) as typeof r.noise};expect(suggestExpression(smile,noisy).id).toBe('rest');
 expect(suggestExpression(smile).id).toBe('unavailable');expect(suggestExpression(null,r).id).toBe('unavailable');
 const transformed=example('wide').map(p=>({x:.5+.8*((p.x-.5)*Math.cos(.3)-(p.y-.5)*Math.sin(.3)),y:.5+.8*((p.x-.5)*Math.sin(.3)+(p.y-.5)*Math.cos(.3)),z:0}));
 expect(suggestExpression(expressionValues(measure(transformed,800,800)),r).id).toBe('joy');
});
test('label requires half a second and resets immediately on loss or an interrupted stream',()=>{
 const f=new ExpressionStabilizer(),r=reference(),joy=suggestExpression(probes('wide'),r);
 expect(f.update(joy,1000).id).toBe('transition');expect(f.update(joy,1250).id).toBe('transition');expect(f.update(joy,1500).id).toBe('joy');
 expect(f.update(suggestExpression(null,r),1550).id).toBe('unavailable');expect(f.update(joy,1600).id).toBe('transition');expect(f.update(joy,2200).id).toBe('transition');
 expect(f.update(suggestExpression(probes('one'),r),2300).id).toBe('transition');
});
test('v3 exports exposure and expression geometry; v2 re-export leaves exposure unknown',async()=>{
 const m=measure(example(),800,800);if(!m.ok)throw Error();const b=calibrate(Array.from({length:20},(_,i)=>({time:i*100,values:m.values})),'eyes');b.expressionReference=reference();
 const trial:any={id:'expr',origin:'synthetic',task:'rest',startedAt:new Date().toISOString(),center:'eyes',baseline:b,durationMs:10000,complete:true,endReason:null,soundEnabled:false,audioEvents:[],sensitivity:1,fundamental:110,volume:.25,mapping:{id:'contour',richness:1,detune:.8},expressionReadout:{version:EXPRESSION_VERSION,enabledBeforeTrial:true,suggestionSeenBeforeTrial:true,labelsDuringTrial:false},samples:[{timeMs:0,values:m.values,delta:changes(m.values,b),expressionValues:probes()}],reflection:{felt:'',perceived:'',tension:null,pleasantness:null}};
 const doc=await documentFor([trial]);expect(doc.schema).toBe('face-mirror-session/v3');expect(validateSession(doc)[0].expressionReadout?.suggestionSeenBeforeTrial).toBe(true);expect(csv([trial])).toContain('suggestion_seen_before_trial');
 expect(()=>validateSession({...doc,trials:[{...trial,expressionReadout:{...trial.expressionReadout,labelsDuringTrial:true}}]})).toThrow();
 expect(()=>validateSession({...doc,trials:[{...trial,samples:[{...trial.samples[0],expressionValues:{...probes(),mouth:NaN}}]}]})).toThrow();
 const {expressionReadout,...old}=trial;delete old.baseline.expressionReference;old.samples=[{timeMs:0,values:m.values,delta:changes(m.values,b)}];
 const imported=validateSession({schema:'face-mirror-session/v2',protocol:V2_PROTOCOL,trials:[old]});expect(imported[0].expressionReadout).toBeUndefined();expect(validateSession(await documentFor(imported))[0].expressionReadout).toBeUndefined();
});
test('visible suggestion follows example points, can be hidden and survives fullscreen responsively',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(String(e)));await page.goto('./?mode=face');
 const panel=page.getByRole('region',{name:'Identificador de expresión'});await expect(panel.getByText('Sin lectura de expresión',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Tomar referencia',exact:true}).click();await expect(page.getByRole('button',{name:'Activar sonido',exact:true})).toBeEnabled();
 await page.getByLabel('Gesto del ejemplo').selectOption('wide');await expect(panel.getByRole('heading',{name:'Alegría posible',exact:true})).toBeVisible();await expect(page.locator('[data-expression-point]')).toHaveCount(3);
 await page.getByRole('button',{name:'Ampliar espejo',exact:true}).click();await expect(page.locator('.face-expression-badge')).toContainText('Alegría posible');await page.keyboard.press('Escape');
 await panel.getByText('Ver puntos y medidas',{exact:true}).click();await expect(panel.getByText('Puntos 61 · 13 · 291',{exact:true})).toBeVisible();await panel.scrollIntoViewIfNeeded();
 if(process.env.FACE_QA_SCREENS)await page.screenshot({path:process.env.FACE_QA_SCREENS+'/expression-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await panel.scrollIntoViewIfNeeded();
 if(process.env.FACE_QA_SCREENS)await page.screenshot({path:process.env.FACE_QA_SCREENS+'/expression-narrow.png',fullPage:true});
 await page.getByLabel('Mostrar lectura orientativa').uncheck();await expect(page.locator('.face-expression-badge')).toHaveCount(0);await expect(page.locator('[data-expression-point]')).toHaveCount(0);expect(errors).toEqual([]);
});
test('trial hides suggestions throughout and afterward; actual exposure is exported',async({page})=>{
 await page.goto('./?mode=face');await page.getByRole('button',{name:'Tomar referencia',exact:true}).click();await expect(page.getByRole('button',{name:'Activar sonido',exact:true})).toBeEnabled();
 await page.getByLabel('Gesto del ejemplo').selectOption('wide');await expect(page.locator('.face-expression-label')).toHaveText('Alegría posible');
 await page.getByRole('button',{name:'Investigación',exact:true}).click();await page.getByText('Autorizo conservar medidas y respuestas en esta pestaña para exportarlas.',{exact:true}).click();await page.getByRole('button',{name:'Guardar ensayo de10 segundos',exact:true}).click();
 await expect(page.getByLabel('Mostrar lectura orientativa')).not.toBeChecked();await expect(page.getByLabel('Mostrar lectura orientativa')).toBeDisabled();await expect(page.locator('.face-expression-badge')).toHaveCount(0);await expect(page.locator('[data-expression-point]')).toHaveCount(0);
 await expect(page.getByRole('heading',{name:'Ensayo 01'})).toBeVisible({timeout:15000});await expect(page.getByLabel('¿Qué sentiste al hacer este gesto?')).toBeFocused();
 const [download]=await Promise.all([page.waitForEvent('download'),page.getByRole('button',{name:'Exportar sesión JSON',exact:true}).click()]);const stream=await download.createReadStream();let content='';for await(const chunk of stream!)content+=chunk;
 const d=JSON.parse(content);expect(d.trials[0].expressionReadout).toEqual({version:EXPRESSION_VERSION,enabledBeforeTrial:true,suggestionSeenBeforeTrial:true,labelsDuringTrial:false});expect(d.trials[0].samples[0].expressionValues.cornerLiftL).toBeGreaterThan(0);
 await page.getByRole('button',{name:'Espejo',exact:true}).click();await expect(page.getByLabel('Mostrar lectura orientativa')).not.toBeChecked();await expect(page.locator('.face-expression-badge')).toHaveCount(0);await page.getByLabel('Mostrar lectura orientativa').check();await expect(page.locator('.face-expression-label')).toHaveText('Alegría posible');
});
