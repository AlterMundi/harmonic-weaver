import {test,expect} from '@playwright/test';

test('historical rope results remain readable without permitting current curve adoption',async({page})=>{
 test.skip(!process.env.LAB_R08_HISTORY_URL,'isolated historical fixture required');
 const origin=process.env.LAB_R08_HISTORY_URL!;
 const comparisons=await(await page.request.get(`${origin}/api/research/r08/comparisons`)).json();
 const paths=await(await page.request.get(`${origin}/api/research/r08/paths`)).json();
 expect(comparisons).toHaveLength(1);expect(paths).toHaveLength(1);
 expect(comparisons[0].read_verification).toBe('historical_integrity_only');
 expect(paths[0].read_verification).toBe('historical_integrity_only');
 const urls=[`/api/research/r08/comparisons/${comparisons[0].id}/artifacts/manifest.json`,
             `/api/research/r08/paths/${paths[0].id}/artifacts/manifest.json`];
 const before=await Promise.all(urls.map(async url=>{
  const response=await page.request.get(origin+url);expect(response.ok()).toBeTruthy();return response.body();
 }));
 await page.goto(origin);
 await expect(page.getByText(/Histórico: integridad verificada, recálculo actual no disponible/)).toBeVisible();
 await page.getByRole('button',{name:'Ver comparación R08',exact:true}).click();
 await expect(page.getByText('Soporte: 1/1 frames de referencia. Sin soporte: 0.',{exact:true})).toBeVisible();
 await page.getByLabel('Video de biblioteca R08').selectOption('synthetic');
 await page.getByRole('button',{name:'Preparar anotación R08',exact:true}).click();
 await expect(page.getByText(/Imagen decodificada/)).toBeVisible();
 const draft=await page.getByLabel('Anotación R08 JSON').inputValue();
 await expect(page.getByText(/Histórica: descargable, recálculo actual no disponible/)).toBeVisible();
 await expect(page.getByRole('button',{name:'Recuperar curva candidata R08',exact:true})).toBeDisabled();
 const rejected=await page.request.post(`${origin}/api/research/r08/paths/${paths[0].id}/rebind`,{data:{media_id:'synthetic'}});
 expect(rejected.status()).toBe(422);
 for(const [i,url] of urls.entries()){
  const event=page.waitForEvent('download');await page.locator(`a[href="${url}"]`).click();
  expect((await event).suggestedFilename()).toBe('manifest.json');
  expect(await(await page.request.get(origin+url)).body()).toEqual(before[i]);
 }
 expect(await page.getByLabel('Anotación R08 JSON').inputValue()).toBe(draft);
 await page.reload();
 await expect(page.getByText(/Histórico: integridad verificada, recálculo actual no disponible/)).toBeVisible();
});
