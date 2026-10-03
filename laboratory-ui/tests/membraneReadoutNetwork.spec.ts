import {test,expect} from '@playwright/test';
import {readFile} from 'node:fs/promises';
import {join} from 'node:path';

test('sound figures decode on reserved support with portable settings and frozen archive',async({page})=>{
 test.skip(!process.env.LAB_R07_READOUT_URL||!process.env.LAB_R07_READOUT_ROOT,'isolated seeded fixture required');
 const url=process.env.LAB_R07_READOUT_URL!;
 const request=JSON.parse(await readFile(join(process.env.LAB_R07_READOUT_ROOT!,'readout-request.json'),'utf8'));
 const {cases,...config}=request;
 await page.goto(url);await page.getByRole('button',{name:'Investigación',exact:true}).click();
 const panel=page.getByRole('heading',{name:'R07 · Recuperación de atributos reservados',exact:true}).locator('..');
 const preset=page.getByLabel('Preset portable de recuperación R07',{exact:true});
 await expect(preset).not.toHaveValue('');await preset.fill(JSON.stringify(config));
 await page.getByRole('button',{name:'Validar preset de recuperación R07',exact:true}).click();
 expect((await(await page.request.get(url+'/api/research/r07-readout')).json()).length).toBe(0);
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'Exportar preset de recuperación R07',exact:true}).click();
 const saved=JSON.parse(await readFile((await(await download).path())!,'utf8'));expect(saved).toEqual(JSON.parse(await preset.inputValue()));expect(saved.cases).toBeUndefined();
 expect(await page.getByLabel('Figura para recuperar atributos',{exact:true}).locator('option').count()).toBe(7);
 const caseText=page.getByLabel('Casos locales de recuperación R07',{exact:true});await caseText.fill(JSON.stringify(cases));
 const outputs:string[]=[];const ids:string[]=[];
 for(let i=0;i<2;i++){
  const started=page.waitForResponse(r=>r.url()===url+'/api/research/r07-readout'&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Calcular recuperación R07',exact:true}).click();const response=await started;expect(response.status()).toBe(200);const ident=(await response.json()).id;ids.push(ident);
  const row=panel.locator(':scope > div').filter({hasText:ident});await row.getByRole('button',{name:'Ver recuperación R07',exact:true}).click();
  await expect(page.getByLabel('Errores de recuperación R07',{exact:true}).locator('tbody tr')).toHaveCount(7);
  await expect(page.getByLabel('Verificación de recuperación R07',{exact:true})).toContainText('Integridad verificada; sin recalcular');
  const result=await page.request.get(url+`/api/research/r07-readout/${ident}/artifacts/result.json`);outputs.push(await result.text());
 }
 expect(outputs[0]).toBe(outputs[1]);const result=JSON.parse(outputs[0]);expect(result.common_count).toBe(2);
 expect(result.mean_squared_error.rms_full[0]).toBeLessThan(result.mean_squared_error.training_mean[0]/1000);
 expect(result.mean_squared_error.rms_shape[0]).toBeCloseTo(result.mean_squared_error.training_mean[0],12);
 await page.getByRole('button',{name:'Recalcular verificación de recuperación R07',exact:true}).click();
 await expect(page.getByLabel('Verificación de recuperación R07',{exact:true})).toContainText('Recalculado numéricamente con código actual');
 await page.reload();await page.getByRole('button',{name:'Investigación',exact:true}).click();
 await panel.locator(':scope > div').filter({hasText:ids[1]}).getByRole('button',{name:'Ver recuperación R07',exact:true}).click();
 await expect(page.getByLabel('Errores de recuperación R07',{exact:true}).locator('tbody tr')).toHaveCount(7);
 const bad=cases.map((c:any)=>({...c}));bad[bad.length-1].recording_id=bad[0].recording_id;
 await preset.fill(JSON.stringify(config));await caseText.fill(JSON.stringify(bad));await page.getByRole('button',{name:'Calcular recuperación R07',exact:true}).click();
 await expect(panel.getByRole('alert')).toContainText('Reserved recording');
 expect((await(await page.request.get(url+'/api/research/r07-readout')).json()).length).toBe(2);
});
