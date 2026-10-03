import {test,expect} from '@playwright/test';
import {readFile} from 'node:fs/promises';

test('R13 quadratic control is portable and repeats over common reserved support',async({page})=>{
 test.skip(!process.env.LAB_R13_QUADRATIC_URL,'production laboratory with real R13 worker required');
 const origin=process.env.LAB_R13_QUADRATIC_URL!;
 const errors:string[]=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(origin);await page.getByRole('button',{name:'Investigación',exact:true}).click();
 await page.getByRole('button',{name:'Cargar recurrencia cuadrática R13',exact:true}).click();
 const toggle=page.getByLabel('Control no lineal: ridge cuadrático R13',{exact:true});await expect(toggle).toBeChecked();
 const downloading=page.waitForEvent('download');await page.getByRole('button',{name:'Guardar configuración portable R13',exact:true}).click();
 const bytes=await readFile((await(await downloading).path())!);const portable=JSON.parse(bytes.toString());
 expect(Object.keys(portable).sort()).toEqual(['kind','reservation','schema_version','settings']);expect(portable.settings.quadratic_control).toBe(true);
 await toggle.uncheck();await page.getByLabel('Importar configuración R13',{exact:true}).setInputFiles({name:'r13-settings.json',mimeType:'application/json',buffer:bytes});await expect(toggle).toBeChecked();
 const accepted=page.waitForResponse(r=>r.url().endsWith('/api/research/r13')&&r.request().method()==='POST');
 await page.getByRole('button',{name:'Correr transferencia R13',exact:true}).click();const response=await accepted;expect(response.ok(),await response.text()).toBeTruthy();const id=(await response.json()).id;
 const table=page.getByRole('table',{name:`Resultados transferencia ${id}`,exact:true});await expect(table).toBeVisible({timeout:20000});await expect(table).toContainText('quadratic_ridge MSE');
 const first=await(await page.request.get(`${origin}/api/research/r13/${id}/artifacts/result.json`)).body();const value=JSON.parse(first.toString());
 expect(value.settings.quadratic_control).toBe(true);expect(value.results[0].common_count).toBe(239);expect(value.results[0].mean_mse.quadratic_ridge).toBeLessThan(1e-12);expect(value.results[0].mean_mse.full_ridge).toBeGreaterThan(.1);
 const repeating=page.waitForResponse(r=>r.url().endsWith(`/${id}/repeat`)&&r.request().method()==='POST');await table.locator('..').getByRole('button',{name:'Repetir corrida R13',exact:true}).click();const repeated=await repeating;expect(repeated.ok()).toBeTruthy();const repeatId=(await repeated.json()).id;
 await expect(page.getByRole('table',{name:`Resultados transferencia ${repeatId}`,exact:true})).toBeVisible({timeout:20000});
 expect(await(await page.request.get(`${origin}/api/research/r13/${repeatId}/artifacts/result.json`)).body()).toEqual(first);
 const state=await(await page.request.get(`${origin}/api/state`)).json();expect(state.preset.voices).toHaveLength(6);expect(state.calibration).toBeNull();expect(state.source.kind).toBeNull();expect(errors).toEqual([]);
});
