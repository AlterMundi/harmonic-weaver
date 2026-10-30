import {test, expect} from '@playwright/test';
import {setup} from './tutorialFixture';

test('three-movement guide preserves source, presets and transport and restores focus',async({page})=>{
  const {state,writes,errors}=await setup(page),preset=JSON.stringify(state.preset);
  const original=await page.getByAltText('Cámara en vivo',{exact:true}).elementHandle();
  await page.getByRole('button',{name:'Hacer tutorial',exact:true}).click();
  const tutorial=page.getByRole('region',{name:'Tutorial de movimiento',exact:true});
  await expect(tutorial).toContainText('Dibujá círculos con las manos');
  await expect(tutorial.getByRole('meter',{name:'Señal de Muñecas'})).toHaveAttribute('value','0.61');
  await expect(tutorial).toContainText('4 de 4 puntos');
  if(process.env.TUTORIAL_QA_DIR)await page.screenshot({path:process.env.TUTORIAL_QA_DIR+'/tutorial-desktop.png'});
  await tutorial.getByRole('button',{name:'Ya lo probé · siguiente',exact:true}).click();
  await expect(tutorial).toContainText('Balanceá hombros y caderas');
  await tutorial.getByRole('button',{name:'Ya lo probé · siguiente',exact:true}).click();
  await expect(tutorial).toContainText('Alterná pequeños pasos');
  await tutorial.getByRole('button',{name:'Terminar tutorial',exact:true}).click();
  await expect(tutorial).toContainText('Listo para explorar');
  expect(await page.getByAltText('Cámara en vivo',{exact:true}).evaluate((node,old)=>node===old,original)).toBe(true);
  expect(JSON.stringify(state.preset)).toBe(preset);expect(state.session.desired_revision).toBe(8);
  expect(state.session.playing).toBe(true);expect(writes).toEqual([]);expect(errors).toEqual([]);
  await tutorial.getByRole('button',{name:'Cerrar tutorial',exact:true}).click();
  await expect(tutorial).toHaveCount(0);await expect(page.getByRole('button',{name:'Hacer tutorial',exact:true})).toBeFocused();
  await page.getByRole('button',{name:'Hacer tutorial',exact:true}).click();
  await page.getByRole('button',{name:'Performance',exact:true}).click();
  await expect(tutorial).toHaveCount(0);expect(writes).toEqual([]);
});

test('reduced motion starts still and supports static positions and explicit playback',async({page})=>{
  await page.emulateMedia({reducedMotion:'reduce'});await setup(page);
  await page.getByRole('button',{name:'Hacer tutorial',exact:true}).click();
  const tutorial=page.getByRole('region',{name:'Tutorial de movimiento'}),figure=tutorial.getByRole('img');
  const first=await figure.getAttribute('data-phase');await page.waitForTimeout(120);expect(await figure.getAttribute('data-phase')).toBe(first);
  await tutorial.getByRole('button',{name:'Siguiente posición',exact:true}).click();
  await expect(figure).not.toHaveAttribute('data-phase',first!);
  const paused=await figure.getAttribute('data-phase');await tutorial.getByRole('button',{name:'Reproducir ejemplo',exact:true}).click();
  await expect.poll(()=>figure.getAttribute('data-phase')).not.toBe(paused);
  await tutorial.getByRole('button',{name:'Pausar ejemplo',exact:true}).click();
  const stopped=await figure.getAttribute('data-phase');await page.waitForTimeout(120);expect(await figure.getAttribute('data-phase')).toBe(stopped);
});

test('missing observations and muted voice are described without synthetic success',async({page})=>{
  const {state,writes}=await setup(page);
  state.motion_frame.persons[0].joints=state.motion_frame.persons[0].joints.filter((j:any)=>j.index!==9&&j.index!==10);
  state.runtime.routing.voices['6']={state:'muted',target_gain:0};
  await page.getByRole('button',{name:'Hacer tutorial',exact:true}).click();
  const tutorial=page.getByRole('region',{name:'Tutorial de movimiento'});
  await expect(tutorial).toContainText('2 de 4 puntos');await expect(tutorial).toContainText('Voz en silencio por Solo o Silenciar');
  state.motion_frame=null;await expect(tutorial).toContainText('Esperando a la persona seleccionada');
  await expect(tutorial.getByRole('meter',{name:'Señal de Codos'})).toHaveAttribute('value','0');
  expect(writes).toEqual([]);
});

test('guide can be read with no camera and fits a narrow screen',async({page})=>{
  await page.setViewportSize({width:390,height:844});const {writes,errors}=await setup(page,false);
  await page.getByRole('button',{name:'Hacer tutorial',exact:true}).click();
  const tutorial=page.getByRole('region',{name:'Tutorial de movimiento'});
  await expect(tutorial).toContainText('Encendé la cámara');
  await expect(tutorial.getByRole('meter',{name:'Señal de Codos'})).toHaveAttribute('value','0');
  await expect(tutorial.getByRole('button',{name:'Reproducir ejemplo'}).or(tutorial.getByRole('button',{name:'Pausar ejemplo'}))).toBeVisible();
  expect(await tutorial.evaluate(el=>el.scrollWidth<=el.clientWidth+1)).toBe(true);
  if(process.env.TUTORIAL_QA_DIR){await tutorial.evaluate(el=>el.scrollIntoView({block:'start'}));await tutorial.screenshot({path:process.env.TUTORIAL_QA_DIR+'/tutorial-narrow.png'});}
  expect(writes).toEqual([]);expect(errors).toEqual([]);
});
