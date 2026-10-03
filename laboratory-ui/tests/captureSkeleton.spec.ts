import {test,expect} from '@playwright/test';
test('skeleton controls reach complete and recovered exports without starting capture',async({page})=>{
 const posted:any[]=[];
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  let value:any={status:'idle'};
  if(path==='/api/captures')value={current:{status:'idle'},jobs:[{id:'complete',status:'complete'},{id:'partial',status:'interrupted',shaper:{id:'driver'},recovery:{status:'recovered',result:{},journal:{status:'partial'}}}]};
  if(path==='/api/capture-exports/jobs')value=[];
  if(route.request().method()==='POST'){posted.push({path,body:route.request().postDataJSON()});value={status:'complete'};}
  await route.fulfill({json:value});
 });
 await page.goto('/tests/capture_harness/');
 const enabled=page.getByRole('checkbox',{name:'Incluir esqueleto observado en la exportación'});
 await expect(enabled).not.toBeChecked();await enabled.check();
 await page.getByLabel('Personas en el esqueleto').selectOption('all');
 await page.getByLabel('Confianza mínima del esqueleto').fill('.7');
 await page.getByLabel('Desfase máximo pose/video (s)').fill('.05');
 await page.getByLabel('Grosor del esqueleto (px)').fill('4');
 await page.getByRole('button',{name:'Exportar captura complete',exact:true}).click();
 await expect.poll(()=>posted.length).toBe(1);
 expect(posted[0].body).toMatchObject({skeleton_overlay:true,skeleton_people:'all',skeleton_confidence:.7,skeleton_max_offset_s:.05,skeleton_line_px:4});
 await page.getByRole('checkbox',{name:'Generar preview MP4 para navegador'}).check();
 await page.getByRole('button',{name:'Exportar prefijo recuperado partial',exact:true}).click();
 await expect.poll(()=>posted.length).toBe(2);
 expect(posted[1].body).toMatchObject({skeleton_overlay:true,recovered_prefix:true,browser_preview:true});
 await page.getByRole('checkbox',{name:'Incluir figura de todos los osciladores grabados'}).check();
 await page.getByLabel('Estilo de figura exportada (JSON)').fill('{"color":"gold","components":true}');
 await page.getByLabel('Frecuencia de referencia de la ventana de figura (Hz)').fill('55');
 await page.getByRole('button',{name:'Exportar prefijo recuperado partial',exact:true}).click();
 await expect.poll(()=>posted.length).toBe(3);
 expect(posted[2].body).toMatchObject({harmonic_figure:true,figure_window_hz:55,figure_visual:{color:'gold',components:true},recovered_prefix:true});
 expect(posted.slice(0,2).map(p=>p.path)).toEqual(['/api/captures/complete/export','/api/captures/partial/export']);
});
