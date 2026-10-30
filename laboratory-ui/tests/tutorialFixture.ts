import {expect} from '@playwright/test';
import {execFileSync} from 'node:child_process';
import {resolve} from 'node:path';

export async function setup(page:any, withCamera=true) {
  const root=resolve(process.cwd(),'..');
  const fixture=JSON.parse(execFileSync(resolve(root,'.venv/bin/python'),['-c',
    'import json;from harmonic_weaver.lab.contracts import Preset;p=Preset();print(json.dumps({"preset":p.model_dump(),"schemas":{"Preset":Preset.model_json_schema()}}))'],{cwd:root,encoding:'utf8'}));
  const joints=Array.from({length:17},(_,index)=>({index,position:[.4+(index%2)*.2,.15+index*.035],confidence:1,state:'observed'}));
  const state:any={preset:fixture.preset,session:{session_id:'synthetic',desired_revision:8,person_id:'one',playing:true,position_s:0,status:'playing'},
    source:withCamera?{kind:'camera',camera:{status:'ready',stream_id:'synthetic'}}:{kind:null},
    motion_frame:withCamera?{source_id:'synthetic',stream_id:'synthetic',width:640,height:480,sequence:1,persons:[{person_id:'one',joints}]}:null,
    runtime:{routing:{voices:{'4':{state:'active',target_gain:.24},'6':{state:'active',target_gain:.61}}},diagnostic:{code:'active',message:'Synthetic',pose:{observed:17}}},
    shaper:{},voice_frame:{sample_index:0,sample_rate:48000,voices:[]}};
  const writes:string[]=[],errors:string[]=[],updates:any[]=[];
  await page.routeWebSocket('**/ws',(ws:any)=>{const send=()=>ws.send(JSON.stringify(state));send();const timer=setInterval(send,50);ws.onClose(()=>clearInterval(timer));});
  await page.route('**/api/**',async(route:any)=>{
    const req=route.request(),path=new URL(req.url()).pathname;
    if(req.method()!=='GET'){
      writes.push(path);const body=req.postDataJSON();updates.push({path,body});
      if(path==='/api/configuration'){state.preset=body.preset;state.session.desired_revision++;}
      await route.fulfill({json:state});return;
    }
    if(path==='/api/camera/preview'){await route.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480"><rect width="640" height="480" fill="#173249"/></svg>'});return;}
    const responses:any={'/api/state':state,'/api/schemas':fixture.schemas,'/api/presets':[],
      '/api/media':[],'/api/calibrations':[],'/api/signals':{},'/api/algorithms':[],
      '/api/environment':{perception:{}},'/api/source-preferences':{default_person:'first',autoplay_video:false},'/api/marks':[]};
    await route.fulfill({json:responses[path]??[]});
  });
  page.on('pageerror',(error:any)=>errors.push(String(error)));
  await page.goto('/');await expect(page.getByRole('button',{name:'Hacer tutorial',exact:true})).toBeVisible();
  return {state,writes,errors,updates};
}

