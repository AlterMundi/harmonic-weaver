import {expect} from '@playwright/test';
import {execFileSync} from 'node:child_process';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';

export async function setupRecording(page:any,{camera=true,existing=false,loseStart=false,loseExport=false,failExport=false,cancelPicker=false,loseCopy=false}={}) {
 const root=resolve(process.cwd(),'..');
 const fixture=JSON.parse(execFileSync(resolve(root,'.venv/bin/python'),['-c','import json;from harmonic_weaver.lab.contracts import Preset;p=Preset();print(json.dumps({"preset":p.model_dump(),"schemas":{"Preset":Preset.model_json_schema()}}))'],{encoding:'utf8'}));
 const state:any={preset:fixture.preset,session:{desired_revision:8,person_id:'one',playing:true,status:'playing'},source:camera?{kind:'camera',camera:{status:'ready',stream_id:'synthetic'}}:{kind:null},runtime:{},voice_frame:{voices:[]},shaper:{}};
 const take:any={id:'take-one',status:'recording',settings:{record_camera:true},camera:{written_frames:10}};
 const inventory:any={current:{status:'idle'},jobs:[]};let exportState:any={status:'idle'};const exports:any[]=[];
 const preferences:any={schema_version:1,max_seconds:300,include_audio:true,skeleton_overlay:true,harmonic_figure:false,format:'mp4',destination_id:null};
 const destinations:any[]=[],deliveries:any[]=[];const provider:any={account:'studio@example.test',account_available:false,connect_available:true};
 const calls:any[]=[],errors:string[]=[];
 const mediaHash=createHash('sha256').update(process.env.LAB_CAPTURE_PREVIEW?readFileSync(process.env.LAB_CAPTURE_PREVIEW):Buffer.from('synthetic media')).digest('hex');
 const saved=()=>{exportState.status='complete';Object.assign(exports[0],{status:'complete',skeleton_overlay:{enabled:true,frames:10},preview:{status:'complete',sha256:mediaHash},output:{sha256:mediaHash}});};
 if(existing){take.status='complete';inventory.current=take;inventory.jobs.push(take);exports.push({id:'export-one',capture_id:take.id});saved();}
 await page.routeWebSocket('**/ws',(ws:any)=>{const send=()=>ws.send(JSON.stringify(state));send();const timer=setInterval(send,100);ws.onClose(()=>clearInterval(timer));});
 await page.route('**/api/**',async(route:any)=>{
  const req=route.request(),path=new URL(req.url()).pathname;
  if(req.method()!=='GET'){
   calls.push({path,body:req.postDataJSON()});
   if(path==='/api/recording-preferences'){Object.assign(preferences,req.postDataJSON());return route.fulfill({json:preferences});}
   if(path==='/api/recording-drive/connect')return route.fulfill({json:{status:'opened'}});
   if(path==='/api/recording-destinations/pick'){
    if(cancelPicker)return route.fulfill({json:{status:'cancelled'}});
    const kind=req.postDataJSON().kind,row={id:kind+'-chosen',kind,label:kind==='drive'?'Estudio en Drive':'Mis tomas',uri:kind==='drive'?'google-drive://studio@example.test/folder':'file:///synthetic/chosen',account:kind==='drive'?provider.account:null};destinations.push(row);return route.fulfill({json:{status:'selected',destination:row}});
   }
   if(path==='/api/capture-exports/export-one/save'){
    const body=req.postDataJSON(),job={id:'delivery-one',export_id:'export-one',status:'copying',destination:destinations.find(d=>d.id===body.destination_id),format:body.format};deliveries.push(job);
    if(loseCopy){loseCopy=false;return route.abort();}return route.fulfill({json:job});
   }
   if(path==='/api/recording-deliveries/delivery-one/verify'){deliveries[0].status='verifying';return route.fulfill({json:deliveries[0]});}
   if(path==='/api/captures/start'){take.status='recording';inventory.current=take;inventory.jobs=[take];if(loseStart){loseStart=false;return route.abort();}return route.fulfill({json:take});}
   if(path==='/api/captures/stop'){take.status='stopping';return route.fulfill({json:take});}
   if(path==='/api/captures/take-one/export'){
    exportState={id:'export-one',capture_id:take.id,settings:req.postDataJSON(),status:failExport?'failed':'rendering'};exports.unshift(exportState);
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
  const data:any={'/api/recording-preferences':preferences,'/api/recording-destinations':{destinations,provider},'/api/recording-deliveries':deliveries,'/api/state':state,'/api/schemas':fixture.schemas,'/api/captures':inventory,'/api/capture-exports':exportState,'/api/capture-exports/jobs':exports,'/api/media':[],'/api/presets':[],'/api/calibrations':[],'/api/signals':{},'/api/algorithms':[],'/api/environment':{perception:{}},'/api/source-preferences':{}};
  await route.fulfill({json:data[path]??[]});
 });
 page.on('pageerror',(e:any)=>errors.push(String(e)));
 await page.goto('/');await expect(page.getByRole('button',{name:/^Tomas \(/})).toBeVisible();
 return {preferences,destinations,provider,deliveries,finishDelivery:()=>{deliveries[0].status='complete';},state,take,inventory,exports,calls,errors,saved,finish:()=>{take.status='complete';},failImages:()=>{take.camera.written_frames=0;take.status='complete';}};
}
