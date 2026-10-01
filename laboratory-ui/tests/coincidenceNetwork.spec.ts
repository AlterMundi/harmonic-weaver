import {test,expect} from '@playwright/test';
test('real network panel freezes verified replay, runs twice and downloads equal artifacts',async({page})=>{
 test.skip(!process.env.LAB_R03_NETWORK_URL,'explicit synthetic HTTP fixture required');
 const origin=process.env.LAB_R03_NETWORK_URL!;
 await page.goto(origin);
 await page.getByRole('combobox',{name:/^Comparación R03/}).selectOption({index:1});
 await page.getByRole('combobox',{name:/^Señal R03/}).selectOption('zone.1.speed');
 await page.getByRole('combobox',{name:/^Grupo de marcas R03/}).selectOption({index:1});
 await page.getByLabel('Intervalos realmente observados R03 (JSON)').fill('[[0.2,2]]');
 await page.getByLabel('Desplazamientos de control R03 (JSON, segundos)').fill('[0.1,-0.1]');
 const results:Buffer[]=[];
 for(let i=0;i<2;i++){
  const started=page.waitForResponse(r=>r.url()===`${origin}/api/research/r03` && r.request().method()==='POST');
  await page.getByRole('button',{name:'Correr contraste R03'}).click();
  const response=await started;expect(response.status()).toBe(200);
  const ident=(await response.json()).id;
  const view=page.getByRole('button',{name:`Ver resultado R03 ${ident}`});
  await expect(view).toBeVisible({timeout:10000});await view.click();
  await expect(page.getByRole('table')).toBeVisible();
  const result=await page.request.get(`${origin}/api/research/r03/${ident}/artifacts/result.json`);
  expect(result.status()).toBe(200);results.push(await result.body());
  const value=await result.json();
  expect(value.temporal_controls.conditions).toHaveLength(3);
  expect(value.feature_provenance.source.person_id).toBe('one');
  expect(value.candidates.events).toBeDefined();
  const downloadPromise=page.waitForEvent('download');
  await page.locator(`a[href="/api/research/r03/${ident}/artifacts/features.json"]`).click();
  const download=await downloadPromise;
  expect(download.suggestedFilename()).toBe('features.json');
  expect(await download.failure()).toBeNull();
 }
 expect(results[0].equals(results[1])).toBe(true);
 await expect(page.getByRole('alert').filter({hasText:/invalid|Error/})).toHaveCount(0);
});
