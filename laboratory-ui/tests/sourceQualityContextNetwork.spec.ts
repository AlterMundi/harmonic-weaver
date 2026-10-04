import {test,expect} from '@playwright/test';

for(const oldFails of [false,true])test('old source quality '+(oldFails?'failure':'report')+' cannot replace the current source',async({page})=>{
 test.skip(!process.env.LAB_SOURCE_QUALITY_URL||!process.env.LAB_SOURCE_QUALITY_VIDEO,'isolated frozen-source production laboratory required');
 const origin=process.env.LAB_SOURCE_QUALITY_URL!,videoPath=process.env.LAB_SOURCE_QUALITY_VIDEO!;
 const initial=await(await page.request.get(`${origin}/api/state`)).json();const firstId=initial.source.job.id;
 const firstURL=`${origin}/api/media/${firstId}/quality`;let release!:()=>void;let reached=false;const held=new Promise<void>(resolve=>release=resolve);
 await page.route(/\/api\/media\/[^/]+\/quality$/,async route=>{
  const response=await route.fetch();expect(response.ok()).toBe(true);const report=await response.json();
  // Fault-control caption tags distinguish responses; all coverage numbers remain real.
  if(route.request().url()===firstURL){reached=true;await held;
   if(oldFails)await route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'old-quality-fault-control'})});
   else await route.fulfill({json:{...report,warning:report.warning+' old-quality-fault-control'}});
  }else await route.fulfill({json:{...report,warning:report.warning+' current-quality-fault-control'}});
 });
 const errors:string[]=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(origin);await expect.poll(()=>reached).toBe(true);
 await page.getByLabel('Ruta del video',{exact:true}).fill(videoPath);await page.getByRole('button',{name:'Abrir video',exact:true}).click();
 await expect.poll(async()=>{const state=await(await page.request.get(`${origin}/api/state`)).json();return state.source?.job?.status==='ready'&&state.source.job.id!==firstId&&state.source.job.cache_hit},{timeout:20000}).toBe(true);
 await page.getByText('Cobertura de tracking y huecos',{exact:true}).click();await expect(page.getByText(/current-quality-fault-control/)).toBeVisible();
 const oldResponse=page.waitForResponse(response=>response.url()===firstURL);release();await(await oldResponse).finished();
 await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));
 await expect(page.getByText(/current-quality-fault-control/)).toBeVisible();await expect(page.getByText(/old-quality-fault-control/)).toHaveCount(0);
 expect(errors).toEqual([]);
});
