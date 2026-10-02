import {test,expect} from '@playwright/test';
test('R08 cancel web preparation terminates confirmed live process and allows retry',async({page})=>{
 test.skip(!process.env.LAB_R08_CANCEL_URL,'slow-first-probe isolated fixture required');
 const origin=process.env.LAB_R08_CANCEL_URL!;
 await page.goto(origin);
 await page.getByLabel('Video de biblioteca R08').selectOption('synthetic');
 await page.getByRole('button',{name:'Preparar anotación R08',exact:true}).click();
 await expect.poll(async()=> (await(await page.request.get(`${origin}/test/decode-live`)).json()).live).toBe(true);
 await expect(page.getByText('Lectura R08: running',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Cancelar preparación R08',exact:true}).click();
 await expect(page.getByText('Lectura R08: cancelled',{exact:true})).toBeVisible();
 await expect.poll(async()=> (await(await page.request.get(`${origin}/test/decode-live`)).json()).live).toBe(false);
 await expect(page.getByLabel('Anotación R08 JSON')).toHaveValue('');
 expect(await(await page.request.get(`${origin}/api/research/r08`)).json()).toEqual([]);
 await page.getByRole('button',{name:'Preparar anotación R08',exact:true}).click();
 await expect(page.getByText(/Imagen decodificada/)).toBeVisible();
 await expect(page.getByText('Lectura R08: complete',{exact:true})).toBeVisible();
});
