import {test,expect} from '@playwright/test';
test('real R04 HTTP workers repeat exactly and browser shows contextual traces',async({page})=>{
 test.skip(!process.env.LAB_R04_NETWORK_URL,'explicit R04 HTTP fixture required');
 const origin=process.env.LAB_R04_NETWORK_URL!;
 await page.goto(origin);
 await page.getByLabel('Muestras R04').fill('30');
 const results:Buffer[]=[];
 for(let i=0;i<2;i++){
  const started=page.waitForResponse(r=>r.url()===`${origin}/api/research/r04` && r.request().method()==='POST');
  await page.getByRole('button',{name:'Correr banco R04'}).click();
  const response=await started;expect(response.status()).toBe(200);
  const ident=(await response.json()).id;
  const view=page.getByRole('button',{name:`Ver resultado R04 ${ident}`});
  await expect(view).toBeVisible({timeout:10000});await view.click();
  await expect(page.getByRole('table')).toBeVisible();
  await page.getByRole('combobox',{name:/^Traza R04/}).selectOption('shared_acceleration/original');
  await expect(page.getByText('indefinido',{exact:true})).toHaveCount(3);
  const trace=page.getByRole('combobox',{name:/^Traza R04/});
  const sample=page.getByLabel('Muestra de traza R04');
  await trace.selectOption('wrist_brake_parent_still/original');
  await sample.fill('10');
  await expect(page.getByRole('table').locator('tbody td').first()).toHaveText('-1');
  await trace.selectOption('wrist_brake_parent_moving/original');await sample.fill('10');
  await expect(page.getByRole('table').locator('tbody td').first()).toHaveText('1');
  const result=await page.request.get(`${origin}/api/research/r04/${ident}/artifacts/result.json`);
  expect(result.status()).toBe(200);results.push(await result.body());
  expect(Object.keys((await result.json()).traces)).toHaveLength(30);
  const downloading=page.waitForEvent('download');
  await page.locator(`a[href="/api/research/r04/${ident}/artifacts/request.json"]`).click();
  const download=await downloading;expect(download.suggestedFilename()).toBe('request.json');expect(await download.failure()).toBeNull();
 }
 expect(results[0].equals(results[1])).toBe(true);
 await expect(page.getByRole('alert').filter({hasText:/invalid|Error/})).toHaveCount(0);
});
