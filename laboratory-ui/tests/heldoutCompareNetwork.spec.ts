import {test,expect} from '@playwright/test';

for(const mode of ['prefix','horizon','context'])test(`R13 saved-run common support ${mode}`,async({page})=>{
 test.skip(!process.env.LAB_R13_COMPARE_URL,'isolated production laboratory required');
 const origin=process.env.LAB_R13_COMPARE_URL!;
 const first=await(await page.request.get(`${origin}/api/research/r13/template`)).json();
 const second=structuredClone(first);
 if(mode==='prefix')second.settings.adaptation_prefix_samples=30;
 if(mode==='horizon')second.settings.horizon_steps=2;
 if(mode==='context')second.sequences[1].subject_group='different-declared-context';
 const ids:string[]=[];
 for(const request of [first,second]){
  const accepted=await page.request.post(`${origin}/api/research/r13`,{data:request});expect(accepted.ok()).toBe(true);const id=(await accepted.json()).id;ids.push(id);
  await expect.poll(async()=>{const jobs=await(await page.request.get(`${origin}/api/research/r13`)).json();return jobs.find((j:any)=>j.id===id)?.status},{timeout:20000}).toBe('complete');
 }
 const before=await(await page.request.get(`${origin}/api/state`)).json();
 await page.goto(origin);await page.getByRole('button',{name:'Investigación',exact:true}).click();
 const panel=page.getByRole('region',{name:'Transferencia reservada R13'});
 for(const id of ids)await panel.getByRole('checkbox',{name:`Comparar R13 ${id}`,exact:true}).check();
 const response=page.waitForResponse(r=>r.url()===`${origin}/api/research/r13/compare`);
 await panel.getByRole('button',{name:'Comparar soporte común R13',exact:true}).click();const compared=await response;
 if(mode==='context'){
  expect(compared.status()).toBe(422);await expect(panel.getByRole('alert')).toContainText('same frozen sequences');await expect(panel.getByRole('table',{name:'Soporte común R13 reserved',exact:true})).toHaveCount(0);
 }else{
  expect(compared.ok(),await compared.text()).toBe(true);const report=await compared.json();expect(report.run_ids).toEqual(ids);
  const sequence=report.sequences[0],a=sequence.conditions[0],b=sequence.conditions[1];
  expect(sequence.common_count).toBe(mode==='prefix'?149:0);
  if(mode==='prefix'){
   expect(a.eligible_count).toBe(178);expect(a.excluded_from_common).toBe(29);expect(b.excluded_from_common).toBe(0);expect(b.mean_delta_mse_vs_first.persistence).toBe(0);
  }else{expect(Object.values(a.mean_mse).every(v=>v===null)).toBe(true);await expect(panel.getByText('Sin soporte compartido; no hay puntuación.',{exact:false})).toBeVisible();}
  await expect(panel.getByRole('table',{name:'Soporte común R13 reserved',exact:true})).toBeVisible();
  const download=page.waitForEvent('download');await panel.getByRole('button',{name:'Guardar comparación R13',exact:true}).click();expect((await download).suggestedFilename()).toBe('r13-common-support.json');
  await panel.getByRole('checkbox',{name:`Comparar R13 ${ids[1]}`,exact:true}).uncheck();await expect(panel.getByRole('table',{name:'Soporte común R13 reserved',exact:true})).toHaveCount(0);
  await expect(panel.getByRole('alert')).toHaveCount(0);
 }
 const after=await(await page.request.get(`${origin}/api/state`)).json();expect(after.preset).toEqual(before.preset);expect(after.session.desired_revision).toBe(before.session.desired_revision);
});
