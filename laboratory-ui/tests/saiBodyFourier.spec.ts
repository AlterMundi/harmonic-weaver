import {test,expect} from '@playwright/test';
test('explicit source scale preparation and common-support result without live actions',async({page})=>{
 const requests:any[]=[];let complete=false;
 const preparation={longest_short_block:12,short_block_lengths:[12],input_frames:32,retained_frames:30,exclusion_counts:{selected_joint_invalid:2},blocks:[{index:0}]};
 await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname;let value:any=[];
 if(path.endsWith('/r09/sources'))value=[{job_id:'job',effective_device:'cpu',person_ids:['bystander','athlete']}];
 if(path.endsWith('/sai-body-fourier'))value=complete?[{id:'run',status:'complete'}]:[];
 if(route.request().method()==='POST'){const body=route.request().postDataJSON();requests.push({path,body});
  if(path.endsWith('/prepare'))value={preparation,provenance:{generation:'synthetic'}};
  else{complete=true;value={id:'run',status:'complete'}};
 }
 if(path.endsWith('/result.json'))value={preparation,limits:['offline synthetic fixture'],comparison:{results:[{block_index:0,stream_id:'epoch',seed:7,descriptors:{'collective.residual':{common_observed:0,total:30,conditions:{original:{common_mean:null,observed:0},shared:{common_mean:null,observed:0},independent:{common_mean:null,observed:0}}}},spectral_checks:{shared:{power_max_relative_error:0}},geometry:{shared:{segments:{'7-9':{maximum_relative_length_change:.08}}}}}]}};
 await route.fulfill({json:value});});
 await page.goto('/tests/sai_body_harness/');
 await expect(page.getByRole('button',{name:'Correr Fourier corporal',exact:true})).toBeDisabled();
 await page.getByRole('button',{name:'Actualizar fuentes Fourier corporales'}).click();
 await page.getByLabel('Fuente Fourier corporal',{exact:true}).selectOption('job');
 await expect(page.getByRole('button',{name:'Correr Fourier corporal',exact:true})).toBeDisabled();
 await page.getByLabel('Persona Fourier corporal',{exact:true}).selectOption('athlete');
 const config=page.getByLabel('Ajustes Fourier corporal JSON',{exact:true});const initial=JSON.parse(await config.inputValue());expect(initial.scale).toBeNull();
 await config.fill(JSON.stringify({...initial,scale:.26,scale_provenance:'explicit synthetic torso',sample_hz:60}));
 await page.getByRole('button',{name:'Preparar bloques Fourier corporales'}).click();
 await expect(page.getByText('Preparación: 30/32 frames',{exact:false})).toBeVisible();
 await expect(page.getByText('Bloque corto descartado más largo: 12 muestras.',{exact:false})).toBeVisible();
 expect(requests[0].body.person_id).toBe('athlete');expect(requests[0].body.settings.scale).toBe(.26);
 await page.getByRole('button',{name:'Correr Fourier corporal',exact:true}).click();
 await page.getByRole('button',{name:'Abrir Fourier corporal',exact:true}).click();
 await expect(page.getByRole('table',{name:'Medias Fourier corporales comunes'})).toContainText('Sin soporte');
 await expect(page.getByText('Soporte común: 0/30',{exact:true})).toBeVisible();
 expect(requests.map(r=>r.path)).toEqual(['/api/research/sai-body-fourier/prepare','/api/research/sai-body-fourier']);
});


test('source person and import clear only source-specific scale without losing method settings',async({page})=>{
 await page.route('**/api/**',async route=>{const path=new URL(route.request().url()).pathname;
  const value=path.endsWith('/r09/sources')?[{job_id:'one',effective_device:'cpu',person_ids:['a','b']},{job_id:'two',effective_device:'cpu',person_ids:['a','b']}]:path.endsWith('/settings')?route.request().postDataJSON():[];
  await route.fulfill({json:value});
 });
 await page.goto('/tests/sai_body_harness/');
 await page.getByRole('button',{name:'Actualizar fuentes Fourier corporales'}).click();
 const source=page.getByLabel('Fuente Fourier corporal',{exact:true}),person=page.getByLabel('Persona Fourier corporal',{exact:true}),config=page.getByLabel('Ajustes Fourier corporal JSON',{exact:true});
 await source.selectOption('one');await person.selectOption('a');
 const configured={...JSON.parse(await config.inputValue()),scale:.26,scale_provenance:'explicit body a',min_samples:32};
 await config.fill(JSON.stringify(configured));await person.selectOption('b');
 expect(JSON.parse(await config.inputValue())).toMatchObject({scale:null,scale_provenance:'',min_samples:32});
 await config.fill(JSON.stringify(configured));await source.selectOption('two');
 expect(await person.inputValue()).toBe('');
 expect(JSON.parse(await config.inputValue())).toMatchObject({scale:null,scale_provenance:'',min_samples:32});
 await person.selectOption('a');await config.fill('{unfinished');await source.selectOption('one');
 await expect(page.getByRole('alert')).toContainText('Corregí el JSON');
 expect(await source.inputValue()).toBe('two');expect(await person.inputValue()).toBe('a');expect(await config.inputValue()).toBe('{unfinished');
 await config.fill(JSON.stringify(configured));
 await page.getByLabel('Importar ajustes Fourier corporales',{exact:false}).setInputFiles({name:'settings.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(configured))});
 await expect(person).toHaveValue('');
 expect(JSON.parse(await config.inputValue())).toMatchObject({scale:null,scale_provenance:'',min_samples:32});
 await expect(page.getByRole('button',{name:'Correr Fourier corporal',exact:true})).toBeDisabled();
});
