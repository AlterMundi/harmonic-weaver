import {test,expect} from '@playwright/test';
test('frozen bodily R04 retains explicit scale missingness portable controls and repeatability',async({page})=>{
 test.skip(!process.env.LAB_R04_FROZEN_BODY_URL,'production fixture with read-only frozen body EVAL required');test.setTimeout(180000);
 const origin=process.env.LAB_R04_FROZEN_BODY_URL!;
 const evaluations=await(await page.request.get(`${origin}/api/evaluations`)).json();expect(evaluations).toHaveLength(1);const eid=evaluations[0].id;
 const report=await(await page.request.get(`${origin}/api/evaluations/${eid}/report`)).json();const source=report.manifest.request.sources[report.manifest.runs[0].source_index];
 expect(source.torso_scale).toBeGreaterThan(0);expect(source.calibration_provenance).toBeTruthy();
 const start=Number(process.env.LAB_R04_BODY_START??source.start_s),end=Number(process.env.LAB_R04_BODY_END??Math.min(source.end_s,start+120));
 const errors:string[]=[];page.on('pageerror',e=>errors.push(String(e)));await page.goto(origin);await page.getByRole('button',{name:'Investigación',exact:true}).click();
 await page.getByRole('combobox',{name:'Comparación corporal R04',exact:true}).selectOption(eid);
 await expect(page.getByRole('combobox',{name:'Corrida corporal R04',exact:true})).toBeVisible();
 await page.getByRole('combobox',{name:'Extremo proximal R04',exact:true}).selectOption('7');await page.getByRole('combobox',{name:'Extremo distal R04',exact:true}).selectOption('9');
 await page.getByLabel('Inicio corporal R04 (s)',{exact:true}).fill(String(start));await page.getByLabel('Fin corporal R04 (s)',{exact:true}).fill(String(end));
 await page.getByLabel('Ruido añadido R04 (desvío)',{exact:true}).fill('.02');await page.getByLabel('Semilla de ruido R04',{exact:true}).fill('17');
 await page.getByRole('button',{name:'Exportar configuración corporal R04',exact:true}).click();
 const preset=page.getByLabel('Configuración corporal R04 JSON',{exact:true});const portable=JSON.parse(await preset.inputValue());expect(Object.keys(portable).sort()).toEqual(['endpoints','schema_version','settings']);expect(portable.settings.perturbation_std).toBe(.02);
 const before=(await(await page.request.get(`${origin}/api/research/r04`)).json()).length;
 await page.getByLabel('Ruido añadido R04 (desvío)',{exact:true}).fill('0');await page.getByRole('button',{name:'Importar configuración corporal R04',exact:true}).click();await expect(page.getByLabel('Ruido añadido R04 (desvío)',{exact:true})).toHaveValue('0.02');
 expect((await(await page.request.get(`${origin}/api/research/r04`)).json()).length).toBe(before);
 const outputs:Buffer[]=[];
 for(let i=0;i<2;i++){
  const accepted=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().endsWith('/api/research/r04/trace'));
  await page.getByRole('button',{name:'Correr R04 con pose congelada',exact:true}).click();const response=await accepted;expect(response.ok(),await response.text()).toBeTruthy();const id=(await response.json()).id;
  const open=page.getByRole('button',{name:`Ver resultado R04 ${id}`,exact:true});await expect(open).toBeVisible({timeout:60000});await open.click();
  await expect(page.getByRole('table',{name:'Resumen R04 pose',exact:true})).toContainText('noisy_endpoints');
  const resultResponse=await page.request.get(`${origin}/api/research/r04/${id}/artifacts/result.json`);expect(resultResponse.ok()).toBeTruthy();outputs.push(await resultResponse.body());const value=await resultResponse.json();
  expect(value.scale).toBe(source.torso_scale);expect(value.provenance.source.person_id).toBe(source.person_id);expect(value.provenance.source.calibration_provenance).toBe(source.calibration_provenance);expect(value.unit).toBe('T/s');
  expect(value.selection).toMatchObject({parent_joint:7,child_joint:9,start_s:start,end_s:end});expect(value.traces.original[0].input_valid).toBe(false);expect(value.traces.original.some((r:any)=>r.relative.state==='observed')).toBe(true);
  expect(value.summaries.pose.common_observations).toBeGreaterThan(0);
  for(const condition of Object.values(value.summaries.pose.conditions) as any[])expect(condition.paired_observations).toBe(value.summaries.pose.common_observations);
  for(const rows of Object.values(value.traces) as any[][]){expect(rows.map(r=>r.time_s)).toEqual(value.traces.original.map((r:any)=>r.time_s));for(const row of rows.filter(r=>!r.input_valid))expect(row.relative.state).toBe('missing')}
  const input=await(await page.request.get(`${origin}/api/research/r04/${id}/artifacts/input.json`)).json();expect(input.scale).toBe(source.torso_scale);expect(input.provenance.source_record).toEqual(report.manifest.source_records[report.manifest.runs[0].source_index]);
 }
 expect(outputs[0].equals(outputs[1])).toBe(true);expect(errors).toEqual([]);
 const state=await(await page.request.get(`${origin}/api/state`)).json();expect(state).toHaveProperty('calibration',null);
});

test('an unscaled frozen body stays blocked instead of inheriting another calibration',async({page})=>{
 test.skip(!process.env.LAB_R04_UNSCALED_BODY_URL,'separate read-only fixture of an unscaled EVAL required');const origin=process.env.LAB_R04_UNSCALED_BODY_URL!;
 const evaluations=await(await page.request.get(`${origin}/api/evaluations`)).json();expect(evaluations).toHaveLength(1);const eid=evaluations[0].id;
 const report=await(await page.request.get(`${origin}/api/evaluations/${eid}/report`)).json();const source=report.manifest.request.sources[report.manifest.runs[0].source_index];expect(source.torso_scale).toBeNull();expect(source.calibration_provenance).toBeFalsy();
 const inventory=await(await page.request.get(`${origin}/api/research/r04`)).json();await page.goto(origin);await page.getByRole('button',{name:'Investigación',exact:true}).click();await page.getByRole('combobox',{name:'Comparación corporal R04',exact:true}).selectOption(eid);
 await expect(page.getByRole('alert').filter({hasText:'Esta fuente no tiene escala'})).toBeVisible();await expect(page.getByRole('button',{name:'Correr R04 con pose congelada',exact:true})).toBeDisabled();
 const rejected=await page.request.post(`${origin}/api/research/r04/trace`,{data:{settings:{},selection:{evaluation_id:eid,run_index:0,parent_joint:7,child_joint:9,start_s:source.start_s,end_s:Math.min(source.end_s,source.start_s+2)}}});expect(rejected.status()).toBe(422);expect((await rejected.json()).detail).toContain('Explicit frozen torso scale');
 expect((await(await page.request.get(`${origin}/api/research/r04`)).json()).length).toBe(inventory.length);
});
