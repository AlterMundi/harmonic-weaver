import {test,expect} from '@playwright/test';
test('explicit completed generation and inclusive segment',async({page})=>{
 test.skip(!process.env.LAB_R09_SOURCE_URL,'isolated spatial fixture required');await page.goto(process.env.LAB_R09_SOURCE_URL!);
 const panel=page.getByRole('region',{name:'Observaciones espaciales R09'});
 let inferenceCalls=0;page.on('request',r=>{if(r.method()==='POST'&&r.url().includes('/api/sources/video'))inferenceCalls++;});
 await panel.getByLabel('Modalidad R09').selectOption('source');await panel.getByRole('button',{name:'Actualizar tracking R09'}).click();
 await panel.getByLabel('Tracking completo R09').selectOption('synthetic-spatial');
 const submit=panel.getByRole('button',{name:'Procesar observaciones R09'});await expect(submit).toBeDisabled();
 await panel.getByLabel('Slot explícito R09').fill('slot-1-generation-1');await panel.getByLabel('Fin de segmento R09').fill('.2');await submit.click();
 await expect(panel.getByText(/observados 1; sostenidos 0; inferidos 0; faltantes 33/)).toBeVisible();
 await panel.getByText('Resultado espacial R09',{exact:true}).click();const result=JSON.parse((await panel.locator('pre').textContent())!);
 expect(result.stream.frames.map((f:any)=>f.index)).toEqual([0,2]);expect(result.tracking_provenance.generation).toBe('fixture-generation');expect(result.tracking_provenance).not.toHaveProperty('path');
 await panel.getByLabel('Slot explícito R09').fill('absent');await submit.click();await expect(panel.getByText(/faltantes 34/)).toBeVisible();
 await panel.getByLabel('Fin de segmento R09').fill('2');await submit.click();await expect(panel.getByRole('alert')).toBeVisible();expect(inferenceCalls).toBe(0);
});
