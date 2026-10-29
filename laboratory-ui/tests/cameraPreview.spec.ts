import {test, expect} from '@playwright/test';
import {execFileSync} from 'node:child_process';
import {resolve} from 'node:path';

async function camera(page:any, holdFirst=false) {
  const root=resolve(process.cwd(),'..');
  const data=JSON.parse(execFileSync(resolve(root,'.venv/bin/python'),['-c',
    'import json; from harmonic_weaver.lab.contracts import Preset; p=Preset(); print(json.dumps({"preset":p.model_dump(),"schemas":{"Preset":Preset.model_json_schema()}}))'],{cwd:root,encoding:'utf8'}));
  const state:any={preset:data.preset,session:{session_id:'synthetic',playing:true,status:'waiting',position_s:0},
    source:{kind:'camera',camera:{status:'ready',stream_id:'synthetic-camera'}},motion_frame:null,
    runtime:{diagnostic:{code:'tracking_missing',message:'Synthetic stale pose'}},
    shaper:{},voice_frame:{sample_index:0,sample_rate:48000,voices:[]}};
  const result={requests:0,active:0,maxActive:0,writes:[] as string[],errors:[] as string[]};
  let release!:()=>void;
  const gate=new Promise<void>(done=>release=done);
  await page.addInitScript(()=>{
    (window as any).previewColors=[];
    document.addEventListener('load',event=>{
      const img=event.target as HTMLImageElement;
      if(img.tagName!=='IMG'||img.alt!=='Cámara en vivo')return;
      const canvas=document.createElement('canvas');canvas.width=canvas.height=1;
      const ctx=canvas.getContext('2d')!;ctx.drawImage(img,0,0,1,1);
      (window as any).previewColors.push([...ctx.getImageData(0,0,1,1).data].slice(0,3).join(','));
    },true);
  });
  await page.routeWebSocket('**/ws',(ws:any)=>{
    const send=()=>ws.send(JSON.stringify(state));send();
    const timer=setInterval(send,50);ws.onClose(()=>clearInterval(timer));
  });
  await page.route('**/api/**',async(route:any)=>{
    const request=route.request(),path=new URL(request.url()).pathname;
    if(request.method()!=='GET')result.writes.push(path);
    if(path==='/api/camera/preview') {
      const n=++result.requests;result.active++;result.maxActive=Math.max(result.maxActive,result.active);
      try {
        if(holdFirst&&n===1){await gate;await route.fulfill({status:503});}
        else await route.fulfill({contentType:'image/svg+xml',body:`<svg xmlns="http://www.w3.org/2000/svg" width="2" height="2"><rect width="2" height="2" fill="${n%2?'red':'blue'}"/></svg>`});
      } finally {result.active--;}
      return;
    }
    const responses:any={'/api/state':state,'/api/schemas':data.schemas,'/api/presets':[],
      '/api/media':[],'/api/calibrations':[],'/api/signals':{},'/api/algorithms':[],
      '/api/environment':{perception:{}},'/api/source-preferences':{default_person:'first',autoplay_video:false},'/api/marks':[]};
    await route.fulfill({json:responses[path]??[]});
  });
  page.on('pageerror',(error:any)=>result.errors.push(String(error)));
  await page.goto('/');await expect(page.getByRole('button',{name:'Performance',exact:true})).toBeVisible();
  return {state,result,release};
}

test('camera images keep changing with no accepted pose and across Performance view',async({page})=>{
  const {state,result}=await camera(page);
  await expect.poll(()=>result.requests).toBeGreaterThanOrEqual(3);
  const colors=await page.evaluate(()=>(window as any).previewColors);
  expect(colors).toContain('255,0,0');expect(colors).toContain('0,0,255');
  expect(state.motion_frame).toBeNull();
  await page.evaluate(()=>(window as any).previewNode=document.querySelector('img[alt="Cámara en vivo"]'));
  const before=result.requests;
  await page.getByRole('button',{name:'Performance',exact:true}).click();
  await expect.poll(()=>result.requests).toBeGreaterThan(before);
  expect(await page.evaluate(()=>(window as any).previewNode===document.querySelector('img[alt="Cámara en vivo"]'))).toBe(true);
  expect(result.writes).toEqual([]);expect(result.errors).toEqual([]);
});

test('preview applies backpressure, recovers after unavailable JPEG, and stops on source close',async({page})=>{
  const {state,result,release}=await camera(page,true);
  await expect.poll(()=>result.requests).toBe(1);
  await page.waitForTimeout(250);expect(result.requests).toBe(1);
  release();await expect.poll(()=>result.requests).toBeGreaterThanOrEqual(3);
  expect(result.maxActive).toBe(1);
  state.source={kind:null};
  await expect(page.getByAltText('Cámara en vivo',{exact:true})).toHaveCount(0);
  const stopped=result.requests;await page.waitForTimeout(250);expect(result.requests).toBe(stopped);
  expect(result.writes).toEqual([]);expect(result.errors).toEqual([]);
});
