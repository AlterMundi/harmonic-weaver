import {test,expect} from '@playwright/test';
import {execFileSync} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';

async function setup(page:any,{camera=true,existing=false,loseStart=false,loseExport=false,failExport=false}={}) {
 const root=resolve(process.cwd(),'..');
 const fixture=JSON.parse(execFileSync(resolve(root,'.venv/bin/python'),['-c','import json;from harmonic_weaver.lab.contracts import Preset;p=Preset();print(json.dumps({"preset":p.model_dump(),"schemas":{"Preset":Preset.model_json_schema()}}))'],{encoding:'utf8'}));
 const state:any={preset:fixture.preset,session:{desired_revision:8,person_id:'one',playing:true,status:'playing'},source:camera?{kind:'camera',camera:{status:'ready',stream_id:'synthetic'}}:{kind:null},runtime:{},voice_frame:{voices:[]},shaper:{}};
 const take:any={id:'take-one',status:'recording',settings:{record_camera:true},camera:{written_frames:10}};
 const inventory:any={current:{status:'idle'},jobs:[]};let exportState:any={status:'idle'};const exports:any[]=[];
 const calls:any[]=[],errors:string[]=[];
 const saved=()=>{exportState.status='complete';Object.assign(exports[0],{status:'complete',skeleton_overlay:{enabled:true,frames:10},preview:{status:'complete'}});};
 if(existing){take.status='complete';inventory.current=take;inventory.jobs.push(take);exports.push({id:'export-one',capture_id:take.id});saved();}
 await page.routeWebSocket('**/ws',(ws:any)=>{const send=()=>ws.send(JSON.stringify(state));send();const timer=setInterval(send,100);ws.onClose(()=>clearInterval(timer));});
 await page.route('**/api/**',async(route:any)=>{
  const req=route.request(),path=new URL(req.url()).pathname;
  if(req.method()!=='GET'){
   calls.push({path,body:req.postDataJSON()});
   if(path==='/api/captures/start'){take.status='recording';inventory.current=take;inventory.jobs=[take];if(loseStart){loseStart=false;return route.abort();}return route.fulfill({json:take});}
   if(path==='/api/captures/stop'){take.status='stopping';return route.fulfill({json:take});}
   if(path==='/api/captures/take-one/export'){
    exportState={id:'export-one',capture_id:take.id,status:failExport?'failed':'rendering'};exports.unshift(exportState);
    if(loseExport){loseExport=false;return route.abort();}
    if(failExport){failExport=false;return route.fulfill({status:500,json:{detail:'Synthetic encoder failure'}});}
    return route.fulfill({json:exportState});
   }
   return route.fulfill({json:{}});
  }
  if(path.endsWith('/artifacts/preview.mp4')&&process.env.LAB_CAPTURE_PREVIEW){
   if(process.env.LAB_CAPTURE_MEDIA_HTTP)return route.continue();
   return route.fulfill({contentType:'video/mp4',body:readFileSync(process.env.LAB_CAPTURE_PREVIEW)});
  }
  const data:any={'/api/state':state,'/api/schemas':fixture.schemas,'/api/captures':inventory,'/api/capture-exports':exportState,'/api/capture-exports/jobs':exports,'/api/media':[],'/api/presets':[],'/api/calibrations':[],'/api/signals':{},'/api/algorithms':[],'/api/environment':{perception:{}},'/api/source-preferences':{}};
  await route.fulfill({json:data[path]??[]});
 });
 page.on('pageerror',(e:any)=>errors.push(String(e)));
 await page.goto('/');await expect(page.getByRole('button',{name:/^Tomas \(/})).toBeVisible();
 return {state,take,inventory,exports,calls,errors,saved,finish:()=>{take.status='complete';},failImages:()=>{take.camera.written_frames=0;take.status='complete';}};
}
const mutations=(fx:any,path:string)=>fx.calls.filter((c:any)=>c.path===path);

test('record, confirm close, export overlay with audio and keep the original source/preset',async({page})=>{
 const fx=await setup(page),preset=JSON.stringify(fx.state.preset);
 await page.waitForTimeout(900);expect(fx.calls).toEqual([]);
 const source=await page.locator('.source-view').elementHandle();
 await page.getByRole('button',{name:'Grabar',exact:true}).evaluate(el=>{(el as HTMLButtonElement).click();(el as HTMLButtonElement).click();});
 await expect(page.getByRole('button',{name:'Detener y guardar',exact:true})).toBeEnabled();
 expect(mutations(fx,'/api/captures/start')).toHaveLength(1);
 expect(mutations(fx,'/api/captures/start')[0].body).toMatchObject({record_camera:true,max_seconds:300,timeline_hz:20});
 await page.getByRole('button',{name:'Detener y guardar',exact:true}).click();
 await page.waitForTimeout(900);expect(mutations(fx,'/api/captures/take-one/export')).toHaveLength(0);
 fx.finish();await expect.poll(()=>mutations(fx,'/api/captures/take-one/export').length).toBe(1);
 expect(mutations(fx,'/api/captures/take-one/export')[0].body).toMatchObject({skeleton_overlay:true,browser_preview:true,harmonic_figure:false,width:1280,height:720});
 fx.saved();await page.getByRole('button',{name:/^Tomas \(/}).click();
 await expect(page.getByText('Video listo',{exact:true})).toBeVisible();
 await expect(page.getByRole('link',{name:'Descargar MP4',exact:true})).toHaveAttribute('href','/api/capture-exports/export-one/artifacts/preview.mp4');
 await expect(page.getByRole('link',{name:/Descargar original MKV/})).toHaveAttribute('href','/api/capture-exports/export-one/artifacts/capture.mkv');
 await page.getByRole('button',{name:'Cerrar tomas'}).click();
 expect(await page.locator('.source-view').evaluate((el,old)=>el===old,source)).toBe(true);
 expect(JSON.stringify(fx.state.preset)).toBe(preset);expect(fx.errors).toEqual([]);
});

test('saved takes survive page reload, preview never autoplays and downloads work',async({page})=>{
 const fx=await setup(page,{existing:true});await page.reload();
 await page.getByRole('button',{name:/^Tomas \(/}).click();
 await expect(page.getByText('Video listo',{exact:true})).toBeVisible();expect(fx.calls).toEqual([]);
 await page.getByRole('button',{name:'Ver video',exact:true}).click();
 const video=page.locator('.takes-dialog video');await expect(video).toHaveJSProperty('autoplay',false);
 if(process.env.LAB_CAPTURE_PREVIEW){
  await expect.poll(()=>video.evaluate((v:HTMLVideoElement)=>v.readyState)).toBeGreaterThanOrEqual(1);
  expect(await video.evaluate((v:HTMLVideoElement)=>v.paused)).toBe(true);
  await video.evaluate(async(v:HTMLVideoElement)=>{v.muted=true;await v.play();});
  await expect.poll(()=>video.evaluate((v:HTMLVideoElement)=>v.currentTime)).toBeGreaterThan(.1);
  const downloaded=page.waitForEvent('download');await page.getByRole('link',{name:'Descargar MP4',exact:true}).click();
  expect(await(await downloaded).failure()).toBeNull();
 }
 if(process.env.TUTORIAL_QA_DIR)await page.screenshot({path:process.env.TUTORIAL_QA_DIR+'/takes-desktop.png'});
 await page.getByRole('button',{name:'Cerrar tomas'}).click();await expect(video).toHaveCount(0);
 await expect(page.getByRole('button',{name:/^Tomas \(/})).toBeFocused();expect(fx.errors).toEqual([]);
});

test('missing camera disables recording and the take library fits a narrow screen',async({page})=>{
 await page.setViewportSize({width:390,height:844});const fx=await setup(page,{camera:false});
 await expect(page.getByRole('button',{name:'Grabar',exact:true})).toBeDisabled();
 await page.getByRole('button',{name:/^Tomas \(/}).click();
 const dialog=page.getByRole('dialog');await expect(dialog).toContainText('encendé la cámara');
 expect(await dialog.evaluate(el=>el.scrollWidth<=el.clientWidth+1)).toBe(true);
 if(process.env.TUTORIAL_QA_DIR)await page.screenshot({path:process.env.TUTORIAL_QA_DIR+'/takes-narrow.png'});
 await page.keyboard.press('Escape');await expect(dialog).not.toBeVisible();expect(fx.calls).toEqual([]);
 if(process.env.TUTORIAL_QA_DIR)await page.screenshot({path:process.env.TUTORIAL_QA_DIR+'/recorder-narrow.png'});
});

test('a lost recording acknowledgement is not replayed and confirmed inventory can stop it',async({page})=>{
 const fx=await setup(page,{loseStart:true});await page.getByRole('button',{name:'Grabar',exact:true}).click();
 await expect(page.getByRole('button',{name:'Detener y guardar',exact:true})).toBeEnabled();
 await page.waitForTimeout(900);expect(mutations(fx,'/api/captures/start')).toHaveLength(1);
 await page.getByRole('button',{name:'Detener y guardar',exact:true}).click();fx.finish();
 await expect.poll(()=>mutations(fx,'/api/captures/take-one/export').length).toBe(1);
 expect(mutations(fx,'/api/captures/start')).toHaveLength(1);
});

test('a lost export acknowledgement resolves through inventory without a second export',async({page})=>{
 const fx=await setup(page,{loseExport:true});await page.getByRole('button',{name:'Grabar',exact:true}).click();
 await expect(page.getByRole('button',{name:'Detener y guardar',exact:true})).toBeEnabled();
 await page.getByRole('button',{name:'Detener y guardar',exact:true}).click();fx.finish();
 await expect.poll(()=>mutations(fx,'/api/captures/take-one/export').length).toBe(1);
 await page.waitForTimeout(1700);expect(mutations(fx,'/api/captures/take-one/export')).toHaveLength(1);
 fx.saved();await page.getByRole('button',{name:/^Tomas \(/}).click();await expect(page.getByText('Video listo',{exact:true})).toBeVisible();
});

test('failed preparation retains originals and only a human retry can request another export',async({page})=>{
 const fx=await setup(page,{failExport:true});await page.getByRole('button',{name:'Grabar',exact:true}).click();
 await expect(page.getByRole('button',{name:'Detener y guardar',exact:true})).toBeEnabled();
 await page.getByRole('button',{name:'Detener y guardar',exact:true}).click();fx.finish();
 await expect.poll(()=>mutations(fx,'/api/captures/take-one/export').length).toBe(1);
 await page.waitForTimeout(1600);expect(mutations(fx,'/api/captures/take-one/export')).toHaveLength(1);
 await page.getByRole('button',{name:/^Tomas \(/}).click();await expect(page.getByText('Originales guardados',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Preparar video de esta toma',exact:true}).click();
 await expect.poll(()=>mutations(fx,'/api/captures/take-one/export').length).toBe(2);
});

test('no received camera frames never produce a misleading black saved video',async({page})=>{
 const fx=await setup(page);await page.getByRole('button',{name:'Grabar',exact:true}).click();
 await expect(page.getByRole('button',{name:'Detener y guardar',exact:true})).toBeEnabled();fx.failImages();
 await expect(page.getByRole('alert')).toContainText('no llegaron imágenes');
 await expect(page.getByRole('button',{name:'Grabar',exact:true})).toBeEnabled();
 expect(mutations(fx,'/api/captures/take-one/export')).toHaveLength(0);
});
