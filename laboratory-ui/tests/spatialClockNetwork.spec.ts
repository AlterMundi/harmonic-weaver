import {test,expect} from '@playwright/test';
import {readFile} from 'node:fs/promises';
test('clock fit exports explicit anchors and clears stale output',async({page})=>{
 test.skip(!process.env.LAB_R09_CLOCK_URL,'isolated fixture required');const url=process.env.LAB_R09_CLOCK_URL!;await page.goto(url);
 const panel=page.getByRole('region',{name:'Ajuste de reloj R09',exact:true});
 const body={source_clock:'camera',common_clock:'session',evidence_id:'synthetic-flashes',anchor_uncertainty_s:.01,anchors:[0,10,20].map(t=>({source_time_s:t,common_time_s:2+1.001*t}))};
 await panel.getByLabel('Marcas de reloj JSON R09').fill(JSON.stringify(body));await panel.getByRole('button',{name:'Ajustar reloj R09',exact:true}).click();
 await expect(panel.getByText(/Desfase: 2 s · tasa: 1.001/)).toBeVisible();
 const download=page.waitForEvent('download');await panel.getByRole('button',{name:'Exportar ajuste reloj R09'}).click();const file=await download;expect(file.suggestedFilename()).toBe('r09-clock-fit.json');
 const result=JSON.parse(await readFile((await file.path())!,'utf8'));expect(result.request).toEqual({...body,validation_anchors:[]});expect(result.source_interval_s).toEqual([0,20]);expect(result.clock.uncertainty_s).toBeCloseTo(.01);
 const attempts:any[]=[];let first=true;await page.route('**/api/research/r09/clock-fits',async route=>{if(route.request().method()!=='POST'){await route.continue();return;}attempts.push(route.request().postDataJSON());if(first){first=false;await route.fetch();await route.abort('failed');}else await route.continue();});
 await panel.getByRole('button',{name:'Guardar ajuste reloj R09'}).click();await expect(panel.getByRole('button',{name:'Recuperar ajuste reloj R09'})).toBeVisible();await page.reload();await panel.getByRole('button',{name:'Recuperar ajuste reloj R09'}).click();expect(attempts).toHaveLength(2);expect(attempts[1]).toEqual(attempts[0]);
 await panel.getByRole('button',{name:'Abrir ajuste reloj R09'}).click();await expect(panel.getByText(/Desfase: 2 s · tasa: 1.001/)).toBeVisible();expect((await(await page.request.get(url+'/api/research/r09/clock-fits')).json())).toHaveLength(1);
 await panel.getByLabel('Marcas de reloj JSON R09').fill(JSON.stringify({...body,evidence_id:''}));await expect(panel.getByRole('button',{name:'Exportar ajuste reloj R09'})).toHaveCount(0);await panel.getByRole('button',{name:'Ajustar reloj R09',exact:true}).click();await expect(panel.getByRole('alert')).toBeVisible();
 expect((await(await page.request.get(url+'/api/research/r09/comparisons')).json())).toHaveLength(0);
});
