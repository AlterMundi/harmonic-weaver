import {test,expect} from '@playwright/test';
for(const paired of [false,true])test(`R05 real network ${paired?'paired mechanisms':'resonators'} preserves presets and repeats PCM`,async({page})=>{
 test.skip(!process.env.LAB_R05_NETWORK_URL,'explicit synthetic pose HTTP fixture required');
 const origin=process.env.LAB_R05_NETWORK_URL!;
 await page.goto(origin);
 const initialJobs=(await (await page.request.get(`${origin}/api/research/r05`)).json()).length;
 await page.getByRole('combobox',{name:/^Comparación R05/}).selectOption({index:1});
 await page.getByRole('combobox',{name:/^Señal R05/}).selectOption('zone.1.speed');
 await expect(page.getByText('Persona congelada:',{exact:false})).toContainText('one');
 await page.getByLabel('resonators.sample_rate R05',{exact:true}).fill('8000');
 await page.getByLabel('excitation.high R05',{exact:true}).fill('.1');
 await page.getByLabel('excitation.low R05',{exact:true}).fill('.02');
 await page.getByLabel('render.tail_s R05',{exact:true}).fill('.1');
 if(paired){
  await page.getByRole('checkbox',{name:'Comparar con mapeo de amplitud R05',exact:true}).check();
  await page.getByLabel('mapping.attack_s R05',{exact:true}).fill('.01');
 }
 await page.getByRole('button',{name:'Exportar configuración R05',exact:true}).click();
 const json=page.getByLabel('Configuración R05 JSON',{exact:true});
 await expect(json).toHaveValue(/sample_rate/);
 const preset=JSON.parse(await json.inputValue());
 expect(Object.keys(preset).sort()).toEqual(paired?['excitation','mapping','render','resonators','schema_version']:['excitation','render','resonators','schema_version']);
 expect(preset.resonators.ratios).toHaveLength(6);
 await page.getByLabel('Inicio R05 (s)',{exact:true}).fill('.3');
 await page.getByLabel('excitation.gain R05',{exact:true}).fill('2');
 await page.getByRole('button',{name:'Importar configuración R05',exact:true}).click();
 await expect(page.getByLabel('excitation.gain R05',{exact:true})).toHaveValue('1');
 await expect(page.getByLabel('Inicio R05 (s)',{exact:true})).toHaveValue(/^(0)?\.3$/);
 await expect(page.getByRole('combobox',{name:/^Señal R05/})).toHaveValue('zone.1.speed');
 expect((await (await page.request.get(`${origin}/api/research/r05`)).json())).toHaveLength(initialJobs);
 const pcm:Buffer[]=[];const mapped:Buffer[]=[];
 for(let i=0;i<2;i++){
  const started=page.waitForResponse(r=>r.url()===`${origin}/api/research/r05` && r.request().method()==='POST');
  await page.getByRole('button',{name:'Correr R05',exact:true}).click();
  const response=await started;expect(response.status()).toBe(200);const ident=(await response.json()).id;
  const file=paired?'excited-sum.wav':'sum.wav';
  const link=page.locator(`a[href="/api/research/r05/${ident}/artifacts/${file}"]`);
  await expect(link).toBeVisible({timeout:10000});
  const manifest=await (await page.request.get(`${origin}/api/research/r05/${ident}/artifacts/manifest.json`)).json();
  expect(manifest.status).toBe('complete');
  if(paired){
   expect(manifest.kind).toBe('mechanism_comparison');
   await page.getByRole('button',{name:`Ver comparación R05 ${ident}`,exact:true}).click();
   const table=page.getByRole('table',{name:'Métricas de mecanismos R05'});
   await expect(table).toContainText('amplitude_mapping');await expect(table).toContainText('common_observed');
   const report=await (await page.request.get(`${origin}/api/research/r05/${ident}/artifacts/result.json`)).json();
   expect(report.clock.total_frames).toBe(14400);
   expect(report.mapping_preparation.mapping).toMatchObject({attack_s:.01,gain:1});
   expect(report.metrics.excited_resonators.common_observed.frames).toBe(report.metrics.amplitude_mapping.common_observed.frames);
   const other=await page.request.get(`${origin}/api/research/r05/${ident}/artifacts/mapped-sum.wav`);
   expect(other.status()).toBe(200);mapped.push(await other.body());
  }else{
   expect(manifest.levels.frames).toBe(14400);
   expect(manifest.preparation.excitation.selection).toMatchObject({start_s:.3,end_s:2});
  }
  const wav=await page.request.get(`${origin}/api/research/r05/${ident}/artifacts/${file}`);
  expect(wav.status()).toBe(200);pcm.push(await wav.body());
  const downloading=page.waitForEvent('download');await link.click();const download=await downloading;
  expect(download.suggestedFilename()).toBe(file);expect(await download.failure()).toBeNull();
 }
 expect(pcm[0].equals(pcm[1])).toBe(true);
 if(paired)expect(mapped[0].equals(mapped[1])).toBe(true);
});
