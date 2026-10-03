import {test,expect} from '@playwright/test';
test('explicit mapping coverage and persisted result',async({page})=>{
 test.skip(!process.env.LAB_R08_BENCHMARK_URL,'isolated fixture required');
 const origin=process.env.LAB_R08_BENCHMARK_URL!;
 const post=async(path:string,data:any)=>(await page.request.post(`${origin}/api/research/r08${path?'/'+path:''}`,{data})).json();
 const media=await post('probe',{media_id:'synthetic'});
 const annotation={media_sha256:media.media_sha256,width_px:media.width_px,height_px:media.height_px,frames:[0,1,2].map(i=>({frame_index:i,time_s:media.frame_times_s[i],state:'observed',visible_segments:[[{x:.2,y:.2},{x:.5,y:.5}]],endpoints:{a:{x:.5,y:.5}}}))};
 const ref=await post('',{media_id:'synthetic',annotation});
 const job=await post('flow',{media_id:'synthetic',request:{media_sha256:media.media_sha256,width_px:media.width_px,height_px:media.height_px,start_frame_index:0,frame_times_s:media.frame_times_s.slice(0,3),seeds:[{x:.5,y:.5}]}});
 await expect.poll(async()=>(await(await page.request.get(`${origin}/api/research/r08/flow/${job.id}`)).json()).status).toBe('complete');
 await page.goto(origin);
 const panel=page.getByRole('region',{name:'Benchmark temporal de extremos R08'});
 await panel.getByLabel('Referencia temporal R08').selectOption(ref.id);
 await panel.getByLabel('Corrida temporal R08').selectOption(job.id);
 await expect(panel.getByLabel('Semillas y extremos en frame inicial R08')).toBeVisible();
 const start=panel.getByRole('button',{name:'Evaluar extremos R08',exact:true});await expect(start).toBeDisabled();
 await panel.getByLabel('Semilla para extremo a R08').fill('3');await expect(start).toBeDisabled();
 await panel.getByLabel('Semilla para extremo a R08').fill('0');await panel.getByLabel('Semilla para extremo b R08').fill('0');await expect(start).toBeDisabled();
 await panel.getByLabel('Semilla para extremo b R08').fill('');
 let first=true;const sent:any[]=[];
 await page.route('**/api/research/r08/flow-benchmarks',async route=>{
  if(route.request().method()!=='POST'){await route.continue();return;}
  sent.push(route.request().postDataJSON());
  if(first){first=false;await route.fetch();await route.abort('failed');}else await route.continue();
 });
 await start.click();await expect(panel.getByRole('button',{name:'Recuperar comparación pendiente R08'})).toBeVisible();
 await page.reload();await page.getByRole('button',{name:'Recuperar comparación pendiente R08'}).click();
 expect(sent).toHaveLength(2);expect(sent[1]).toEqual(sent[0]);
 await expect(panel.getByText(/entrada de semillas 1/)).toBeVisible();await expect(panel.getByText(/Soporte: .*\/2 extremos elegibles/)).toBeVisible();
 const download=page.waitForEvent('download');await panel.getByRole('link',{name:'result.json',exact:true}).click();expect((await download).suggestedFilename()).toBe('result.json');
 await page.reload();await expect(page.getByText(/Métrica recalculada sobre entradas congeladas/)).toBeVisible();
 await page.getByRole('button',{name:'Ver benchmark R08',exact:true}).click();await expect(page.getByText(/entrada de semillas 1/)).toBeVisible();
 expect((await(await page.request.get(`${origin}/api/research/r08/flow-benchmarks`)).json())).toHaveLength(1);
 const existing=await(await page.request.get(`${origin}/api/research/r08/flow-benchmarks`)).json();
 const second=await post('flow-benchmarks',{reference_id:ref.id,flow_id:job.id,endpoint_seeds:{a:0}});
 await page.reload();const paired=page.getByRole('region',{name:'Comparación pareada R08',exact:true});
 const compare=paired.getByRole('button',{name:'Comparar soporte común R08'});await expect(compare).toBeDisabled();
 await paired.getByLabel(existing[0].id,{exact:true}).check();await expect(compare).toBeDisabled();
 await paired.getByLabel(second.id,{exact:true}).check();
 let pairedFirst=true;const pairedSent:any[]=[];
 await page.route('**/api/research/r08/flow-paired',async route=>{
  if(route.request().method()!=='POST'){await route.continue();return;}
  pairedSent.push(route.request().postDataJSON());
  if(pairedFirst){pairedFirst=false;await route.fetch();await route.abort('failed');}else await route.continue();
 });
 await compare.click();await expect(paired.getByRole('button',{name:'Recuperar banco pareado pendiente R08'})).toBeVisible();
 await page.reload();await page.getByRole('button',{name:'Recuperar banco pareado pendiente R08'}).click();
 expect(pairedSent).toHaveLength(2);expect(pairedSent[1]).toEqual(pairedSent[0]);
 await expect(paired.getByText(/Soporte común:/)).toBeVisible();
 await expect(paired.getByRole('table')).toBeVisible();
 const pairedDownload=page.waitForEvent('download');await paired.getByRole('link',{name:'result.json',exact:true}).click();expect((await pairedDownload).suggestedFilename()).toBe('result.json');
 await page.reload();await page.getByRole('button',{name:'Ver banco pareado R08',exact:true}).click();
 await expect(page.getByText(/Soporte común:/)).toBeVisible();
 expect((await(await page.request.get(`${origin}/api/research/r08/flow-paired`)).json())).toHaveLength(1);

});
