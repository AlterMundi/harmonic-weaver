import {test,expect} from '@playwright/test';
import {setupRecording as setup} from './recordingFixture';

test('Fuentes is available in Performance and opens named cameras without changing the view or instrument',async({page})=>{
 await page.addInitScript(()=>localStorage.setItem('weaver-lab-performance','true'));
 const fx=await setup(page,{camera:false}),preset=JSON.stringify(fx.state.preset);
 await expect(page.getByRole('button',{name:'Performance',exact:true})).toHaveAttribute('aria-pressed','true');
 const viewer=await page.locator('.source-view').elementHandle();
 const open=page.getByRole('button',{name:'Abrir fuentes',exact:true});await expect(open).toBeVisible();await open.click();
 const dialog=page.getByRole('dialog',{name:'Fuentes',exact:true});await expect(dialog).toBeVisible();
 await expect(dialog.getByRole('combobox',{name:'Cámara disponible',exact:true})).toContainText('Logi Webcam C920e');
 await expect(dialog.getByRole('combobox',{name:'Cámara disponible',exact:true})).toContainText('Integrated Webcam HD');
 await expect(dialog.getByRole('group',{name:'Tipo de fuente',exact:true})).toBeVisible();
 const button=dialog.getByRole('button',{name:'Usar esta cámara',exact:true});await button.scrollIntoViewIfNeeded();
 expect(await button.evaluate(el=>{const r=el.getBoundingClientRect();return el.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2));})).toBe(true);
 await page.keyboard.press('Escape');await expect(dialog).not.toBeVisible();await expect(open).toBeFocused();
 await expect(page.getByRole('button',{name:'Performance',exact:true})).toHaveAttribute('aria-pressed','true');
 expect(await page.locator('.source-view').evaluate((el,old)=>el===old,viewer)).toBe(true);expect(JSON.stringify(fx.state.preset)).toBe(preset);expect(fx.calls).toEqual([]);expect(fx.errors).toEqual([]);
});

test('video upload and camera controls share the same Fuentes panel and close leaves source running',async({page})=>{
 const fx=await setup(page);const original=await page.locator('.source-view').elementHandle();await page.getByRole('button',{name:'Abrir fuentes',exact:true}).click();
 const dialog=page.getByRole('dialog',{name:'Fuentes',exact:true});
 await dialog.getByRole('button',{name:'Cargar video',exact:true}).click();
 await expect(dialog.getByLabel('Elegir y cargar un video',{exact:false})).toBeAttached();await expect(dialog.getByRole('combobox',{name:'Videos de la biblioteca',exact:true})).toBeVisible();
 await expect(dialog.getByRole('button',{name:'Cámara en vivo',exact:true})).toHaveAttribute('aria-pressed','false');
 await dialog.getByRole('button',{name:'Cámara en vivo',exact:true}).click();await expect(dialog.getByRole('combobox',{name:'Cámara disponible',exact:true})).toContainText('Logi Webcam C920e');
 await dialog.getByRole('button',{name:'Cerrar fuentes',exact:true}).click();expect(fx.calls).toEqual([]);expect(fx.state.source.kind).toBe('camera');
 expect(await page.locator('.source-view').evaluate((el,old)=>el===old,original)).toBe(true);
});

test('Explore source shortcuts open the chosen section and video operations retain the existing API',async({page})=>{
 const fx=await setup(page,{camera:false});await page.getByRole('button',{name:'Cargar un video',exact:true}).click();
 const dialog=page.getByRole('dialog',{name:'Fuentes',exact:true});await expect(dialog.getByRole('button',{name:'Cargar video',exact:true})).toHaveAttribute('aria-pressed','true');
 await dialog.getByText('Video por ruta y tracking · avanzado',{exact:true}).click();
 await dialog.getByLabel('Ruta del video',{exact:true}).fill('/synthetic/video.mp4');await dialog.getByRole('button',{name:'Abrir video',exact:true}).click();
 await expect.poll(()=>fx.calls.filter((c:any)=>c.path==='/api/sources/video').length).toBe(1);expect(fx.calls.find((c:any)=>c.path==='/api/sources/video').body.path).toBe('/synthetic/video.mp4');
});

test('Fuentes remains accessible while the movement tutorial is open',async({page})=>{
 const fx=await setup(page,{camera:false});await page.getByRole('button',{name:'Hacer tutorial',exact:true}).click();
 const tutorial=page.getByRole('region',{name:'Tutorial de movimiento',exact:true});await expect(tutorial).toBeVisible();
 await page.getByRole('button',{name:'Abrir fuentes',exact:true}).click();const dialog=page.getByRole('dialog',{name:'Fuentes',exact:true});await expect(dialog).toBeVisible();
 await dialog.getByRole('button',{name:'Cerrar fuentes',exact:true}).click();await expect(tutorial).toBeVisible();expect(fx.calls).toEqual([]);
});

test('narrow Fuentes dialog scrolls within the viewport and keeps readable controls',async({page})=>{
 await page.setViewportSize({width:390,height:844});await setup(page,{camera:false});await page.getByRole('button',{name:'Abrir fuentes',exact:true}).click();
 const dialog=page.getByRole('dialog',{name:'Fuentes',exact:true});await expect(dialog.getByRole('combobox',{name:'Cámara disponible',exact:true})).toContainText('Logi Webcam C920e');
 expect(await dialog.evaluate(el=>el.scrollWidth<=el.clientWidth+1)).toBe(true);expect((await dialog.boundingBox())!.height).toBeLessThanOrEqual(822);
 expect(await dialog.getByRole('combobox',{name:'Cámara disponible',exact:true}).evaluate(el=>parseFloat(getComputedStyle(el).fontSize))).toBeGreaterThanOrEqual(16);
 if(process.env.TUTORIAL_QA_DIR)await page.screenshot({path:process.env.TUTORIAL_QA_DIR+'/fuentes-narrow.png'});
});


test('camera start and stop are both reachable inside Fuentes',async({page})=>{
 const fx=await setup(page,{camera:false});await page.getByRole('button',{name:'Abrir fuentes',exact:true}).click();const d=page.getByRole('dialog',{name:'Fuentes',exact:true});
 await d.getByRole('combobox',{name:'Cámara disponible',exact:true}).selectOption(fx.cameras[0].id);await d.getByRole('button',{name:'Usar esta cámara',exact:true}).click();
 await expect.poll(()=>fx.calls.filter((c:any)=>c.path==='/api/sources/camera').length).toBe(1);fx.cameraReady();await expect(d.getByText(/Cámara en vivo · Logi/)).toBeVisible();
 await d.getByRole('button',{name:'Cerrar fuente / apagar cámara',exact:true}).click();await expect.poll(()=>fx.calls.filter((c:any)=>c.path==='/api/sources/close').length).toBe(1);await expect(d.getByRole('button',{name:'Cerrar fuente / apagar cámara',exact:true})).toBeDisabled();expect(fx.state.source.kind).toBeNull();
});

test('Cargar video opens the existing upload flow with a chosen browser file',async({page})=>{
 const fx=await setup(page,{camera:false});await page.getByRole('button',{name:'Abrir fuentes',exact:true}).click();const d=page.getByRole('dialog',{name:'Fuentes',exact:true});await d.getByRole('button',{name:'Cargar video',exact:true}).click();
 await d.getByLabel('Elegir y cargar un video',{exact:false}).setInputFiles({name:'synthetic.mp4',mimeType:'video/mp4',buffer:Buffer.from('synthetic upload fixture; no human media')});
 await expect.poll(()=>fx.calls.filter((c:any)=>c.path==='/api/sources/upload').length).toBe(1);expect(fx.calls.find((c:any)=>c.path==='/api/sources/upload').contentType).toContain('multipart/form-data');
});
