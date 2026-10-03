import {test,expect} from '@playwright/test';

test('spectral probes export import repeat and follow phase medium seed selection',async({page})=>{
 test.skip(!process.env.LAB_R06_SPECTRUM_URL,'isolated production UI required');
 const url=process.env.LAB_R06_SPECTRUM_URL!;
 await page.goto(url);await page.getByRole('button',{name:'Investigación',exact:true}).click();
 for(const [key,value] of Object.entries({'medium.sample_rate':'8000',excitation_span_s:'.1',tail_s:'.1'}))await page.getByLabel(`${key} R06`,{exact:true}).fill(value);
 await page.getByRole('checkbox',{name:'Sondas espectrales R06',exact:true}).check();
 const config={frequencies_hz:[0,40.4,80.8],window:'tail'};
 await page.getByLabel('spectral_probe R06',{exact:true}).fill(JSON.stringify(config));
 await page.getByRole('checkbox',{name:'Comparar fases de excitación R06',exact:true}).check();
 await page.getByLabel('phase_controls R06',{exact:true}).fill('[[0,1,2,3,4,5]]');
 await page.getByRole('checkbox',{name:'Banco de semillas R06',exact:true}).check();
 await page.getByRole('checkbox',{name:'Comparar medios R06',exact:true}).check();
 await page.getByRole('button',{name:'Exportar configuración R06',exact:true}).click();
 const text=page.getByLabel('Configuración R06 JSON',{exact:true});await expect(text).not.toHaveValue('');
 expect(JSON.parse(await text.inputValue()).settings.spectral_probe).toEqual(config);
 await page.getByLabel('spectral_probe R06',{exact:true}).fill('{"frequencies_hz":[1],"window":"complete"}');
 await page.getByRole('button',{name:'Importar configuración R06',exact:true}).click();
 await expect(page.getByLabel('spectral_probe R06',{exact:true})).toHaveValue(JSON.stringify(config));
 const reports:Buffer[]=[];let firstId='';let selected='';
 for(let i=0;i<2;i++){
  const start=page.getByRole('button',{name:'Correr banco R06',exact:true});await expect(start).toBeEnabled();await start.click();
  await expect.poll(async()=>{const rows=await(await page.request.get(url+'/api/research/r06')).json();return rows.filter((r:any)=>r.status==='complete').length;}).toBe(i+1);
  const jobs=await(await page.request.get(url+'/api/research/r06')).json();selected=jobs.find((r:any)=>r.status==='complete'&&r.id!==firstId).id;
  if(i===0)firstId=selected;
  const response=await page.request.get(url+`/api/research/r06/${selected}/artifacts/result.json`);expect(response.status()).toBe(200);reports.push(await response.body());
 }
 expect(reports[0].equals(reports[1])).toBe(true);
 await page.getByRole('button',{name:`Ver resultado R06 ${selected}`,exact:true}).click();
 const table=page.getByRole('table',{name:'Sondas espectrales R06',exact:true});await expect(table.locator('tbody tr')).toHaveCount(12);
 await page.getByLabel('Fase de resultado R06',{exact:true}).selectOption('0');
 await page.getByLabel('Medio de traza R06',{exact:true}).selectOption('0');
 await page.getByLabel('Semilla de resultado R06',{exact:true}).selectOption('0');
 const report=JSON.parse(reports[1].toString());
 const expected=report.replicates[0].report.phase_controls[0].report.medium_controls[0].conditions.rational.spectral_probe;
 const row=table.locator('tbody tr').filter({has:page.getByRole('cell',{name:'rational',exact:true})}).nth(1);
 expect(Number(await row.locator('td').nth(3).innerText())).toBeCloseTo(expected.rows[1].output_coefficient_squared,12);
 await expect(row.locator('td').nth(4)).toHaveText('tail');await expect(row.locator('td').nth(5)).toHaveText('800');
 expect(expected.rows.every((r:any)=>r.event_coefficient_squared===0)).toBe(true);
});
