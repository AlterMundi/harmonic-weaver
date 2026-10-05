import { test, expect } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';

function fixture() {
  const root=resolve(process.cwd(),'..');
  return JSON.parse(execFileSync(resolve(root,'.venv/bin/python'),['-c',
    'import json; from harmonic_weaver.lab.contracts import Preset,Macro,MacroTarget; p=Preset(); p.macros=[Macro(id="intensity",label="Intensidad compartida",value=.7,targets=[MacroTarget(path="master",minimum=0.,maximum=1.)])]; print(json.dumps({"preset":p.model_dump(),"schemas":{"Preset":Preset.model_json_schema()}}))'],{cwd:root,encoding:'utf8'}));
}
async function setup(page:any) {
 const data=fixture(); const writes:any[]=[];
 let preset=data.preset;
 const state:any={preset,session:{session_id:'synthetic',desired_revision:1,person_id:'one',source_id:'synthetic',playing:true,position_s:0,loop:true,status:'playing'},
  source:{kind:'camera',job:null,camera:{status:'running'}},motion_frame:{width:100,height:100,persons:[{person_id:'one',joints:[]},{person_id:'two',joints:[]}]},
  runtime:{diagnostic:{code:'active',message:'Prueba sintética en marcha',observed_signals:6,pose:{observed:17}}},
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
   if(path==='/api/person')state.session.person_id=body.person_id;
   if(path==='/api/presets')saved.push(body);
   if(path==='/api/macros/intensity'){state.preset.macros[0].value=body.value;state.preset.master=body.value;state.session.desired_revision++;}
   if(path.endsWith('/apply')){state.preset={...preset,master:.42};state.session.desired_revision++;}
   await route.fulfill({json:state});return;
  }
  const responses:any={ '/api/schemas':data.schemas,'/api/state':state,'/api/presets':saved,'/api/media':[],
   '/api/calibrations':[],'/api/signals':{},'/api/algorithms':[], '/api/environment':{perception:{}},
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
