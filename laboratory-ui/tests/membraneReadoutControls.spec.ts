import {test,expect} from '@playwright/test';
import {execFileSync} from 'node:child_process';
import {resolve} from 'node:path';

test('R07 direct controls, archive recovery and case editing preserve portable boundaries',async({page})=>{
 const root=resolve(process.cwd(),'..');
 const defaults=JSON.parse(execFileSync(resolve(root,'.venv/bin/python'),['-c',
  'import json; from harmonic_weaver.lab.research.membrane_readout import Config; print(json.dumps(Config().model_dump()))'],{cwd:root,encoding:'utf8'}));
 const profile={signal_ids:['zone.1.speed'],method:'mean',min_observations:2,min_observed_fraction:1,max_gap_s:.1};
 const cases=Array.from({length:5},(_,i)=>({id:`case-${i+1}`,projection_run_id:'b'.repeat(32),role:i<3?'train':'test',recording_id:'fixture',subject_group:'fixture',targets:[i],computed_label:profile}));
 const restored={...defaults,reservation:'within_take',attribute_ids:['mean:zone.1.speed'],attribute_units:['T/s'],label_settings:profile,cases};
 const bundle=execFileSync(resolve('node_modules/.bin/esbuild'),['--bundle','--format=esm','--jsx=automatic','--loader=tsx','--minify'],{encoding:'utf8',maxBuffer:8*1024*1024,input:`
 import React from 'react';import {createRoot} from 'react-dom/client';import {MembraneReadoutPanel} from './src/MembraneReadoutPanel';
 createRoot(document.getElementById('root')).render(<MembraneReadoutPanel api={window.fixtureApi}/>);`});
 const errors:string[]=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.route('**/*',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path==='/fixture.js'){await route.fulfill({contentType:'application/javascript',body:bundle});return;}
  if(path!=='/'){await route.abort();return;}
  await route.fulfill({contentType:'text/html',body:`<div id="root"></div><script>
  window.writes=[];window.fixtureApi=async(path,body)=>{
   if(body){window.writes.push({path,body});if(path.endsWith('/configuration'))return {...${JSON.stringify(defaults)},...body};return {id:'result'};}
   if(path==='research/r07')return [{id:'${'b'.repeat(32)}',status:'complete'}];
   if(path==='research/r07-readout')return [{id:'${'a'.repeat(32)}'}];
   if(path.endsWith('/request'))return ${JSON.stringify(restored)};
   throw Error('Unexpected '+path);
  };</script><script type="module" src="/fixture.js"></script>`});
 });
 await page.goto('/');
 await page.getByLabel('Regularización R07',{exact:true}).fill('.7');
 await page.getByLabel('Reserva R07',{exact:true}).selectOption('subject');
 await page.getByLabel('Normalización R07',{exact:true}).selectOption('center_train');
 let config=JSON.parse(await page.getByLabel('Preset portable de recuperación R07',{exact:true}).inputValue());
 expect(config.settings.ridge).toBe(.7);expect(config.reservation).toBe('subject');expect(config).not.toHaveProperty('cases');
 await page.getByLabel('Resumen de etiqueta R07',{exact:true}).selectOption('rms');
 expect(JSON.parse(await page.getByLabel('Preset portable de recuperación R07',{exact:true}).inputValue())).not.toHaveProperty('label_settings');
 await page.getByRole('button',{name:'Recuperar configuración y casos R07',exact:true}).click();
 await expect(page.getByLabel('Reserva R07',{exact:true})).toHaveValue('within_take');
 await expect(page.getByLabel('Regularización R07',{exact:true})).toHaveValue('0.1');
 await expect(page.getByLabel('Selección de casos R07').locator('tbody tr')).toHaveCount(5);
 config=JSON.parse(await page.getByLabel('Preset portable de recuperación R07',{exact:true}).inputValue());
 expect(config).not.toHaveProperty('cases');expect(config.label_settings).toEqual(profile);
 await page.getByLabel('Atributos declarados R07',{exact:true}).fill('[2]');
 await page.getByLabel('Resumen de etiqueta R07',{exact:true}).selectOption('rms');
 await expect(page.getByLabel('Atributos declarados R07',{exact:true})).toHaveValue('');
 await page.getByLabel('Cobertura mínima R07',{exact:true}).fill('.95');
 const labels=JSON.parse(await page.getByLabel('Perfil portable de etiquetas R07',{exact:true}).inputValue());
 expect(labels.method).toBe('rms');expect(labels.min_observed_fraction).toBe(.95);
 expect(JSON.parse(await page.getByLabel('Preset portable de recuperación R07',{exact:true}).inputValue()).label_settings).toEqual(labels);
 await page.getByRole('button',{name:'Quitar caso case-1',exact:true}).click();
 await page.getByLabel('Rol case-2',{exact:true}).selectOption('test');
 await page.getByLabel('Figura para recuperar atributos',{exact:true}).selectOption('b'.repeat(32));
 await page.getByLabel('Grabación declarada R07',{exact:true}).fill('fixture');
 await page.getByLabel('Grupo corporal declarado R07',{exact:true}).fill('fixture');
 await page.getByLabel('Atributos declarados R07',{exact:true}).fill('[2]');
 await page.getByRole('button',{name:'Agregar caso de recuperación R07',exact:true}).click();
 const selected=JSON.parse(await page.getByLabel('Casos locales de recuperación R07',{exact:true}).inputValue());
 expect(selected).toHaveLength(5);expect(new Set(selected.map((c:any)=>c.id)).size).toBe(5);
 expect(selected.find((c:any)=>c.id==='case-2').role).toBe('test');
 await page.getByLabel('Casos locales de recuperación R07',{exact:true}).fill('[null]');
 await expect(page.getByLabel('Selección de casos R07')).toHaveCount(0);
 expect(await page.evaluate(()=>(window as any).writes.every((w:any)=>w.path.startsWith('research/r07-readout')))).toBe(true);
 expect(errors).toEqual([]);
});
