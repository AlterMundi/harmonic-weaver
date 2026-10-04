import {test,expect} from '@playwright/test';
import {readFile} from 'node:fs/promises';

test('processing profiles persist portably without selections jobs or live edits',async({page})=>{
 test.skip(!process.env.LAB_EVALUATION_PROFILE_URL,'production laboratory required');
 const origin=process.env.LAB_EVALUATION_PROFILE_URL!;
 const errors:string[]=[];page.on('pageerror',e=>errors.push(String(e)));
 let evaluationPosts=0;page.on('request',r=>{if(r.method()==='POST'&&/\/api\/evaluations(?:\/|$)/.test(r.url()))evaluationPosts++});
 await page.goto(origin);const before=await(await page.request.get(`${origin}/api/state`)).json();await page.getByRole('button',{name:'Comparar',exact:true}).click();
 const name='Perfil de procesamiento '+Date.now();await page.getByLabel('Nombre del perfil de procesamiento',{exact:true}).fill(name);
 await page.getByLabel('Reloj de control (Hz)',{exact:true}).fill('90');await page.getByLabel('Historia previa (s)',{exact:true}).fill('3');await page.getByLabel('Máximo de corridas por tanda',{exact:true}).fill('2');
 await page.getByLabel('Generar WAV y estado de osciladores',{exact:true}).check();await page.getByLabel('Frecuencia de muestreo (Hz)',{exact:true}).fill('8000');
 const saved=page.waitForResponse(r=>r.url().endsWith('/api/evaluation-profiles')&&r.request().method()==='POST');await page.getByRole('button',{name:'Guardar perfil de comparación',exact:true}).click();const response=await saved;expect(response.ok(),await response.text()).toBeTruthy();const profile=await response.json();
 expect(Object.keys(profile).sort()).toEqual(['control_hz','id','max_runs_per_invocation','name','pcm','preroll_s','schema_version']);expect(Object.keys(profile.pcm).sort()).toEqual(['block_frames','enabled','sample_rate','shaper_master','tail_s']);
 await page.getByLabel('Reloj de control (Hz)',{exact:true}).fill('60');await page.getByRole('button',{name:'Cargar perfil de comparación',exact:true}).click();await expect(page.getByLabel('Reloj de control (Hz)',{exact:true})).toHaveValue('90');
 const downloading=page.waitForEvent('download');await page.getByRole('button',{name:'Descargar perfil de comparación',exact:true}).click();const bytes=await readFile((await(await downloading).path())!);expect(JSON.parse(bytes.toString())).toEqual(profile);
 await page.reload();await page.getByRole('button',{name:'Comparar',exact:true}).click();await page.getByLabel('Perfil de procesamiento',{exact:true}).selectOption(profile.id);await page.getByRole('button',{name:'Cargar perfil de comparación',exact:true}).click();await expect(page.getByLabel('Máximo de corridas por tanda',{exact:true})).toHaveValue('2');
 await page.getByLabel('Perfil de comparación JSON',{exact:true}).fill(bytes.toString());
 let release!:()=>void;const held=new Promise<void>(resolve=>release=resolve);let requested=false;
 await page.route(`${origin}/api/evaluation-profiles/validate`,async route=>{const result=await route.fetch();requested=true;await held;await route.fulfill({response:result})});
 await page.getByRole('button',{name:'Aplicar JSON de comparación',exact:true}).click();await expect.poll(()=>requested).toBe(true);await page.getByLabel('Reloj de control (Hz)',{exact:true}).fill('120');release();
 await expect(page.getByRole('alert').filter({hasText:'Los ajustes cambiaron durante la carga'})).toBeVisible();await expect(page.getByLabel('Reloj de control (Hz)',{exact:true})).toHaveValue('120');await page.unroute(`${origin}/api/evaluation-profiles/validate`);
 await page.getByRole('button',{name:'Aplicar JSON de comparación',exact:true}).click();await expect(page.getByLabel('Reloj de control (Hz)',{exact:true})).toHaveValue('90');
 const after=await(await page.request.get(`${origin}/api/state`)).json();expect(after.preset).toEqual(before.preset);expect(after.calibration).toEqual(before.calibration);expect(after.source).toEqual(before.source);expect(evaluationPosts).toBe(0);expect(errors).toEqual([]);
});
