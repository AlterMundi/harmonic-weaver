import {test,expect} from '@playwright/test';
test('R07 transfer portable preset real computation repeat and restore',async({page})=>{
 test.skip(!process.env.LAB_R07_NETWORK_URL,'isolated HTTP fixture required');
 const origin=process.env.LAB_R07_NETWORK_URL!;
 await page.goto(origin);
 const text=page.getByLabel('Configuración portable de transferencia R07');
 await expect(text).not.toHaveValue('');
 const config=JSON.parse(await text.inputValue());
 config.settings.frequencies_hz=[0,40.4];config.settings.x=[0,.3];config.settings.y=[.5,.4];
 config.settings.resolutions=[{modes_x:2,modes_y:2},{modes_x:4,modes_y:4}];
 await text.fill(JSON.stringify(config));
 await page.getByRole('button',{name:'Validar preset de transferencia R07',exact:true}).click();
 await expect.poll(async()=>JSON.parse(await text.inputValue()).settings.x).toEqual([0,.3]);
 expect(await(await page.request.get(`${origin}/api/research/r07-transfer`)).json()).toEqual([]);
 for(let i=0;i<2;i++){
  await page.getByRole('button',{name:'Calcular transferencia R07',exact:true}).click();
  await expect(page.getByRole('button',{name:'Ver transferencia R07',exact:true})).toHaveCount(i+1);
 }
 // Read both persisted jobs directly: inventory order is UUID order.
 const jobs=await(await page.request.get(`${origin}/api/research/r07-transfer`)).json();
 const a=await(await page.request.get(`${origin}/api/research/r07-transfer/${jobs[0].id}/artifacts/result.json`)).body();
 const b=await(await page.request.get(`${origin}/api/research/r07-transfer/${jobs[1].id}/artifacts/result.json`)).body();
 expect(a).toEqual(b);
 await page.getByRole('button',{name:'Ver transferencia R07',exact:true}).first().click();
 await expect(page.locator('table tbody tr')).toHaveCount(8);
 await page.reload();
 await expect(page.getByRole('button',{name:'Ver transferencia R07',exact:true})).toHaveCount(2);
 await page.getByRole('button',{name:'Ver transferencia R07',exact:true}).first().click();
 await expect(page.locator('table tbody tr')).toHaveCount(8);
});
