import {test,expect} from '@playwright/test';
import {execFileSync} from 'node:child_process';
import {resolve} from 'node:path';

test('R07 Shaper selection and stereo preset stay separate from live controls',async({page})=>{
 const root=resolve(process.cwd(),'..');
 const defaults=JSON.parse(execFileSync(resolve(root,'.venv/bin/python'),['-c',
  'import json; from harmonic_weaver.lab.app import MembraneConfig; print(json.dumps(MembraneConfig().model_dump()))'],{cwd:root,encoding:'utf8'}));
 const bundle=execFileSync(resolve('node_modules/.bin/esbuild'),['--bundle','--format=esm','--jsx=automatic','--loader=tsx','--minify'],{encoding:'utf8',maxBuffer:8*1024*1024,input:`
 import React from 'react';import {createRoot} from 'react-dom/client';import {MembranePanel} from './src/MembranePanel';
 createRoot(document.getElementById('root')).render(<MembranePanel api={window.fixtureApi}/>);`});
 const errors:string[]=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.route('**/*',async route=>{
  const path=new URL(route.request().url()).pathname;
  if(path==='/fixture.js'){await route.fulfill({contentType:'application/javascript',body:bundle});return;}
  if(path!=='/'){await route.abort();return;}
  await route.fulfill({contentType:'text/html',body:`<div id="root"></div><script>
  window.writes=[];window.fixtureApi=async(path,body)=>{
   if(body){window.writes.push({path,body});if(path.endsWith('/configuration'))return {...${JSON.stringify(defaults)},...body};return {id:'job'};}
   if(path==='research/r05')return [{id:'r05',status:'complete'}];
   if(path==='research/r07')return [];
   if(path==='evaluations')return [{id:'${'a'.repeat(32)}',status:'complete'}];
   if(path.includes('/report'))return {manifest:{runs:[{preset_id:'reference',source_index:0,pcm:{settings:{sample_rate:8000},samples:16000}}]}};
   throw Error('Unexpected '+path);
  };</script><script type="module" src="/fixture.js"></script>`});
 });
 await page.goto('/');
 await page.getByLabel('Origen de audio R07').selectOption('evaluation_shaper');
 await page.getByLabel('Evaluación Shaper R07').selectOption('a'.repeat(32));
 await page.getByLabel('Corrida Shaper R07').selectOption('0');
 await expect(page.getByLabel('R07 sample_rate',{exact:true})).toHaveValue('8000');
 await page.getByLabel('Reducción estéreo R07').selectOption('right');
 await page.getByRole('button',{name:'Exportar configuración R07',exact:true}).click();
 const portable=JSON.parse(await page.getByLabel('Preset portable R07').inputValue());
 expect(portable.settings.stereo_mix).toBe('right');expect(portable).not.toHaveProperty('evaluation_id');
 await page.getByRole('button',{name:'Calcular membrana R07',exact:true}).click();
 const writes=await page.evaluate(()=>(window as any).writes);
 const start=writes.find((w:any)=>w.path==='research/r07/from-evaluation');
 expect(start.body.evaluation_id).toBe('a'.repeat(32));expect(start.body.run_index).toBe(0);
 expect(start.body.settings.arm).toBe('single');expect(start.body.settings.stereo_mix).toBe('right');
 expect(writes.every((w:any)=>w.path.startsWith('research/r07'))).toBe(true);
 await page.getByLabel('Origen de audio R07').selectOption('r05');
 await expect(page.getByLabel('Fuente R05 para R07')).toBeVisible();
 expect(errors).toEqual([]);
});
