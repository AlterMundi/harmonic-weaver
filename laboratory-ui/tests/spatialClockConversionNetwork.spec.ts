import {test,expect} from '@playwright/test';
import {readFile} from 'node:fs/promises';
test('clock conversion resolves two IDs and recovers after reload',async({page})=>{
 test.skip(!process.env.LAB_R09_CLOCK_CONVERSION_URL,'isolated fixture required');const url=process.env.LAB_R09_CLOCK_CONVERSION_URL!;
 const stream={source_id:'synthetic',subject_slot:'slot',provider:'monocular_3d',dimensions:3,coordinate_frame:'model',units:'model_units',clock:{source_clock:'camera',common_clock:'old',offset_s:0,rate:1,uncertainty_s:0,method:'declared_assumption'},frames:[{index:0,source_time_s:0,points:[{label:'hand',state:'inferred',position:[.1,.2,.3]}]}]};
 const conversion=await(await page.request.post(url+'/api/research/r09/conversions',{data:{stream}})).json();
 const fit={source_clock:'camera',common_clock:'session',evidence_id:'synthetic',anchor_uncertainty_s:.01,anchors:[0,10,20].map(t=>({source_time_s:t,common_time_s:2+1.001*t}))};
 const clock=await(await page.request.post(url+'/api/research/r09/clock-fits',{data:{fit}})).json();
 await page.goto(url);const panel=page.getByRole('region',{name:'Guardar conversión con reloj R09',exact:true});await panel.getByRole('button',{name:'Actualizar conversiones para reloj R09'}).click();await panel.getByLabel('Conversión original para reloj R09').selectOption(conversion.id);await panel.getByLabel('Ajuste para guardar conversión R09').selectOption(clock.id);
 const attempts:any[]=[];let first=true;await page.route('**/api/research/r09/clock-conversions',async route=>{attempts.push(route.request().postDataJSON());if(first){first=false;await route.fetch();await route.abort('failed');}else await route.continue();});
 await panel.getByRole('button',{name:'Guardar conversión con reloj R09',exact:true}).click();await expect(panel.getByRole('button',{name:'Recuperar conversión con reloj R09'})).toBeVisible();await page.reload();await panel.getByRole('button',{name:'Recuperar conversión con reloj R09'}).click();expect(attempts).toHaveLength(2);expect(attempts[1]).toEqual(attempts[0]);await expect(panel.getByText(/Conversión con reloj guardada:/)).toBeVisible();
 const download=page.waitForEvent('download');await panel.getByRole('link',{name:'result.json',exact:true}).click();const result=JSON.parse(await readFile((await(await download).path())!,'utf8'));
 expect(result.clock_application.conversion.id).toBe(conversion.id);expect(result.clock_application.clock_fit.id).toBe(clock.id);expect(result.clock_application.original_stream.frames).toEqual(result.stream.frames);expect(result.stream.clock.offset_s).toBe(2);expect(result.clock_application.original_stream.clock.offset_s).toBe(0);
 const rows=await(await page.request.get(url+'/api/research/r09/conversions')).json();expect(rows).toHaveLength(2);
});
