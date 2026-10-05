import { test, expect } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';

function fixture() {
  const root=resolve(process.cwd(),'..');
  return JSON.parse(execFileSync(resolve(root,'.venv/bin/python'),['-c',
    'import json; from harmonic_weaver.lab.contracts import Preset,Macro,MacroTarget; p=Preset(); p.macros=[Macro(id="intensity",label="Intensidad compartida",value=.7,targets=[MacroTarget(path="master",minimum=0.,maximum=1.)])]; print(json.dumps({"preset":p.model_dump(),"schemas":{"Preset":Preset.model_json_schema()}}))'],{cwd:root,encoding:'utf8'}));
}
async function setup(page:any,calibrations:any[]=[]) {
 const data=fixture(); const writes:any[]=[];
 let preset=data.preset;
 const state:any={preset,session:{session_id:'synthetic',desired_revision:1,person_id:'one',source_id:'synthetic',playing:true,position_s:0,loop:true,status:'playing'},
  source:{kind:'camera',job:null,camera:{status:'running'}},motion_frame:{width:100,height:100,persons:[{person_id:'one',joints:[]},{person_id:'two',joints:[]}]},
  runtime:{can_confirm_person:true,diagnostic:{code:'active',message:'Prueba sintética en marcha',observed_signals:6,pose:{observed:17}}},
  shaper:{telemetry_valid:true,applied_revision:1},voice_frame:{sample_index:0,sample_rate:48000,block_frames:1024,voices:[]},calibration:null};
 const saved=[{...preset,id:'reference',name:'Referencia sintética'}];
 let tick:any;
 await page.routeWebSocket('**/ws',(ws:any)=>{
  const send=()=>{state.session.position_s+=.05;state.voice_frame.sample_index+=2400;ws.send(JSON.stringify(state));};
  send();tick=setInterval(send,50);ws.onClose(()=>clearInterval(tick));
 });
 await page.route('**/api/**',async (route:any)=>{
  const request=route.request();const path=new URL(request.url()).pathname;
  if(request.method()!=='GET') {
   const body=request.postDataJSON();writes.push({path,body});
   if(path==='/api/configuration'){preset=body.preset;state.preset=preset;state.session.desired_revision++;}
   if(path==='/api/person'){state.session.person_id=body.person_id;state.runtime.selection_status='explicit';}
   if(path==='/api/transport'){
    if(body.tracked_prefix!=null)state.session.loop_end_s=body.tracked_prefix ? state.source.job.prefix_s : null;
    if(body.loop!=null){state.session.loop=body.loop;if(!body.loop)state.session.loop_end_s=null;}
   }
   if(path==='/api/calibrate')state.calibration=calibrations.find(c=>c.id===body.reuse_id) || {torso_scale:.2,provenance:'synthetic measurement'};
   if(path==='/api/presets')saved.push(body);
   if(path==='/api/macros/intensity'){state.preset.macros[0].value=body.value;state.preset.master=body.value;state.session.desired_revision++;}
   if(path.endsWith('/apply')){state.preset={...preset,master:.42};state.session.desired_revision++;}
   await route.fulfill({json:state});return;
  }
  const responses:any={ '/api/schemas':data.schemas,'/api/state':state,'/api/presets':saved,'/api/media':[],
   '/api/calibrations':calibrations,'/api/signals':{},'/api/algorithms':[], '/api/environment':{perception:{}},
   '/api/source-preferences':{default_person:'best_coverage',autoplay_video:true},'/api/marks':[]};
  if(path.includes('preview')){await route.fulfill({status:204});return;}
  await route.fulfill({json:responses[path] ?? []});
 });
 const errors:string[]=[];page.on('pageerror',(e:any)=>errors.push(String(e)));
 await page.goto('/');await expect(page.getByRole('button',{name:'Performance',exact:true})).toBeVisible();
 return {writes,state,errors};
}

test('view switch keeps source mounted and makes no changes to sound or transport',async({page})=>{
 const {writes,state,errors}=await setup(page);
 const media=await page.locator('.video-wrap').elementHandle();
 await page.getByRole('button',{name:'Performance',exact:true}).click();
 await expect(page.getByRole('region',{name:'Controles de performance'})).toBeVisible();
 await expect(page.getByRole('button',{name:'Fuente',exact:true})).not.toBeVisible();
 const t=state.session.position_s;await expect.poll(()=>state.session.position_s).toBeGreaterThan(t);
 expect(await page.locator('.video-wrap').evaluate((node,old)=>node===old,media)).toBe(true);
 await page.getByRole('button',{name:'Explorar',exact:true}).click();
 await expect(page.getByRole('button',{name:'Fuente',exact:true})).toBeVisible();
 expect(writes).toEqual([]);expect(errors).toEqual([]);
});

test('performance edits existing controls, keeps ratios, saves and marks explicitly',async({page})=>{
 const {writes,state,errors}=await setup(page);const ratios=state.preset.voices.map((v:any)=>v.ratio);
 await page.getByRole('button',{name:'Performance',exact:true}).click();
 const region=page.getByRole('region',{name:'Controles de performance'});
 await region.getByRole('slider',{name:'Intensidad compartida',exact:true}).fill('0.5');
 await expect.poll(()=>writes.some(w=>w.path==='/api/macros/intensity'&&w.body.value===.5)).toBe(true);
 await region.getByRole('slider',{name:'Intensidad general',exact:true}).fill('0.65');
 await expect.poll(()=>writes.some(w=>w.path==='/api/configuration'&&w.body.preset.master===.65)).toBe(true);
 await region.getByRole('slider',{name:'Realce expresivo',exact:true}).fill('3');
 await expect.poll(()=>state.preset.expression).toBe(3);
 await region.getByRole('slider',{name:'Articulación',exact:true}).fill('0.2');
 await expect.poll(()=>state.preset.transient_mix).toBe(.2);
 await region.getByRole('checkbox').first().check();
 await expect.poll(()=>state.preset.voices[0].muted).toBe(true);
 expect(state.preset.voices.map((v:any)=>v.ratio)).toEqual(ratios);
 await region.getByLabel('Persona en performance').selectOption('two');
 await expect.poll(()=>state.session.person_id).toBe('two');
 await region.getByRole('textbox',{name:'Nombre para guardar'}).fill('Mi configuración');
 await region.getByRole('button',{name:'Guardar configuración actual'}).click();
 await expect.poll(()=>writes.filter(w=>w.path==='/api/presets').length).toBe(1);
 const saved=writes.find(w=>w.path==='/api/presets').body;
 expect(saved.name).toBe('Mi configuración');expect(saved.master).toBe(.65);expect(saved.expression).toBe(3);
 expect(saved).not.toHaveProperty('source_id');expect(saved).not.toHaveProperty('person_id');
 await region.getByRole('button',{name:'Marcar «se siente bien»'}).click();
 await expect.poll(()=>writes.some(w=>w.path==='/api/marks')).toBe(true);
 expect(writes.find(w=>w.path==='/api/marks').body).toEqual({text:'Se siente bien',category:'experience'});
 expect(errors).toEqual([]);
});

test('view persists locally and calibration and audio warnings stay visible',async({page})=>{
 const {state,writes,errors}=await setup(page);
 state.preset.algorithm.id='angular';state.runtime.diagnostic.message='Calibración requerida';
 state.shaper.error='Salida desconectada';
 await page.getByRole('button',{name:'Performance',exact:true}).click();
 await expect(page.getByTestId('model-status')).toHaveText('Calibración requerida');
 await expect(page.getByRole('button',{name:'Calibrar con el cuerpo visible'})).toBeVisible();
 await expect(page.getByRole('alert')).toContainText('Salida desconectada');
 await page.reload();
 await expect(page.getByRole('region',{name:'Controles de performance'})).toBeVisible();
 expect(writes).toEqual([]);expect(errors).toEqual([]);
});

test('performance recovery lists only matching scales and measurement needs selected body support',async({page})=>{
 const calibrations=[
  {id:'matching',source_id:'synthetic',person_id:'one',torso_scale:.2,measured_at:'measured-one'},
  {id:'other-body',source_id:'synthetic',person_id:'two',torso_scale:.4,measured_at:'measured-two'},
  {id:'other-source',source_id:'another',person_id:'one',torso_scale:.3,measured_at:'measured-other'},
 ];
 const {state,writes,errors}=await setup(page,calibrations);
 state.preset.algorithm.id='local';state.runtime.diagnostic.message='Calibración requerida';
 const joints=[5,6,11,12].map(index=>({index,state:'observed',position:[.5,index<11?.2:.7]}));
 state.motion_frame.persons[1].joints=joints;
 await page.getByRole('button',{name:'Performance',exact:true}).click();
 await expect(page.getByRole('button',{name:'Calibrar con el cuerpo visible'})).toBeDisabled();
 await page.getByText('Recuperar escala guardada de esta fuente y persona',{exact:true}).click();
 const recovery=page.getByLabel('Calibración de esta fuente y persona',{exact:true});
 expect(await recovery.locator('option').evaluateAll(options=>options.map(o=>(o as HTMLOptionElement).value))).toEqual(['','matching']);
 expect(writes).toEqual([]);
 await recovery.selectOption('matching');
 await expect.poll(()=>writes.filter(w=>w.path==='/api/calibrate').map(w=>w.body)).toEqual([{reuse_id:'matching'}]);
 await expect(page.getByRole('button',{name:'Calibrar con el cuerpo visible'})).not.toBeVisible();
 state.calibration=null;state.motion_frame.persons[0].joints=joints;
 await expect(page.getByRole('button',{name:'Calibrar con el cuerpo visible'})).toBeEnabled();
 await page.getByRole('button',{name:'Explorar',exact:true}).click();
 await page.getByText('Reutilizar calibración explícitamente',{exact:true}).click();
 const all=page.getByLabel('Calibración guardada',{exact:true});
 expect(await all.locator('optgroup').evaluateAll(groups=>groups.map(g=>(g as HTMLOptGroupElement).label)))
  .toEqual(['Esta fuente y persona','Otra fuente o persona · reutilización explícita']);
 expect(await all.locator('option').evaluateAll(options=>options.map(o=>(o as HTMLOptionElement).value)))
  .toEqual(['','matching','other-body','other-source']);
 await expect(all.locator('option[value="other-body"]')).toContainText('two');
 await expect(all.locator('option[value="other-source"]')).toContainText('another');
 expect(errors).toEqual([]);
});

test('tracked-prefix controls freeze and explicitly expand the loop without changing preset',async({page})=>{
 const {state,writes,errors}=await setup(page);
 state.source.job={id:'synthetic-prefix',status:'building',prefix_s:2,duration_s:60,person_ids:['one']};
 const before=JSON.stringify(state.preset);
 const prefix=page.getByRole('checkbox',{name:'Loop sobre prefijo trackeado'});
 await expect(prefix).toBeVisible();await prefix.click();await expect(prefix).toBeChecked();
 await expect.poll(()=>state.session.loop_end_s).toBe(2);
 await expect(page.getByText('Hasta 2.0 s · límite fijo')).toBeVisible();
 const expand=page.getByRole('button',{name:'Ampliar al prefijo disponible'});
 await expect(expand).toBeDisabled();
 state.source.job.prefix_s=4;
 await expect(expand).toBeEnabled();expect(state.session.loop_end_s).toBe(2);
 await expand.click();await expect.poll(()=>state.session.loop_end_s).toBe(4);
 await page.getByRole('button',{name:'Performance',exact:true}).click();
 await expect(prefix).toBeVisible();
 await prefix.click();await expect(prefix).not.toBeChecked();await expect.poll(()=>state.session.loop_end_s).toBeNull();
 expect(writes.map(w=>w.body)).toEqual([{tracked_prefix:true},{tracked_prefix:true},{tracked_prefix:false}]);
 expect(JSON.stringify(state.preset)).toBe(before);expect(errors).toEqual([]);
});

test('pinning the automatic body sends only its selection and preserves current controls',async({page})=>{
 const {state,writes,errors}=await setup(page);
 state.runtime.can_confirm_person=false;
 state.runtime.selection_status='automatic';state.calibration={torso_scale:.2,provenance:'synthetic measured scale'};
 const before=JSON.stringify(state.preset),scale=state.calibration;
 await page.getByRole('button',{name:'Performance',exact:true}).click();
 await expect(page.getByRole('button',{name:'Fijar esta persona',exact:true})).not.toBeVisible();
 state.runtime.can_confirm_person=true;
 await page.getByRole('button',{name:'Fijar esta persona',exact:true}).click();
 await expect.poll(()=>state.runtime.selection_status).toBe('explicit');
 await expect(page.getByRole('button',{name:'Fijar esta persona',exact:true})).not.toBeVisible();
 expect(writes).toEqual([{path:'/api/person',body:{person_id:'one'}}]);
 expect(JSON.stringify(state.preset)).toBe(before);expect(state.calibration).toBe(scale);expect(errors).toEqual([]);
});
