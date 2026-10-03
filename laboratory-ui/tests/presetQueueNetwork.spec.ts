import {test,expect} from '@playwright/test';

test('rapid preset choices serialize and retain the latest choice',async({page})=>{
 test.skip(!process.env.LAB_PRESET_QUEUE_URL,'isolated production laboratory required');
 const origin=process.env.LAB_PRESET_QUEUE_URL!;
 const templates=await(await page.request.get(`${origin}/api/presets`)).json();
 const template=templates.find((p:any)=>p.algorithm.id==='baseline');
 const presets=[0,1,2].map(i=>({...template,id:`queue-${Date.now()}-${i}`,name:`Queue control ${Date.now()} ${i}`,master:.21+i*.1}));
 for(const p of presets)expect((await page.request.post(`${origin}/api/presets`,{data:p})).ok()).toBe(true);
 let pauseSnapshots=false;
 await page.routeWebSocket(/\/ws$/,socket=>{const server=socket.connectToServer();server.onMessage(m=>{if(!pauseSnapshots)socket.send(m)});socket.onMessage(m=>server.send(m))});
 await page.goto(origin);await page.getByRole('button',{name:'Presets',exact:true}).click();
 await expect(page.getByRole('button',{name:presets[0].name,exact:true})).toBeVisible();
 const initial=await(await page.request.get(`${origin}/api/state`)).json();
 pauseSnapshots=true;
 let release!:()=>void;const held=new Promise<void>(r=>release=r);let reached=false;const submitted:string[]=[];
 await page.route(/\/api\/presets\/[^/]+\/apply$/,async route=>{
  const id=route.request().url().split('/').at(-2)!;submitted.push(id);
  if(id===presets[0].id){reached=true;await held;}
  await route.continue();
 });
 await page.getByRole('button',{name:presets[0].name,exact:true}).click();await expect.poll(()=>reached).toBe(true);
 await page.getByRole('button',{name:presets[1].name,exact:true}).click();
 await page.getByRole('button',{name:presets[2].name,exact:true}).click();
 const latest=page.waitForResponse(r=>r.url()===`${origin}/api/presets/${presets[2].id}/apply`);
 release();const response=await latest;expect(response.ok(),await response.text()).toBe(true);
 await expect(page.getByLabel('Nombre',{exact:true})).toHaveAttribute('placeholder',presets[2].name);
 expect(submitted).toEqual([presets[0].id,presets[2].id]);
 const final=await(await page.request.get(`${origin}/api/state`)).json();expect(final.preset.id).toBe(presets[2].id);expect(final.session.desired_revision).toBe(initial.session.desired_revision+2);
 await expect(page.getByText(/expected revision/)).toHaveCount(0);
 pauseSnapshots=false;
});

for(const outcome of ['edit','conflict'])test(`queued preset is discarded after ${outcome}`,async({page})=>{
 test.skip(!process.env.LAB_PRESET_QUEUE_URL,'isolated production laboratory required');
 const origin=process.env.LAB_PRESET_QUEUE_URL!;
 const templates=await(await page.request.get(`${origin}/api/presets`)).json();const template=templates.find((p:any)=>p.algorithm.id==='baseline');
 const choices=[0,1].map(i=>({...template,id:`cancel-${Date.now()}-${i}`,name:`Cancel queue ${Date.now()} ${i}`}));
 for(const p of choices)expect((await page.request.post(`${origin}/api/presets`,{data:p})).ok()).toBe(true);
 await page.goto(origin);await page.getByRole('button',{name:'Presets',exact:true}).click();await expect(page.getByRole('button',{name:choices[0].name,exact:true})).toBeVisible();
 let release!:()=>void;let reached=false;const held=new Promise<void>(r=>release=r);const submitted:string[]=[];
 await page.route(/\/api\/presets\/[^/]+\/apply$/,async route=>{
  const id=route.request().url().split('/').at(-2)!;submitted.push(id);
  if(id===choices[0].id){
   const response=outcome==='edit'?await route.fetch():null;
   reached=true;await held;
   if(response)await route.fulfill({response});else await route.fulfill({status:409,contentType:'application/json',body:JSON.stringify({detail:'explicit-conflict-control'})});
  }else await route.continue();
 });
 await page.getByRole('button',{name:choices[0].name,exact:true}).click();await expect.poll(()=>reached).toBe(true);
 await page.getByRole('button',{name:choices[1].name,exact:true}).click();
 if(outcome==='edit'){
  await expect(page.getByLabel('Nombre',{exact:true})).toHaveAttribute('placeholder',choices[0].name);
  await page.getByRole('button',{name:'Instrumento',exact:true}).click();
  const accepted=page.waitForResponse(r=>r.url()===`${origin}/api/configuration`&&r.request().method()==='PUT');
  await page.getByRole('spinbutton',{name:'Master',exact:true}).fill('.137');expect((await accepted).ok()).toBe(true);
 }
 const first=page.waitForResponse(r=>r.url()===`${origin}/api/presets/${choices[0].id}/apply`);release();await(await first).finished();
 await page.getByRole('button',{name:'Presets',exact:true}).click();await expect(page.getByText(/esperando confirmación/)).toHaveCount(0);
 expect(submitted).toEqual([choices[0].id]);
 if(outcome==='conflict')await expect(page.getByText(/explicit-conflict-control/)).toBeVisible();
 else {const final=await(await page.request.get(`${origin}/api/state`)).json();expect(final.preset.id).toBe(choices[0].id);expect(final.preset.master).toBe(.137);}
});
