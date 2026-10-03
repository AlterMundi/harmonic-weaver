import {test,expect} from '@playwright/test';
import {readFile} from 'node:fs/promises';
test('resolved R05 stimulus preview pins hashes and save recovers',async({page})=>{
 test.skip(!process.env.LAB_R10_SOURCE_URL,'isolated experience-stimulus fixture required');const url=process.env.LAB_R10_SOURCE_URL!;await page.goto(url);
 const panel=page.getByRole('region',{name:'Estímulos R05 para R10',exact:true});
 await panel.getByLabel('Selección R05 JSON R10').fill(JSON.stringify({config:{},participant_slot:'synthetic-slot',role:'observer',order_index:0,stimuli:[]}));
 await panel.getByRole('button',{name:'Actualizar estímulos R05 para R10'}).click();await panel.getByLabel('Corrida R05 para R10').selectOption('b'.repeat(32));await panel.getByRole('button',{name:'Añadir estímulo R05 al protocolo'}).click();await panel.getByRole('button',{name:'Preparar estímulos resueltos R10'}).click();await expect(panel.getByText(/1 estímulos resueltos · 3 ensayos/)).toBeVisible();
 expect((await(await page.request.get(url+'/api/research/r10/protocols')).json())).toHaveLength(0);
 const attempts:any[]=[];let first=true;await page.route('**/api/research/r10/r05-protocols',async route=>{attempts.push(route.request().postDataJSON());if(first){first=false;await route.fetch();await route.abort('failed');}else await route.continue();});
 await panel.getByRole('button',{name:'Guardar protocolo R05 R10',exact:true}).click();await expect(panel.getByRole('button',{name:'Recuperar protocolo R05 R10'})).toBeVisible();await page.reload();await panel.getByRole('button',{name:'Recuperar protocolo R05 R10'}).click();expect(attempts).toHaveLength(2);expect(attempts[1]).toEqual(attempts[0]);expect(attempts[0].expected_sources[0].pcm_sha256).toMatch(/^[a-f0-9]{64}$/);
 const parent=page.getByRole('region',{name:'Protocolo de experiencia R10',exact:true});await parent.getByRole('button',{name:'Abrir protocolo congelado R10'}).click();await expect(parent.getByRole('table',{name:'Orden de ensayos R10'}).locator('tbody tr')).toHaveCount(3);
 const download=page.waitForEvent('download');await parent.getByRole('link',{name:'result.json',exact:true}).click();const result=JSON.parse(await readFile((await(await download).path())!,'utf8'));expect(result.sources[0].r05_id).toBe('b'.repeat(32));expect(result.sources[0].source_start_s).toBe(.3);expect(result.sources[0].source_end_s).toBe(1.5);expect(result.sources[0].pcm_sha256).toBe(attempts[0].expected_sources[0].pcm_sha256);
 expect((await(await page.request.get(url+'/api/research/r10/protocols')).json())).toHaveLength(1);
});
