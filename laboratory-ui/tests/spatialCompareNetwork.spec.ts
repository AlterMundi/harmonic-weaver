import {test,expect} from '@playwright/test';
test('spatial comparison common clock coverage export and reload',async({page})=>{
 test.skip(!process.env.LAB_R09_COMPARE_URL,'isolated fixture required');await page.goto(process.env.LAB_R09_COMPARE_URL!);
 const panel=page.getByRole('region',{name:'Comparación espacial R09',exact:true});
 const stream=(times:number[],p:number[])=>({source_id:'synthetic',subject_slot:'slot',provider:'image_pose',dimensions:2,coordinate_frame:'image',units:'image_normalized',clock:{source_clock:'pts',common_clock:'session',offset_s:0,rate:1,uncertainty_s:.01,method:'declared_assumption'},frames:times.map((t,i)=>({index:i,source_time_s:t,points:[{label:'hand',state:'observed',position:p}]}))});
 await panel.getByLabel('Stream referencia R09').fill(JSON.stringify(stream([.1,.2],[.1,.2])));
 await panel.getByLabel('Stream candidato R09').fill(JSON.stringify(stream([.11,.19],[.4,.6])));
 await panel.getByLabel('Etiquetas de comparación R09').fill('["hand"]');await panel.getByRole('button',{name:'Guardar comparación espacial R09'}).click();
 await expect(panel.getByText(/Soporte espacial: 1\/2/)).toBeVisible();await expect(panel.getByText(/Error medio sobre soporte: 0.5/)).toBeVisible();
 const download=page.waitForEvent('download');await panel.getByRole('link',{name:'result.json',exact:true}).click();expect((await download).suggestedFilename()).toBe('result.json');
 await page.reload();await panel.getByRole('button',{name:'Abrir comparación espacial R09'}).click();await expect(panel.getByText(/Soporte espacial: 1\/2/)).toBeVisible();
 const runs=await(await page.request.get(`${process.env.LAB_R09_COMPARE_URL}/api/research/r09/comparisons`)).json();expect(runs).toHaveLength(1);
});
test('saved conversion selection preserves provenance',async({page})=>{
 test.skip(!process.env.LAB_R09_COMPARE_URL,'isolated fixture required');const url=process.env.LAB_R09_COMPARE_URL!;
 const frames=[{source_id:'synthetic',stream_id:'test',sequence:0,source_time_s:0,available_monotonic_s:1,timestamp_origin:'pts',width:160,height:120,persons:[{person_id:'slot',joints:[{index:0,position:[.5,.2],confidence:.9,state:'observed'}]}]}];
 const conversion={frames,person_id:'slot',clock:{source_clock:'pts',common_clock:'session',offset_s:0,rate:1,uncertainty_s:.01,method:'declared_assumption'}};
 const ids=[];for(let i=0;i<2;i++){const r=await page.request.post(url+'/api/research/r09/conversions',{data:{conversion}});expect(r.ok()).toBeTruthy();ids.push((await r.json()).id);}
 await page.goto(url);const panel=page.getByRole('region',{name:'Comparación espacial R09',exact:true});
 await panel.getByLabel('Origen de comparación R09').selectOption('saved');await panel.getByRole('button',{name:'Actualizar conversiones para comparar R09'}).click();
 await panel.getByLabel('Referencia guardado R09').selectOption(ids[0]);await panel.getByLabel('Candidato guardado R09').selectOption(ids[1]);await panel.getByRole('button',{name:'Guardar comparación espacial R09'}).click();
 await expect(panel.getByText(/Error medio sobre soporte: 0;/)).toBeVisible();await expect(panel.getByText(/Conversiones comparadas:/)).toContainText(ids[0]);
 const rows=await(await page.request.get(url+'/api/research/r09/comparisons')).json();const results=await Promise.all(rows.map(async(r:any)=>(await page.request.get(url+'/api/research/r09/comparisons/'+r.id+'/artifacts/result.json')).json()));
 const result=results.find((r:any)=>r.sources?.reference.id===ids[0]);expect(result.sources.candidate.id).toBe(ids[1]);expect(result.sources.reference.manifest_sha256).toMatch(/^[a-f0-9]{64}$/);
});
