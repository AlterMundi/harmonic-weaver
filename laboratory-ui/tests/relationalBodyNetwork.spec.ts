import {test,expect} from '@playwright/test';
test('R04 body real network freezes endpoints and repeats exact worker results',async({page})=>{
 test.skip(!process.env.LAB_R04_BODY_NETWORK_URL,'explicit pose HTTP fixture required');
 const origin=process.env.LAB_R04_BODY_NETWORK_URL!;
 await page.goto(origin);
 await page.getByRole('combobox',{name:/^Comparación corporal R04/}).selectOption({index:1});
 await page.getByRole('combobox',{name:/^Extremo proximal R04/}).selectOption('7');
 await page.getByRole('combobox',{name:/^Extremo distal R04/}).selectOption('9');
 const results:Buffer[]=[];
 for(let i=0;i<2;i++){
  const started=page.waitForResponse(r=>r.url()===`${origin}/api/research/r04/trace` && r.request().method()==='POST');
  await page.getByRole('button',{name:'Correr R04 con pose congelada'}).click();
  const response=await started;expect(response.status()).toBe(200);
  const ident=(await response.json()).id;
  const view=page.getByRole('button',{name:`Ver resultado R04 ${ident}`});
  await expect(view).toBeVisible({timeout:10000});await view.click();
  await expect(page.getByText('Resultado corporal congelado:',{exact:false})).toContainText('persona one');
  const result=await page.request.get(`${origin}/api/research/r04/${ident}/artifacts/result.json`);
  expect(result.status()).toBe(200);results.push(await result.body());
  const value=await result.json();expect(value.input_kind).toBe('frozen_pose_endpoints');
  expect(value.selection).toMatchObject({parent_joint:7,child_joint:9,start_s:.2,end_s:2});
  expect(Object.keys(value.traces)).toHaveLength(6);
  expect(value.traces.original.some((r:any)=>!r.input_valid)).toBe(true);
  expect(value.traces.original.some((r:any)=>r.relative.state==='observed')).toBe(true);
  const downloading=page.waitForEvent('download');
  await page.locator(`a[href="/api/research/r04/${ident}/artifacts/input.json"]`).click();
  const download=await downloading;expect(download.suggestedFilename()).toBe('input.json');expect(await download.failure()).toBeNull();
 }
 expect(results[0].equals(results[1])).toBe(true);
 await expect(page.getByRole('alert').filter({hasText:/invalid|Error/})).toHaveCount(0);
});
