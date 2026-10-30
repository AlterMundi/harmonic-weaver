import {test,expect} from '@playwright/test';
import {setupRecording as setup} from './recordingFixture';

const writes=(fx:any,path:string)=>fx.calls.filter((r:any)=>r.path===path);
async function panel(page:any){await page.getByRole('button',{name:'Configurar grabación',exact:true}).click();return page.getByRole('region',{name:'Configuración de grabación',exact:true});}
async function save(page:any){await page.getByRole('button',{name:'Guardar configuración de grabación',exact:true}).click();await expect(page.getByRole('region',{name:'Configuración de grabación',exact:true}).getByRole('status')).toContainText('Configuración guardada');}

test('Grabar is beside Captura and settings persist without recording or changing the instrument',async({page})=>{
 const fx=await setup(page),preset=JSON.stringify(fx.state.preset);const p=await panel(page);
 const nav=await page.getByRole('navigation',{name:'Secciones del laboratorio'}).getByRole('button').allTextContents();
 expect(nav.indexOf('Grabar')).toBe(nav.indexOf('Captura')+1);
 await p.getByRole('button',{name:'Solo video y música',exact:true}).click();
 await expect(p.getByLabel('Sonido de HarmoCap en el video',{exact:true})).toBeChecked();
 await expect(p.getByLabel('Líneas de movimiento sobre el cuerpo',{exact:true})).not.toBeChecked();
 await p.getByLabel('Visualizador cimático junto al video',{exact:true}).check();
 await p.getByLabel('Duración máxima de grabación').fill('60');await save(page);
 expect(fx.preferences).toMatchObject({max_seconds:60,skeleton_overlay:false,harmonic_figure:true,include_audio:true});
 expect(writes(fx,'/api/captures/start')).toHaveLength(0);expect(JSON.stringify(fx.state.preset)).toBe(preset);
 await page.reload();const again=await panel(page);await expect(again.getByLabel('Visualizador cimático junto al video',{exact:true})).toBeChecked();
 await expect(again.getByLabel('Duración máxima de grabación')).toHaveValue('60');expect(fx.errors).toEqual([]);
});

test('the next take uses saved sound, figure and overlay choices and locks settings while recording',async({page})=>{
 const fx=await setup(page);const p=await panel(page);
 await p.getByLabel('Sonido de HarmoCap en el video',{exact:true}).uncheck();
 await p.getByLabel('Líneas de movimiento sobre el cuerpo',{exact:true}).uncheck();
 await p.getByLabel('Visualizador cimático junto al video',{exact:true}).check();await save(page);
 await page.getByRole('button',{name:'Grabar',exact:true}).click();
 await expect(p.getByLabel('Visualizador cimático junto al video',{exact:true})).toBeDisabled();
 await page.getByRole('button',{name:'Detener y guardar',exact:true}).click();fx.finish();
 await expect.poll(()=>writes(fx,'/api/captures/take-one/export').length).toBe(1);
 expect(writes(fx,'/api/captures/take-one/export')[0].body).toMatchObject({include_audio:false,skeleton_overlay:false,harmonic_figure:true});
});

test('a chosen folder receives a copy only after explicit recording and confirmed export',async({page})=>{
 const fx=await setup(page);const p=await panel(page);
 await p.getByLabel('Destino de la grabación').selectOption('folder');await p.getByRole('button',{name:'Elegir carpeta',exact:true}).click();
 await expect(p.getByLabel('Carpeta elegida')).toHaveValue('folder-chosen');await save(page);
 expect(writes(fx,'/api/capture-exports/export-one/save')).toHaveLength(0);
 await page.getByRole('button',{name:'Grabar',exact:true}).click();await expect(page.getByRole('button',{name:'Detener y guardar',exact:true})).toBeEnabled();
 await page.getByRole('button',{name:'Detener y guardar',exact:true}).click();fx.finish();
 await expect.poll(()=>writes(fx,'/api/captures/take-one/export').length).toBe(1);
 expect(writes(fx,'/api/capture-exports/export-one/save')).toHaveLength(0);fx.saved();
 await expect.poll(()=>writes(fx,'/api/capture-exports/export-one/save').length).toBe(1);
 expect(writes(fx,'/api/capture-exports/export-one/save')[0].body).toEqual({destination_id:'folder-chosen',format:'mp4'});
 fx.finishDelivery();await page.getByRole('button',{name:/^Tomas \(/}).click();await expect(page.getByText(/Copia en carpeta verificada/)).toBeVisible();
});

test('Drive requires the account connection and confirmed folder; opening login uploads nothing',async({page})=>{
 const fx=await setup(page);const p=await panel(page);await p.getByLabel('Destino de la grabación').selectOption('drive');
 await expect(p).toContainText('studio@example.test');await expect(p.getByRole('button',{name:'Elegir carpeta de Drive',exact:true})).toBeDisabled();
 await expect(p.getByRole('button',{name:'Guardar configuración de grabación',exact:true})).toBeDisabled();
 await p.getByRole('button',{name:'Conectar Drive',exact:true}).click();expect(writes(fx,'/api/recording-drive/connect')).toHaveLength(1);
 expect(writes(fx,'/api/captures/start')).toHaveLength(0);
 fx.provider.account_available=true;await p.getByRole('button',{name:'Actualizar conexión',exact:true}).click();
 await p.getByRole('button',{name:'Elegir carpeta de Drive',exact:true}).click();await save(page);
 expect(fx.preferences.destination_id).toBe('drive-chosen');expect(writes(fx,'/api/capture-exports/export-one/save')).toHaveLength(0);
 if(process.env.TUTORIAL_QA_DIR)await page.screenshot({path:process.env.TUTORIAL_QA_DIR+'/recording-drive-settings.png'});
});

test('cancelled folder choice does not replace the saved destination',async({page})=>{
 const fx=await setup(page,{cancelPicker:true});const p=await panel(page);await p.getByLabel('Destino de la grabación').selectOption('folder');
 await p.getByRole('button',{name:'Elegir carpeta',exact:true}).click();
 await expect(p.getByLabel('Carpeta elegida')).toHaveValue('');expect(fx.preferences.destination_id).toBeNull();
 await expect(p.getByRole('button',{name:'Guardar configuración de grabación',exact:true})).toBeDisabled();
});

test('unknown delivery acknowledgement is not replayed and verification remains explicit',async({page})=>{
 const fx=await setup(page,{loseCopy:true});const p=await panel(page);
 await p.getByLabel('Destino de la grabación').selectOption('folder');await p.getByRole('button',{name:'Elegir carpeta',exact:true}).click();await save(page);
 await page.getByRole('button',{name:'Grabar',exact:true}).click();await expect(page.getByRole('button',{name:'Detener y guardar',exact:true})).toBeEnabled();
 await page.getByRole('button',{name:'Detener y guardar',exact:true}).click();fx.finish();
 await expect.poll(()=>writes(fx,'/api/captures/take-one/export').length).toBe(1);fx.saved();
 await expect.poll(()=>writes(fx,'/api/capture-exports/export-one/save').length).toBe(1);
 fx.deliveries[0].status='unconfirmed';await page.waitForTimeout(1500);expect(writes(fx,'/api/capture-exports/export-one/save')).toHaveLength(1);
 await page.getByRole('button',{name:/^Tomas \(/}).click();await expect(page.getByText(/Guardado sin confirmación/)).toBeVisible();
 await page.getByRole('button',{name:'Verificar guardado',exact:true}).click();expect(writes(fx,'/api/recording-deliveries/delivery-one/verify')).toHaveLength(1);
});

test('recording setup remains legible on a narrow screen',async({page})=>{
 await page.setViewportSize({width:390,height:844});await setup(page);const p=await panel(page);
 expect(await p.evaluate(el=>el.scrollWidth<=el.clientWidth+1)).toBe(true);
 await expect(p.getByRole('button',{name:'Guardar configuración de grabación',exact:true})).toBeEnabled();
 if(process.env.TUTORIAL_QA_DIR)await p.screenshot({path:process.env.TUTORIAL_QA_DIR+'/recording-setup-narrow.png'});
});
