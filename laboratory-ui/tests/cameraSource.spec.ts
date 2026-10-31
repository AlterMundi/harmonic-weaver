import {test,expect} from '@playwright/test';
import {setupRecording} from './recordingFixture';
async function setup(page:any,options:any={}){const fx=await setupRecording(page,options);await page.getByRole('button',{name:'Abrir fuentes',exact:true}).click();return fx;}
const writes=(fx:any,path:string)=>fx.calls.filter((c:any)=>c.path===path);
const region=(page:any)=>page.getByRole('group',{name:'Conectar cámara',exact:true});

test('USB and integrated cameras are named and enumeration opens neither',async({page})=>{
 const fx=await setup(page,{camera:false}),p=region(page);await expect(p.getByRole('combobox',{name:'Cámara disponible',exact:true})).toContainText('Logi Webcam C920e');await expect(p).toContainText('Integrated Webcam HD');
 await expect(p.getByRole('button',{name:'Usar esta cámara',exact:true})).toBeDisabled();expect(fx.calls).toEqual([]);
 await p.getByRole('button',{name:'Actualizar cámaras',exact:true}).click();expect(fx.calls).toEqual([]);
 await p.getByText('Si abrís la web desde otra computadora',{exact:true}).click();await expect(p).toContainText('ejecutá HarmoCap en esa computadora');
});

test('a remembered USB identity is retained after renumbering, without opening it on reload',async({page})=>{
 const fx=await setup(page,{camera:false}),p=region(page),select=p.getByRole('combobox',{name:'Cámara disponible',exact:true});await select.selectOption(fx.cameras[0].id);await page.reload();await page.getByRole('button',{name:'Abrir fuentes',exact:true}).click();await expect(select).toHaveValue(fx.cameras[0].id);expect(fx.calls).toEqual([]);
 fx.cameras[0].index=4;await p.getByRole('button',{name:'Actualizar cámaras',exact:true}).click();await expect(select).toContainText('cámara 4');
 await p.getByRole('button',{name:'Usar esta cámara',exact:true}).evaluate(el=>{(el as HTMLButtonElement).click();(el as HTMLButtonElement).click();});
 await expect.poll(()=>writes(fx,'/api/sources/camera').length).toBe(1);expect(writes(fx,'/api/sources/camera')[0].body.device_id).toBe(fx.cameras[0].id);expect(writes(fx,'/api/sources/camera')[0].body.index).toBeUndefined();
 await expect(p).toContainText('Preparando la cámara');fx.cameraReady();await expect(p).toContainText('Cámara en vivo · Logi Webcam C920e');await expect(p).toContainText('todavía no se detectó un cuerpo');expect(fx.errors).toEqual([]);
});

test('unplugged saved camera never falls back to the remaining webcam',async({page})=>{
 const fx=await setup(page,{camera:false}),p=region(page);const chosen=fx.cameras[0].id;await p.getByRole('combobox',{name:'Cámara disponible',exact:true}).selectOption(chosen);fx.cameras.splice(0,1);
 await p.getByRole('button',{name:'Actualizar cámaras',exact:true}).click();await expect(p).toContainText('La cámara guardada no aparece conectada');await expect(p.getByRole('combobox',{name:'Cámara disponible',exact:true})).toHaveValue(chosen);await expect(p.getByRole('button',{name:'Usar esta cámara',exact:true})).toBeDisabled();expect(fx.calls).toEqual([]);
});

test('failed inventory preserves the current source and requires a confirmed list before switching',async({page})=>{
 const fx=await setup(page,{camera:false}),p=region(page);await p.getByRole('combobox',{name:'Cámara disponible',exact:true}).selectOption(fx.cameras[0].id);fx.failCameras();await p.getByRole('button',{name:'Actualizar cámaras',exact:true}).click();await expect(p.getByRole('alert')).toContainText('No se pudo actualizar');await expect(p.getByRole('button',{name:'Usar esta cámara',exact:true})).toBeDisabled();expect(fx.calls).toEqual([]);
});

test('lost camera acknowledgement is not automatically replayed and live state resolves it',async({page})=>{
 const fx=await setup(page,{camera:false,loseCameraStart:true}),p=region(page);await p.getByRole('combobox',{name:'Cámara disponible',exact:true}).selectOption(fx.cameras[0].id);await p.getByRole('button',{name:'Usar esta cámara',exact:true}).click();
 await expect(p.getByRole('button',{name:'Esta cámara está en uso',exact:true})).toBeDisabled();await p.getByRole('button',{name:'Actualizar cámaras',exact:true}).click();expect(writes(fx,'/api/sources/camera')).toHaveLength(1);fx.cameraReady();await expect(p).toContainText('Cámara en vivo');
});

test('camera selection and closing are blocked during a recording',async({page})=>{
 const fx=await setup(page),p=region(page);fx.inventory.current={id:'busy-take',status:'recording'};await expect(p.getByRole('combobox',{name:'Cámara disponible',exact:true})).toBeDisabled();await expect(p.getByRole('button',{name:'Cerrar fuente / apagar cámara',exact:true})).toBeDisabled();await expect(p).toContainText('Detené la grabación');expect(writes(fx,'/api/sources/camera')).toHaveLength(0);
});

test('unsupported enumeration offers the explicit legacy index without probing random cameras',async({page})=>{
 const fx=await setup(page,{camera:false}),p=region(page);fx.cameraInventory.supported=false;fx.cameras.splice(0);await p.getByRole('button',{name:'Actualizar cámaras',exact:true}).click();await expect(p).toContainText('detección por nombre está disponible en Linux');await p.getByText('Elegir cámara por índice · avanzado',{exact:true}).click();await p.getByRole('spinbutton',{name:'Índice de cámara',exact:true}).fill('2');await p.getByRole('button',{name:'Usar índice manual',exact:true}).click();await expect.poll(()=>writes(fx,'/api/sources/camera').length).toBe(1);expect(writes(fx,'/api/sources/camera')[0].body.index).toBe(2);
});

test('named camera settings are readable and fit a narrow screen',async({page})=>{
 await page.setViewportSize({width:390,height:844});await setup(page,{camera:false});const p=region(page);await expect(p.getByRole('combobox',{name:'Cámara disponible',exact:true})).toContainText('Logi Webcam C920e');expect(await p.evaluate(el=>el.scrollWidth<=el.clientWidth+1)).toBe(true);if(process.env.TUTORIAL_QA_DIR)await p.screenshot({path:process.env.TUTORIAL_QA_DIR+'/camera-choice-narrow.png'});
});

test('portrait and reverse direction are explicit, per-device choices remembered without starting',async({page})=>{
 const fx=await setup(page,{camera:false}),p=region(page),select=p.getByRole('combobox',{name:'Cámara disponible',exact:true}),orientation=p.getByRole('group',{name:'Orientación de la cámara'});
 await select.selectOption(fx.cameras[0].id);await orientation.getByRole('button',{name:'Vertical',exact:true}).click();await orientation.getByRole('button',{name:'Dar vuelta',exact:true}).click();await expect(orientation).toContainText('giro a la izquierda');
 await select.selectOption(fx.cameras[1].id);await expect(orientation.getByRole('button',{name:'Horizontal',exact:true})).toHaveAttribute('aria-pressed','true');
 await select.selectOption(fx.cameras[0].id);await expect(orientation.getByRole('button',{name:'Vertical',exact:true})).toHaveAttribute('aria-pressed','true');await expect(orientation).toContainText('giro a la izquierda');
 await page.reload();await page.getByRole('button',{name:'Abrir fuentes',exact:true}).click();await expect(orientation).toContainText('giro a la izquierda');expect(writes(fx,'/api/sources/camera')).toHaveLength(0);
 await p.getByRole('button',{name:'Usar esta cámara',exact:true}).click();await expect.poll(()=>writes(fx,'/api/sources/camera').length).toBe(1);expect(writes(fx,'/api/sources/camera')[0].body.perception.camera_rotation_degrees).toBe(270);
});

test('changing an active camera orientation preserves its processing settings and waits for Apply',async({page})=>{
 const fx=await setup(page),p=region(page),orientation=p.getByRole('group',{name:'Orientación de la cámara'});
 Object.assign(fx.state.source.camera,{device_id:fx.cameras[0].id,index:0,rotation_degrees:0,perception:{checkpoint:'keep.pt',imgsz:448,confidence:.42}});
 await expect(p.getByRole('combobox',{name:'Cámara disponible',exact:true})).toHaveValue(fx.cameras[0].id);
 await orientation.getByRole('button',{name:'Vertical',exact:true}).click();await expect(p.getByRole('button',{name:'Aplicar orientación',exact:true})).toBeEnabled();await expect(orientation).toContainText('En uso: Horizontal');expect(writes(fx,'/api/sources/camera')).toHaveLength(0);
 const before=JSON.stringify(fx.state.preset);await p.getByRole('button',{name:'Aplicar orientación',exact:true}).click();await expect.poll(()=>writes(fx,'/api/sources/camera').length).toBe(1);
 expect(writes(fx,'/api/sources/camera')[0].body.perception).toEqual({checkpoint:'keep.pt',imgsz:448,confidence:.42,camera_rotation_degrees:90});expect(JSON.stringify(fx.state.preset)).toBe(before);fx.cameraReady();
 await expect(orientation).toContainText('En uso: Vertical');await orientation.getByRole('button',{name:'Horizontal',exact:true}).click();await p.getByRole('button',{name:'Aplicar orientación',exact:true}).click();await expect.poll(()=>writes(fx,'/api/sources/camera').length).toBe(2);expect(writes(fx,'/api/sources/camera')[1].body.perception.camera_rotation_degrees).toBe(0);
 expect(fx.errors).toEqual([]);
});

test('rotation cannot restart the source during a recording',async({page})=>{
 const fx=await setup(page),orientation=region(page).getByRole('group',{name:'Orientación de la cámara'});fx.inventory.current={id:'busy-take',status:'recording'};
 for(const label of ['Horizontal','Vertical','Dar vuelta'])await expect(orientation.getByRole('button',{name:label,exact:true})).toBeDisabled();expect(writes(fx,'/api/sources/camera')).toHaveLength(0);
});

test('portrait controls remain readable and contained on narrow screens',async({page})=>{
 await page.setViewportSize({width:390,height:844});const fx=await setup(page,{camera:false}),p=region(page),orientation=p.getByRole('group',{name:'Orientación de la cámara'});await p.getByRole('combobox',{name:'Cámara disponible',exact:true}).selectOption(fx.cameras[0].id);await orientation.getByRole('button',{name:'Vertical',exact:true}).click();
 expect(await orientation.evaluate(el=>el.scrollWidth<=el.clientWidth+1)).toBe(true);expect(await orientation.getByRole('button',{name:'Vertical',exact:true}).evaluate(el=>parseFloat(getComputedStyle(el).fontSize))).toBeGreaterThanOrEqual(16);
 if(process.env.TUTORIAL_QA_DIR)await orientation.screenshot({path:process.env.TUTORIAL_QA_DIR+'/camera-orientation-narrow.png'});
});

test('portrait preview and skeleton share the fitted image coordinates',async({page})=>{
 const fx=await setup(page);await page.route('**/api/camera/preview?**',route=>route.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="720" height="1280"><rect width="720" height="1280" fill="#17324a"/><circle cx="256" cy="384" r="24" fill="#69e7cf"/></svg>'}));
 fx.state.motion_frame={width:720,height:1280,persons:[{person_id:'one',joints:[{index:5,position:[.2,.3],state:'observed'},{index:6,position:[.4,.3],state:'observed'}]}]};fx.state.preset.visual.show_skeleton=true;
 await page.getByRole('button',{name:'Cerrar fuentes',exact:true}).click();const svg=page.locator('.video-wrap .skeleton');await expect(svg).toHaveAttribute('viewBox','0 0 0.5625 1');
 await expect.poll(()=>page.getByAltText('Cámara en vivo').evaluate((el:any)=>el.naturalWidth)).toBe(720);
 const result=await page.locator('.video-wrap').evaluate((wrap:any)=>{const img=wrap.querySelector('img'),svg=wrap.querySelector('svg'),b=img.getBoundingClientRect(),s=Math.min(b.width/img.naturalWidth,b.height/img.naturalHeight),m=svg.getScreenCTM();return {svgX:m.a*.2+m.e,svgY:m.d*.3+m.f,imageX:b.x+(b.width-img.naturalWidth*s)/2+256*s,imageY:b.y+(b.height-img.naturalHeight*s)/2+384*s};});
 expect(Math.abs(result.svgX-result.imageX)).toBeLessThan(1);expect(Math.abs(result.svgY-result.imageY)).toBeLessThan(1);
 if(process.env.TUTORIAL_QA_DIR)await page.locator('.source-view').screenshot({path:process.env.TUTORIAL_QA_DIR+'/portrait-source-synthetic.png'});
});

test('choosing a camera directly reveals and focuses its orientation step',async({page})=>{
 const fx=await setup(page,{camera:false}),p=region(page),orientation=p.getByRole('group',{name:'Orientación de la cámara'});
 await p.getByRole('combobox',{name:'Cámara disponible',exact:true}).selectOption(fx.cameras[0].id);
 await expect(orientation).toBeFocused();await expect(orientation).toContainText('2. Elegí Horizontal o Vertical');await expect(orientation).toContainText('Orientación para Logi Webcam C920e.');expect(writes(fx,'/api/sources/camera')).toHaveLength(0);
 await orientation.getByRole('button',{name:'Vertical',exact:true}).click();await p.getByRole('button',{name:'Usar esta cámara',exact:true}).click();await expect.poll(()=>writes(fx,'/api/sources/camera').length).toBe(1);expect(writes(fx,'/api/sources/camera')[0].body.perception.camera_rotation_degrees).toBe(90);
});
