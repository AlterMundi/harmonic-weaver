import {test,expect} from '@playwright/test';
import {setupRecording as setup} from './recordingFixture';

const mutations=(fx:any,path:string)=>fx.calls.filter((c:any)=>c.path===path);
const stopAndFinish=async(page:any,fx:any)=>{
 const stopped=page.waitForResponse((response:any)=>new URL(response.url()).pathname==='/api/captures/stop'&&response.request().method()==='POST');
 await page.getByRole('button',{name:'Detener y guardar',exact:true}).click();await stopped;fx.finish();
};

test('record, confirm close, export overlay with audio and keep the original source/preset',async({page})=>{
 const fx=await setup(page),preset=JSON.stringify(fx.state.preset);
 await page.waitForTimeout(900);expect(fx.calls).toEqual([]);
 const source=await page.locator('.source-view').elementHandle();
 await page.getByRole('button',{name:'Grabar',exact:true}).evaluate(el=>{(el as HTMLButtonElement).click();(el as HTMLButtonElement).click();});
 await expect(page.getByRole('button',{name:'Detener y guardar',exact:true})).toBeEnabled();
 expect(mutations(fx,'/api/captures/start')).toHaveLength(1);
 expect(mutations(fx,'/api/captures/start')[0].body).toMatchObject({record_camera:true,max_seconds:300,timeline_hz:20});
 await page.getByRole('button',{name:'Detener y guardar',exact:true}).click();
 await page.waitForTimeout(900);expect(mutations(fx,'/api/captures/take-one/export')).toHaveLength(0);
 fx.finish();await expect.poll(()=>mutations(fx,'/api/captures/take-one/export').length).toBe(1);
 expect(mutations(fx,'/api/captures/take-one/export')[0].body).toMatchObject({skeleton_overlay:true,browser_preview:true,harmonic_figure:false,width:1280,height:720});
 fx.saved();await page.getByRole('button',{name:/^Tomas \(/}).click();
 await expect(page.getByText('Video listo',{exact:true})).toBeVisible();
 await expect(page.getByRole('link',{name:'Descargar MP4',exact:true})).toHaveAttribute('href','/api/capture-exports/export-one/artifacts/preview.mp4');
 await expect(page.getByRole('link',{name:/Descargar original MKV/})).toHaveAttribute('href','/api/capture-exports/export-one/artifacts/capture.mkv');
 await page.getByRole('button',{name:'Cerrar tomas'}).click();
 expect(await page.locator('.source-view').evaluate((el,old)=>el===old,source)).toBe(true);
 expect(JSON.stringify(fx.state.preset)).toBe(preset);expect(fx.errors).toEqual([]);
});

test('saved takes survive page reload, preview never autoplays and downloads work',async({page})=>{
 const fx=await setup(page,{existing:true});await page.reload();
 await page.getByRole('button',{name:/^Tomas \(/}).click();
 await expect(page.getByText('Video listo',{exact:true})).toBeVisible();expect(fx.calls).toEqual([]);
 await page.getByRole('button',{name:'Ver video',exact:true}).click();
 const video=page.locator('.takes-dialog video');await expect(video).toHaveJSProperty('autoplay',false);
 if(process.env.LAB_CAPTURE_PREVIEW){
  await expect.poll(()=>video.evaluate((v:HTMLVideoElement)=>v.readyState)).toBeGreaterThanOrEqual(1);
  expect(await video.evaluate((v:HTMLVideoElement)=>v.paused)).toBe(true);
  await video.evaluate(async(v:HTMLVideoElement)=>{v.muted=true;await v.play();});
  await expect.poll(()=>video.evaluate((v:HTMLVideoElement)=>v.currentTime)).toBeGreaterThan(.1);
  const downloaded=page.waitForEvent('download');await page.getByRole('link',{name:'Descargar MP4',exact:true}).click();
  expect(await(await downloaded).failure()).toBeNull();
 }
 if(process.env.TUTORIAL_QA_DIR)await page.screenshot({path:process.env.TUTORIAL_QA_DIR+'/takes-desktop.png'});
 await page.getByRole('button',{name:'Cerrar tomas'}).click();await expect(video).toHaveCount(0);
 await expect(page.getByRole('button',{name:/^Tomas \(/})).toBeFocused();expect(fx.errors).toEqual([]);
});

test('missing camera disables recording and the take library fits a narrow screen',async({page})=>{
 await page.setViewportSize({width:390,height:844});const fx=await setup(page,{camera:false});
 await expect(page.getByRole('button',{name:'Grabar',exact:true})).toBeDisabled();
 await page.getByRole('button',{name:/^Tomas \(/}).click();
 const dialog=page.getByRole('dialog');await expect(dialog).toContainText('encendé la cámara');
 expect(await dialog.evaluate(el=>el.scrollWidth<=el.clientWidth+1)).toBe(true);
 if(process.env.TUTORIAL_QA_DIR)await page.screenshot({path:process.env.TUTORIAL_QA_DIR+'/takes-narrow.png'});
 await page.keyboard.press('Escape');await expect(dialog).not.toBeVisible();expect(fx.calls).toEqual([]);
 if(process.env.TUTORIAL_QA_DIR)await page.screenshot({path:process.env.TUTORIAL_QA_DIR+'/recorder-narrow.png'});
});

test('a lost recording acknowledgement is not replayed and confirmed inventory can stop it',async({page})=>{
 const fx=await setup(page,{loseStart:true});await page.getByRole('button',{name:'Grabar',exact:true}).click();
 await expect(page.getByRole('button',{name:'Detener y guardar',exact:true})).toBeEnabled();
 await page.waitForTimeout(900);expect(mutations(fx,'/api/captures/start')).toHaveLength(1);
 await stopAndFinish(page,fx);
 await expect.poll(()=>mutations(fx,'/api/captures/take-one/export').length).toBe(1);
 expect(mutations(fx,'/api/captures/start')).toHaveLength(1);
});

test('a lost export acknowledgement resolves through inventory without a second export',async({page})=>{
 const fx=await setup(page,{loseExport:true});await page.getByRole('button',{name:'Grabar',exact:true}).click();
 await expect(page.getByRole('button',{name:'Detener y guardar',exact:true})).toBeEnabled();
 await stopAndFinish(page,fx);
 await expect.poll(()=>mutations(fx,'/api/captures/take-one/export').length).toBe(1);
 await page.waitForTimeout(1700);expect(mutations(fx,'/api/captures/take-one/export')).toHaveLength(1);
 fx.saved();await page.getByRole('button',{name:/^Tomas \(/}).click();await expect(page.getByText('Video listo',{exact:true})).toBeVisible();
});

test('failed preparation retains originals and only a human retry can request another export',async({page})=>{
 const fx=await setup(page,{failExport:true});await page.getByRole('button',{name:'Grabar',exact:true}).click();
 await expect(page.getByRole('button',{name:'Detener y guardar',exact:true})).toBeEnabled();
 await stopAndFinish(page,fx);
 await expect.poll(()=>mutations(fx,'/api/captures/take-one/export').length).toBe(1);
 await page.waitForTimeout(1600);expect(mutations(fx,'/api/captures/take-one/export')).toHaveLength(1);
 await page.getByRole('button',{name:/^Tomas \(/}).click();await expect(page.getByText('Originales guardados',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Preparar video de esta toma',exact:true}).click();
 await expect.poll(()=>mutations(fx,'/api/captures/take-one/export').length).toBe(2);
});

test('no received camera frames never produce a misleading black saved video',async({page})=>{
 const fx=await setup(page);await page.getByRole('button',{name:'Grabar',exact:true}).click();
 await expect(page.getByRole('button',{name:'Detener y guardar',exact:true})).toBeEnabled();fx.failImages();
 await expect(page.getByRole('alert')).toContainText('no llegaron imágenes');
 await expect(page.getByRole('button',{name:'Grabar',exact:true})).toBeEnabled();
 expect(mutations(fx,'/api/captures/take-one/export')).toHaveLength(0);
});
