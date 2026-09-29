import {test,expect} from '@playwright/test';

test('live instrument edits, portable preset and effective audio figure',async({page})=>{
  const errors:string[]=[];
  const presetName='Prueba web '+Date.now();
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto('/');
  await expect(page.getByRole('heading',{name:'Weaver / laboratorio corporal'})).toBeVisible();
  await expect(page.getByText('En línea',{exact:false})).toBeVisible();
  await page.getByRole('button',{name:'Instrumento',exact:true}).click();
  const master=page.getByRole('spinbutton',{name:'Master',exact:true});
  await master.fill('0.31');
  await expect.poll(async()=>{const r=await page.request.get('/api/state');return(await r.json()).preset.master;}).toBe(.31);
  await expect.poll(async()=>{const r=await page.request.get('/api/state');const d=await r.json();return d.session.desired_revision===d.shaper.applied_revision;}).toBe(true);
  await page.getByRole('button',{name:'Figura',exact:true}).click();
  await page.getByRole('checkbox',{name:'Mostrar componentes',exact:true}).check();
  await expect.poll(async()=>{const r=await page.request.get('/api/state');return(await r.json()).preset.visual.components;}).toBe(true);
  await page.getByRole('button',{name:'Presets',exact:true}).click();
  await page.getByRole('textbox',{name:'Nombre',exact:true}).fill(presetName);
  await page.getByRole('button',{name:'Guardar como nuevo'}).click();
  await expect(page.getByRole('button',{name:presetName,exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Fuente',exact:true}).click();
  await page.screenshot({path:'/tmp/weaver-laboratory-first-ui.png',fullPage:true});
  expect(errors).toEqual([]);
});
