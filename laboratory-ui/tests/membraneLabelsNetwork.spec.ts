import {test,expect} from '@playwright/test';
import {readFile} from 'node:fs/promises';
import {join} from 'node:path';

test('verified EVAL labels stay downstream of figures and survive portable export and freezing',async({page})=>{
 test.skip(!process.env.LAB_R07_LABEL_URL||!process.env.LAB_R07_LABEL_ROOT,'isolated seeded fixture required');
 const url=process.env.LAB_R07_LABEL_URL!;
 const fixture=JSON.parse(await readFile(join(process.env.LAB_R07_LABEL_ROOT!,'label-fixture.json'),'utf8'));
 await page.goto(url);await page.getByRole('button',{name:'Investigación',exact:true}).click();
 const panel=page.getByRole('heading',{name:'R07 · Recuperación de atributos reservados',exact:true}).locator('..');
 const preset=page.getByLabel('Preset portable de recuperación R07',{exact:true});
 await expect(preset).not.toHaveValue('');
 const config=JSON.parse(await preset.inputValue());config.reservation='within_take';await preset.fill(JSON.stringify(config));
 const select=page.getByLabel('Figura para recuperar atributos',{exact:true});
 let releaseFirst!:()=>void;const firstGate=new Promise<void>(resolve=>{releaseFirst=resolve;});let first=true;
 await page.route('**/api/research/r07-readout/label',async route=>{const response=await route.fetch();if(first){first=false;await firstGate;}await route.fulfill({response});});
 const figures=new Map<string,string>();
 for(let i=0;i<fixture.projection_ids.length;i++){
  const ident=fixture.projection_ids[i];figures.set(ident,await(await page.request.get(url+`/api/research/r07/${ident}/artifacts/result.json`)).text());
  await select.selectOption(ident);
  if(i===0){
   await page.getByRole('button',{name:'Cargar señales para etiquetas R07',exact:true}).click();
   await page.getByLabel('Señal para etiqueta R07',{exact:true}).selectOption('zone.1.speed');
   await page.getByRole('button',{name:'Agregar señal a etiquetas R07',exact:true}).click();
  }
  await page.getByRole('button',{name:'Calcular atributos desde EVAL R07',exact:true}).click();
  if(i===0){await expect(select).toBeDisabled();await expect(preset).toBeDisabled();releaseFirst();}
  await expect(page.getByLabel('Cobertura de etiquetas R07',{exact:true})).toContainText('fracción 1');
  expect(JSON.parse(await preset.inputValue()).attribute_units).toEqual(['T/s']);
  await page.getByLabel('Rol del caso R07',{exact:true}).selectOption(i<3?'train':'test');
  await page.getByLabel('Grabación declarada R07',{exact:true}).fill('synthetic-same-take');
  await page.getByLabel('Grupo corporal declarado R07',{exact:true}).fill('synthetic');
  await page.getByRole('button',{name:'Agregar caso de recuperación R07',exact:true}).click();
 }
 const cases=JSON.parse(await page.getByLabel('Casos locales de recuperación R07',{exact:true}).inputValue());
 expect(cases).toHaveLength(6);expect(cases.every((c:any)=>c.computed_label.signal_ids[0]==='zone.1.speed')).toBe(true);
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'Exportar preset de recuperación R07',exact:true}).click();
 const exported=JSON.parse(await readFile((await(await download).path())!,'utf8'));expect(exported.label_settings.signal_ids).toEqual(['zone.1.speed']);expect(exported.cases).toBeUndefined();
 const started=page.waitForResponse(r=>r.url()===url+'/api/research/r07-readout'&&r.request().method()==='POST');
 await page.getByRole('button',{name:'Calcular recuperación R07',exact:true}).click();const response=await started;expect(response.status()).toBe(200);const id=(await response.json()).id;
 await panel.locator(':scope > div').filter({hasText:id}).getByRole('button',{name:'Ver recuperación R07',exact:true}).click();
 await expect(page.getByLabel('Errores de recuperación R07',{exact:true})).toContainText('mean:zone.1.speed');
 const dataset=await(await page.request.get(url+`/api/research/r07-readout/${id}/artifacts/dataset.json`)).json();
 expect(dataset.cases.every((c:any)=>c.computed_label.provenance.evaluation_id===fixture.evaluation_id)).toBe(true);
 for(const [ident,before] of figures)expect(await(await page.request.get(url+`/api/research/r07/${ident}/artifacts/result.json`)).text()).toBe(before);
 // Editing a computed value makes it explicitly manual rather than retaining a false derived-label claim.
 await page.getByLabel('Atributos declarados R07',{exact:true}).fill('[99]');
 await expect(page.getByLabel('Cobertura de etiquetas R07',{exact:true})).toHaveCount(0);
 await page.reload();await page.getByRole('button',{name:'Investigación',exact:true}).click();
 await panel.locator(':scope > div').filter({hasText:id}).getByRole('button',{name:'Ver recuperación R07',exact:true}).click();
 await expect(page.getByLabel('Errores de recuperación R07',{exact:true})).toContainText('T/s');
});
