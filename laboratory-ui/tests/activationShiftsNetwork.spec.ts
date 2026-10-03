import {test,expect} from '@playwright/test';

test('per-voice circular shifts retain input spectra and portable web configuration',async({page})=>{
 test.skip(!process.env.LAB_R06_SHIFTS_URL,'isolated production UI required');
 const url=process.env.LAB_R06_SHIFTS_URL!;
 await page.goto(url);await page.getByRole('button',{name:'Investigación',exact:true}).click();
 for(const [key,value] of Object.entries({'medium.sample_rate':'8000',excitation_span_s:'.05',tail_s:'.025',event_count:'4'}))await page.getByLabel(`${key} R06`,{exact:true}).fill(value);
 await page.getByRole('checkbox',{name:'Desplazamientos circulares por voz R06',exact:true}).check();
 const shifts=[[0,0,0,0,0,0],[100,100,100,100,100,100],[0,7,11,19,23,29]];
 await page.getByLabel('circular_shift_controls R06',{exact:true}).fill(JSON.stringify(shifts));
 await page.getByRole('button',{name:'Exportar configuración R06',exact:true}).click();
 const text=page.getByLabel('Configuración R06 JSON',{exact:true});await expect(text).not.toHaveValue('');
 expect(JSON.parse(await text.inputValue()).settings.circular_shift_controls).toEqual(shifts);
 await page.getByRole('checkbox',{name:'Desplazamientos circulares por voz R06',exact:true}).uncheck();
 await page.getByRole('button',{name:'Importar configuración R06',exact:true}).click();
 await expect(page.getByLabel('circular_shift_controls R06',{exact:true})).toHaveValue(JSON.stringify(shifts));
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
 const table=page.getByRole('table',{name:'Espectros conservados por desplazamiento R06',exact:true});await expect(table.locator('tbody tr')).toHaveCount(12);
 const report=JSON.parse(reports[1].toString());
 expect(report.circular_shift_controls[1].conditions.rational.spectral_preservation.changed_input_samples).toBe(0);
 for(const c of report.circular_shift_controls)for(const v of Object.values(c.conditions) as any[])expect(v.spectral_preservation.power_max_relative_error).toBeLessThan(1e-12);
 await page.getByLabel('Desplazamiento de traza R06',{exact:true}).selectOption('2');
 await expect(page.getByLabel('Traza R06',{exact:true})).toContainText(`suma ${report.circular_shift_controls[2].conditions.rational.trace[0].sum}`);
});
