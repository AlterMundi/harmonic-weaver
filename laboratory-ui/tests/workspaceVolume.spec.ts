import {test,expect} from '@playwright/test';
import {setup} from './tutorialFixture';

test('desktop options scroll independently and never move beneath the viewers',async({page})=>{
  const {writes,errors}=await setup(page);
  const viewers=page.getByRole('region',{name:'Visualizadores del instrumento',exact:true});
  const options=page.getByRole('region',{name:'Opciones del instrumento',exact:true});
  await page.getByRole('button',{name:'Instrumento',exact:true}).click();
  const before=await viewers.boundingBox();expect(before).not.toBeNull();
  await options.evaluate(el=>{el.scrollTop=el.scrollHeight;});
  await expect.poll(()=>options.evaluate(el=>el.scrollTop)).toBeGreaterThan(0);
  expect((await viewers.boundingBox())!.y).toBeCloseTo(before!.y,1);
  const tab=page.getByRole('button',{name:'Modelos',exact:true});
  const box=await tab.boundingBox();expect(box).not.toBeNull();
  expect(await tab.evaluate(el=>{const r=el.getBoundingClientRect();return el.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));})).toBe(true);
  expect(await page.evaluate(()=>document.documentElement.scrollHeight<=window.innerHeight+2)).toBe(true);
  if(process.env.TUTORIAL_QA_DIR)await page.screenshot({path:process.env.TUTORIAL_QA_DIR+'/workspace-desktop.png'});
  const readings=page.getByRole('complementary',{name:'Lecturas del instrumento',exact:true});
  await readings.evaluate(el=>{el.scrollTop=el.scrollHeight;});
  expect(await readings.evaluate(el=>el.scrollTop)).toBeGreaterThan(0);
  expect(writes).toEqual([]);expect(errors).toEqual([]);
});

test('listening level is independent of voice ratios and supports mute and restore',async({page})=>{
  const {state,updates,errors}=await setup(page);const voices=JSON.stringify(state.preset.voices);
  const level=page.getByRole('slider',{name:'Nivel de escucha',exact:true});
  await level.fill('2');
  await expect.poll(()=>updates.length).toBeGreaterThan(0);
  await expect.poll(()=>state.preset.output_gain).toBe(2);
  expect(JSON.stringify(state.preset.voices)).toBe(voices);
  await page.getByRole('button',{name:'Silenciar instrumento',exact:true}).click();
  await expect.poll(()=>state.preset.output_gain).toBe(0);
  await page.getByRole('button',{name:'Reactivar sonido',exact:true}).click();
  await expect.poll(()=>state.preset.output_gain).toBe(2);
  expect(errors).toEqual([]);
});

test('openness is an explicit mode and posture capture requires observed body data',async({page})=>{
  const {state,updates}=await setup(page);
  await page.getByText('Apertura de brazos y respuesta',{exact:true}).click();
  await expect(page.getByRole('button',{name:'Guardar postura abierta',exact:true})).toBeDisabled();
  state.runtime.body_volume={state:'observed',ratio:.5,level:0};
  await page.getByRole('button',{name:'Guardar postura cerrada',exact:true}).click();
  await expect.poll(()=>state.preset.body_volume.closed_ratio).toBe(.5);
  state.runtime.body_volume={state:'observed',ratio:2.5,level:1};
  await page.getByRole('button',{name:'Guardar postura abierta',exact:true}).click();
  await expect.poll(()=>state.preset.body_volume.open_ratio).toBe(2.5);
  await page.getByRole('checkbox',{name:'Controlar volumen con apertura',exact:true}).check();
  await expect.poll(()=>state.preset.body_volume.enabled).toBe(true);
  await page.getByRole('combobox',{name:'Respuesta a la apertura',exact:true}).selectOption('pose');
  await expect.poll(()=>state.preset.body_volume.mode).toBe('pose');
  expect(updates.every((x:any)=>x.path==='/api/configuration')).toBe(true);
});

test('short desktop keeps options reachable without viewer overlap',async({page})=>{
  await page.setViewportSize({width:1280,height:600});await setup(page);
  await page.getByRole('button',{name:'Instrumento',exact:true}).click();
  const options=page.getByRole('region',{name:'Opciones del instrumento',exact:true});
  await options.evaluate(el=>{el.scrollTop=el.scrollHeight;});
  expect(await options.evaluate(el=>el.scrollTop)).toBeGreaterThan(0);
  const tab=page.getByRole('button',{name:'Modelos',exact:true});await tab.scrollIntoViewIfNeeded();
  expect(await tab.evaluate(el=>{const r=el.getBoundingClientRect();return el.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));})).toBe(true);
});
