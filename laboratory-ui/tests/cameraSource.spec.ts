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
