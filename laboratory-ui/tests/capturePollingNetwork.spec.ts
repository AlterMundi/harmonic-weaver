import {test,expect} from '@playwright/test';

test('capture polling shows failures keeps cached status and resumes without mutations',async({page})=>{
 test.skip(!process.env.LAB_CAPTURE_POLL_URL,'production laboratory API required');
 const origin=process.env.LAB_CAPTURE_POLL_URL!;
 let release!:()=>void;const held=new Promise<void>(resolve=>release=resolve);
 let hold=true,fail=false,posts=0,captureRequests=0;
 let holdExports=false,exportsHeldRequests=0,releaseExports!:()=>void;
 const exportsHeld=new Promise<void>(resolve=>releaseExports=resolve);
 const errors:string[]=[];page.on('pageerror',e=>errors.push(String(e)));
 page.on('request',r=>{if(r.method()==='POST')posts++});
 await page.route(`${origin}/api/captures`,async route=>{
  captureRequests++;if(hold)await held;
  if(fail)await route.fulfill({status:503,contentType:'application/json',body:'{"detail":"capture inventory unavailable"}'});
  else await route.continue();
 });
 for(const path of ['capture-exports','capture-exports/jobs','capture-recovery'])await page.route(`${origin}/api/${path}`,async route=>{
  if(path==='capture-exports/jobs'&&holdExports){exportsHeldRequests++;await exportsHeld}
  if(fail)await route.fulfill({status:503,contentType:'application/json',body:'{"detail":"inventory unavailable"}'});
  else await route.continue();
 });
 await page.goto(origin);await page.getByRole('button',{name:'Captura',exact:true}).click();
 await expect.poll(()=>captureRequests).toBe(1);await expect(page.getByRole('button',{name:'Iniciar captura',exact:true})).toBeDisabled();
 await expect(page.getByRole('status').filter({hasText:'Esperando inventario de capturas'})).toBeVisible();
 await page.waitForTimeout(1150);expect(captureRequests).toBe(1);
 hold=false;release();await expect(page.getByRole('button',{name:'Iniciar captura',exact:true})).toBeEnabled();
 fail=true;holdExports=true;
 for(const phrase of ['No se pudo actualizar el inventario de capturas','No se pudo actualizar las exportaciones','No se pudo actualizar la recuperación'])await expect(page.getByRole('alert').filter({hasText:phrase})).toBeVisible();
 await expect(page.getByRole('button',{name:'Iniciar captura',exact:true})).toBeDisabled();
 await expect(page.getByText('Exportación: idle', {exact:false})).toBeVisible();
 await expect.poll(()=>exportsHeldRequests).toBe(1);
 await page.waitForTimeout(1150);expect(exportsHeldRequests).toBe(1);
 fail=false;holdExports=false;releaseExports();
 await expect(page.getByRole('alert').filter({hasText:'No se pudo actualizar'})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Iniciar captura',exact:true})).toBeEnabled();
 expect(posts).toBe(0);expect(errors).toEqual([]);
});
