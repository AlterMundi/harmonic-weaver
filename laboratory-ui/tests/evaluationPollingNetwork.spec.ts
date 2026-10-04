import {test,expect} from '@playwright/test';

test('evaluation failures retain known progress and guard new calculations',async({page})=>{
 test.skip(!process.env.LAB_EVALUATION_POLL_URL,'production laboratory required');
 const origin=process.env.LAB_EVALUATION_POLL_URL!;
 let release!:()=>void;const held=new Promise<void>(resolve=>release=resolve);
 let hold=true,fail=false,requests=0,posts=0,status='partial';
 const errors:string[]=[];page.on('pageerror',e=>errors.push(String(e)));page.on('request',r=>{if(r.method()==='POST')posts++});
 // Declared UI inventory fixtures: no worker/run or private source is created.
 await page.route(`${origin}/api/evaluations`,async route=>{
  requests++;if(hold)await held;
  if(fail)await route.fulfill({status:503,contentType:'application/json',body:'{"detail":"evaluation inventory unavailable"}'});
  else await route.fulfill({contentType:'application/json',body:JSON.stringify([{id:'declared-ui-job',status,completed_runs:2,total_runs:4,resume_supported:status==='partial',repeat_supported:true}])});
 });
 await page.goto(origin);await page.getByRole('button',{name:'Comparar',exact:true}).click();
 await expect.poll(()=>requests).toBe(1);await expect(page.getByRole('status').filter({hasText:'Esperando inventario de comparaciones'})).toBeVisible();
 await page.waitForTimeout(1650);expect(requests).toBe(1);hold=false;release();
 const resume=page.getByRole('button',{name:'Continuar comparación congelada',exact:true});const repeat=page.getByRole('button',{name:'Repetir configuración congelada',exact:true});
 await expect(resume).toBeEnabled();await expect(repeat).toBeEnabled();
 fail=true;await expect(page.getByRole('alert').filter({hasText:'No se pudo actualizar las comparaciones'})).toBeVisible();
 await expect(resume).toBeDisabled();await expect(repeat).toBeDisabled();await expect(page.getByText('partial · 2/4 corridas',{exact:false})).toBeVisible();
 fail=false;status='running';const cancel=page.getByRole('button',{name:'Cancelar comparación',exact:true});await expect(cancel).toBeEnabled();
 fail=true;await expect(page.getByRole('alert').filter({hasText:'No se pudo actualizar las comparaciones'})).toBeVisible();await expect(cancel).toBeEnabled();
 fail=false;status='partial';await expect(resume).toBeEnabled();await expect(page.getByRole('alert').filter({hasText:'No se pudo actualizar las comparaciones'})).toHaveCount(0);
 expect(posts).toBe(0);expect(errors).toEqual([]);
});
