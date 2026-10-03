import {test,expect} from '@playwright/test';

test('phase controls portable config real worker and trace selectors stay aligned',async({page})=>{
 test.skip(!process.env.LAB_R06_PHASE_URL,'isolated production UI required');
 const url=process.env.LAB_R06_PHASE_URL!;
 await page.goto(url);await page.getByRole('button',{name:'Investigación',exact:true}).click();
 await page.getByLabel('medium.sample_rate R06',{exact:true}).fill('8000');
 await page.getByLabel('excitation_span_s R06',{exact:true}).fill('.1');
 await page.getByLabel('tail_s R06',{exact:true}).fill('.1');
 await page.getByRole('checkbox',{name:'Comparar fases de excitación R06',exact:true}).check();
 const phases=[[0,0,0,0,0,0],[0,1,2,3,4,5]];
 await page.getByLabel('phase_controls R06',{exact:true}).fill(JSON.stringify(phases));
 await page.getByRole('checkbox',{name:'Banco de semillas R06',exact:true}).check();
 await page.getByRole('checkbox',{name:'Comparar medios R06',exact:true}).check();
 await page.getByRole('button',{name:'Exportar configuración R06',exact:true}).click();
 const text=page.getByLabel('Configuración R06 JSON',{exact:true});
 await expect(text).not.toHaveValue('');
 const frozen=JSON.parse(await text.inputValue());expect(frozen.settings.phase_controls).toEqual(phases);
 await page.getByLabel('phase_controls R06',{exact:true}).fill('[[1,1,1,1,1,1]]');
 await page.getByRole('button',{name:'Importar configuración R06',exact:true}).click();
 await expect(page.getByLabel('phase_controls R06',{exact:true})).toHaveValue(JSON.stringify(phases));
 const reports:Buffer[]=[];let firstId='';
 for(let i=0;i<2;i++){
  await expect(page.getByRole('button',{name:'Correr banco R06',exact:true})).toBeEnabled();
  await page.getByRole('button',{name:'Correr banco R06',exact:true}).click();
  await expect.poll(async()=>{const rows=await(await page.request.get(url+'/api/research/r06')).json();return rows.filter((r:any)=>r.status==='complete').length;}).toBe(i+1);
  const jobs=await(await page.request.get(url+'/api/research/r06')).json();
  const job=jobs.filter((r:any)=>r.status==='complete').sort((a:any,b:any)=>a.id.localeCompare(b.id));
  // Select a result not previously fetched, independent of UUID sorting.
  const ident=i===0?job[0].id:job.find((r:any)=>r.id!==firstId)!.id;
  if(i===0)firstId=ident;
  const response=await page.request.get(url+`/api/research/r06/${ident}/artifacts/result.json`);
  expect(response.status()).toBe(200);reports.push(await response.body());
  await page.getByRole('button',{name:`Ver resultado R06 ${ident}`,exact:true}).click();
 }
 expect(reports[0].equals(reports[1])).toBe(true);
 const report=JSON.parse(reports[0].toString());
 expect(report.phase_controls[0].report.conditions).toEqual(report.conditions);
 await expect(page.getByRole('table',{name:'Contraste de fases R06',exact:true}).locator('tbody tr')).toHaveCount(8);
 await page.getByLabel('Fase de resultado R06',{exact:true}).selectOption('1');
 const row=page.getByRole('table',{name:'Comparación R06',exact:true}).locator('tbody tr').filter({has:page.getByRole('cell',{name:'phi',exact:true})});
 expect(Number(await row.locator('td').nth(2).innerText())).toBeCloseTo(report.phase_controls[1].report.conditions.phi.metrics.rms,12);
 await page.getByLabel('Medio de traza R06',{exact:true}).selectOption('0');
 await page.getByLabel('Semilla de resultado R06',{exact:true}).selectOption('0');
 await expect(page.getByText('Resultado congelado de semilla 18',{exact:false})).toBeVisible();
 await expect(page.getByLabel('Fase de resultado R06',{exact:true})).toHaveValue('1');
 await expect(page.getByLabel('Traza R06',{exact:true})).toBeVisible();
});
