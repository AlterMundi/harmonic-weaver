import {test,expect} from '@playwright/test';

for(const holdEditResponse of [false,true])test('late preset response preserves '+(holdEditResponse?'pending':'confirmed')+' control edits',async({page})=>{
 test.skip(!process.env.LAB_PRESET_RESPONSE_URL,'isolated production laboratory required');
 const origin=process.env.LAB_PRESET_RESPONSE_URL!;let pauseSnapshots=false;
 await page.routeWebSocket(/\/ws$/,socket=>{
  const server=socket.connectToServer();
  server.onMessage(message=>{if(!pauseSnapshots)socket.send(message)});
  socket.onMessage(message=>server.send(message));
 });
 const errors:string[]=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(origin);await expect(page.getByRole('heading',{name:'Weaver / laboratorio corporal',exact:true})).toBeVisible();
 const initial=await(await page.request.get(`${origin}/api/state`)).json();
 const presets=await(await page.request.get(`${origin}/api/presets`)).json();
 const preset=presets.find((p:any)=>p.algorithm.id==='baseline'&&p.id!==initial.preset.id);
 expect(preset).toBeTruthy();const applyURL=`${origin}/api/presets/${preset.id}/apply`;
 let release!:()=>void;const held=new Promise<void>(resolve=>release=resolve);let reached=false;
 await page.route(applyURL,async route=>{const response=await route.fetch();expect(response.ok()).toBe(true);reached=true;await held;await route.fulfill({response})});
 await page.getByRole('button',{name:'Presets',exact:true}).click();await page.getByRole('button',{name:preset.name,exact:true}).click();await expect.poll(()=>reached).toBe(true);
 // Backend has applied the preset; its real WS snapshot exposes the new revision.
 await expect.poll(async()=> (await(await page.request.get(`${origin}/api/state`)).json()).preset.id).toBe(preset.id);
 await page.getByRole('button',{name:'Instrumento',exact:true}).click();const master=page.getByRole('spinbutton',{name:'Master',exact:true});await expect(master).toHaveValue(String(preset.master));
 pauseSnapshots=true;
 const configURL=`${origin}/api/configuration`;let releaseEdit!:()=>void;let editReached=false;let newer:any;const heldEdit=new Promise<void>(resolve=>releaseEdit=resolve);
 if(holdEditResponse)await page.route(configURL,async route=>{const response=await route.fetch();expect(response.ok()).toBe(true);newer=await response.json();editReached=true;await heldEdit;await route.fulfill({response})});
 const changed=page.waitForResponse(r=>r.url()===configURL&&r.request().method()==='PUT');await master.fill('.173');
 if(holdEditResponse)await expect.poll(()=>editReached).toBe(true);else{const response=await changed;expect(response.ok()).toBe(true);newer=await response.json()}
 const late=page.waitForResponse(r=>r.url()===applyURL);release();await (await late).finished();await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));
 // Keep snapshots paused: no later WS refresh can mask a stale HTTP overwrite.
 await expect.poll(async()=>Number(await master.inputValue())).toBe(.173);
 if(holdEditResponse){releaseEdit();await(await changed).finished();await page.unroute(configURL)}
 const nextEdit=page.waitForResponse(r=>r.url()===`${origin}/api/configuration`&&r.request().method()==='PUT');await master.fill('.174');const next=await nextEdit;expect(next.ok(),await next.text()).toBe(true);const final=await next.json();
 expect(final.session.desired_revision).toBe(newer.session.desired_revision+1);expect(final.preset.master).toBe(.174);
 pauseSnapshots=false;await page.unroute(applyURL);expect(errors).toEqual([]);
});

test('late first preset cannot replace a newer applied preset',async({page})=>{
 test.skip(!process.env.LAB_PRESET_RESPONSE_URL,'isolated production laboratory required');
 const origin=process.env.LAB_PRESET_RESPONSE_URL!;let pauseSnapshots=false;
 await page.routeWebSocket(/\/ws$/,socket=>{const server=socket.connectToServer();server.onMessage(message=>{if(!pauseSnapshots)socket.send(message)});socket.onMessage(message=>server.send(message))});
 const initial=await(await page.request.get(`${origin}/api/state`)).json();const presets=await(await page.request.get(`${origin}/api/presets`)).json();
 const first=presets.find((p:any)=>p.algorithm.id==='baseline'&&p.id!==initial.preset.id);
 const second={...first,id:'late-response-'+Date.now(),name:'Delayed response control '+Date.now(),master:.293};
 expect((await page.request.post(`${origin}/api/presets`,{data:second})).ok()).toBe(true);
 await page.goto(origin);await expect(page.getByRole('heading',{name:'Weaver / laboratorio corporal',exact:true})).toBeVisible();
 const firstURL=`${origin}/api/presets/${first.id}/apply`;let release!:()=>void;let reached=false;const held=new Promise<void>(resolve=>release=resolve);
 await page.route(firstURL,async route=>{const response=await route.fetch();expect(response.ok()).toBe(true);reached=true;await held;await route.fulfill({response})});
 await page.getByRole('button',{name:'Presets',exact:true}).click();await page.getByRole('button',{name:first.name,exact:true}).click();await expect.poll(()=>reached).toBe(true);
 await page.getByRole('button',{name:'Instrumento',exact:true}).click();const master=page.getByRole('spinbutton',{name:'Master',exact:true});await expect(master).toHaveValue(String(first.master));
 pauseSnapshots=true;await page.getByRole('button',{name:'Presets',exact:true}).click();
 const confirmed=page.waitForResponse(r=>r.url()===`${origin}/api/presets/${second.id}/apply`);await page.getByRole('button',{name:second.name,exact:true}).click();const response=await confirmed;expect(response.ok(),await response.text()).toBe(true);
 await page.getByRole('button',{name:'Instrumento',exact:true}).click();await expect(master).toHaveValue(String(second.master));
 const late=page.waitForResponse(r=>r.url()===firstURL);release();await (await late).finished();await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));
 await expect(master).toHaveValue(String(second.master));
 const edit=page.waitForResponse(r=>r.url()===`${origin}/api/configuration`&&r.request().method()==='PUT');await master.fill('.177');const changed=await edit;expect(changed.ok(),await changed.text()).toBe(true);expect((await changed.json()).preset.id).toBe(second.id);
 pauseSnapshots=false;
});
