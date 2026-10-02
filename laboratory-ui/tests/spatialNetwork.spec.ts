import {test,expect} from '@playwright/test';
test('spatial import clock configuration conversion and export',async({page})=>{
 test.skip(!process.env.LAB_R09_URL,'isolated fixture required');await page.goto(process.env.LAB_R09_URL!);
 const panel=page.getByRole('region',{name:'Observaciones espaciales R09'});
 const frames=[{source_id:'synthetic',stream_id:'test',sequence:0,source_time_s:0.,available_monotonic_s:1.,timestamp_origin:'pts',width:160,height:120,persons:[{person_id:'slot-1',joints:[{index:0,position:[.5,.2],confidence:.9,state:'observed'}]}]}];
 await panel.getByLabel('Importar JSON local R09').setInputFiles({name:'frames.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(frames))});
 await panel.getByLabel('Slot explícito R09').fill('slot-1');
 await panel.getByLabel('Mapeo de reloj JSON R09').fill(JSON.stringify({source_clock:'pts',common_clock:'session',offset_s:.2,rate:1.,uncertainty_s:.01,method:'declared_assumption'}));
 await panel.getByRole('button',{name:'Procesar observaciones R09'}).click();
 await expect(panel.getByText(/observados 1; sostenidos 0; inferidos 0; faltantes 16/)).toBeVisible();
 const download=page.waitForEvent('download');await panel.getByRole('button',{name:'Exportar resultado R09'}).click();expect((await download).suggestedFilename()).toBe('r09-spatial-result.json');
 await panel.getByText('Resultado espacial R09',{exact:true}).click();
 const raw=await panel.locator('pre').textContent();const result=JSON.parse(raw!);expect(result.common_times_s).toEqual([.2]);
 await panel.getByLabel('Modalidad R09').selectOption('validate');await panel.getByLabel('Observaciones JSON R09').fill(JSON.stringify(result.stream));
 await panel.getByRole('button',{name:'Procesar observaciones R09'}).click();await expect(panel.getByText(/Contrato validado: image_pose/)).toBeVisible();
 await panel.getByLabel('Observaciones JSON R09').fill('{}');await panel.getByRole('button',{name:'Procesar observaciones R09'}).click();await expect(panel.getByRole('alert')).toBeVisible();
});
