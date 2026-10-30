import {test,expect} from '@playwright/test';
import {setupRecording as setup} from './recordingFixture';
import {browserFolder,googleFixture,recordingPanel as panel,saveRecording as save,recordAndExport,browserRecords} from './browserRecordingFixture';
const writes=(fx:any,path:string)=>fx.calls.filter((r:any)=>r.path===path);

test('settings persist in this browser without modifying the server or instrument',async({page,browser})=>{
 const fx=await setup(page),preset=JSON.stringify(fx.state.preset),p=await panel(page);
 const nav=await page.getByRole('navigation',{name:'Secciones del laboratorio'}).getByRole('button').allTextContents();expect(nav.indexOf('Grabar')).toBe(nav.indexOf('Captura')+1);
 await p.getByRole('button',{name:'Solo video y música',exact:true}).click();await p.getByLabel('Visualizador cimático junto al video',{exact:true}).check();await p.getByLabel('Duración máxima de grabación').fill('60');await save(page);
 expect(fx.calls).toEqual([]);expect(JSON.stringify(fx.state.preset)).toBe(preset);
 await page.reload();const again=await panel(page);await expect(again.getByLabel('Visualizador cimático junto al video',{exact:true})).toBeChecked();await expect(again.getByLabel('Duración máxima de grabación')).toHaveValue('60');
 const other=await browser.newContext({baseURL:process.env.LAB_URL});try{const q=await other.newPage();await setup(q);const independent=await panel(q);await expect(independent.getByLabel('Duración máxima de grabación')).toHaveValue('300');await expect(independent.getByLabel('Visualizador cimático junto al video',{exact:true})).not.toBeChecked();}finally{await other.close();}
 expect(fx.errors).toEqual([]);
});

test('the next take uses browser settings and recording locks the form',async({page})=>{
 const fx=await setup(page),p=await panel(page);await p.getByLabel('Sonido de HarmoCap en el video',{exact:true}).uncheck();await p.getByLabel('Líneas de movimiento sobre el cuerpo',{exact:true}).uncheck();await p.getByLabel('Visualizador cimático junto al video',{exact:true}).check();await save(page);
 await page.getByRole('button',{name:'Grabar',exact:true}).click();await expect(p.getByLabel('Visualizador cimático junto al video',{exact:true})).toBeDisabled();
 await page.getByRole('button',{name:'Detener y guardar',exact:true}).click();fx.finish();await expect.poll(()=>writes(fx,'/api/captures/take-one/export').length).toBe(1);
 expect(writes(fx,'/api/captures/take-one/export')[0].body).toMatchObject({include_audio:false,skeleton_overlay:false,harmonic_figure:true});
});

test('the client folder receives real verified bytes only after confirmed export',async({page})=>{
 await browserFolder(page);const fx=await setup(page),p=await panel(page);await p.getByLabel('Destino de la grabación').selectOption('folder');await p.getByRole('button',{name:'Elegir carpeta',exact:true}).click();await expect(p).toContainText('Mis tomas');await save(page);
 expect(await page.evaluate(()=>(window as any).__folderWrites)).toBe(0);await recordAndExport(page,fx);
 await page.getByRole('button',{name:/^Tomas \(/}).click();await expect(page.getByText(/Copia en carpeta verificada/)).toBeVisible();
 const jobs=(await browserRecords(page)).find((v:any)=>Array.isArray(v)&&v[0]?.export_id);expect(jobs[0].status).toBe('complete');expect(jobs[0].files[0].size).toBeGreaterThan(1000);
 expect(await page.evaluate(()=>(window as any).__folderWrites)).toBe(1);expect(fx.calls.filter((c:any)=>/recording-|\/save$/.test(c.path))).toEqual([]);
 await page.reload();await page.getByRole('button',{name:/^Tomas \(/}).click();await expect(page.getByText(/Copia en carpeta verificada/)).toBeVisible();expect(await page.evaluate(()=>(window as any).__folderWrites)).toBe(0);expect(fx.errors).toEqual([]);
});

test('cancelled folder and unsupported picker preserve the download route',async({page})=>{
 await browserFolder(page,{cancel:true});await setup(page);const p=await panel(page);await p.getByLabel('Destino de la grabación').selectOption('folder');await p.getByRole('button',{name:'Elegir carpeta',exact:true}).click();await expect(p.getByLabel('Carpeta elegida')).toHaveValue('');await expect(p.getByRole('button',{name:'Guardar configuración de grabación',exact:true})).toBeDisabled();
 await p.getByLabel('Destino de la grabación').selectOption('download');await save(page);await expect(p).toContainText('El navegador decide la carpeta');

});

test('unsupported browser offers downloads and never calls a server picker',async({page})=>{
 await browserFolder(page,{unavailable:true});const fx=await setup(page),p=await panel(page);await p.getByLabel('Destino de la grabación').selectOption('folder');await expect(p.getByRole('button',{name:'Elegir carpeta',exact:true})).toBeDisabled();await expect(p).toContainText('Este navegador no permite elegir carpetas');await p.getByLabel('Destino de la grabación').selectOption('download');await save(page);expect(fx.calls).toEqual([]);
});

test('lost local close acknowledgement is verified without writing the file twice',async({page})=>{
 await browserFolder(page,{loseClose:true});const fx=await setup(page),p=await panel(page);await p.getByLabel('Destino de la grabación').selectOption('folder');await p.getByRole('button',{name:'Elegir carpeta',exact:true}).click();await save(page);await recordAndExport(page,fx);
 await page.getByRole('button',{name:/^Tomas \(/}).click();await expect(page.getByText(/Guardado sin confirmación/)).toBeVisible();expect(await page.evaluate(()=>(window as any).__folderWrites)).toBe(1);
 await page.getByRole('button',{name:'Verificar guardado',exact:true}).click();await expect(page.getByText(/Copia en carpeta verificada/)).toBeVisible();expect(await page.evaluate(()=>(window as any).__folderWrites)).toBe(1);
});

test('a second tab sees an active copy without marking it uncertain or duplicating it',async({page,context})=>{
 await browserFolder(page);const fx=await setup(page,{existing:true}),p=await panel(page);
 await p.getByLabel('Destino de la grabación').selectOption('folder');await p.getByRole('button',{name:'Elegir carpeta',exact:true}).click();await save(page);
 let release:any;const gate=new Promise<void>(resolve=>release=resolve);
 await page.route('**/artifacts/preview.mp4',async(route:any)=>{await gate;await route.continue();});
 await page.getByRole('button',{name:/^Tomas \(/}).click();await page.getByRole('button',{name:'Guardar copia en destino elegido',exact:true}).click();
 const second=await context.newPage();try{
  await browserFolder(second);await setup(second,{existing:true});await second.getByRole('button',{name:/^Tomas \(/}).click();
  await expect(second.getByText(/Guardando y verificando/)).toBeVisible();await expect(second.getByRole('button',{name:'Guardar copia en destino elegido',exact:true})).toBeDisabled();
  release();await expect(second.getByText(/Copia en carpeta verificada/)).toBeVisible();expect(await page.evaluate(()=>(window as any).__folderWrites)).toBe(1);
 }finally{release();await second.close();}
 expect(fx.errors).toEqual([]);
});

test('expired folder permission requires an explicit authorization click',async({page})=>{
 await browserFolder(page);await setup(page);const p=await panel(page);await p.getByLabel('Destino de la grabación').selectOption('folder');await p.getByRole('button',{name:'Elegir carpeta',exact:true}).click();await save(page);
 await page.evaluate(()=>{(window as any).__folderPermission='denied';});await expect(page.getByRole('button',{name:'Grabar',exact:true})).toBeDisabled({timeout:8000});
 await p.getByRole('button',{name:'Autorizar carpeta',exact:true}).click();await expect(page.getByRole('button',{name:'Grabar',exact:true})).toBeEnabled();
});

async function chooseDrive(page:any){const p=await panel(page);await p.getByLabel('Destino de la grabación').selectOption('drive');await p.getByRole('button',{name:'Preparar Drive',exact:true}).click();await p.getByRole('button',{name:'Conectar Drive',exact:true}).click();await expect(p).toContainText('Cuenta conectada:');await p.getByRole('button',{name:'Elegir carpeta de Drive',exact:true}).click();await expect(p).toContainText('Mi estudio');await save(page);return p;}

test('Drive uses the browser account and minimal picker grant, never a native server account',async({page})=>{
 const cloud=await googleFixture(page);const fx=await setup(page);expect(cloud.calls).toEqual([]);const p=await chooseDrive(page);await expect(p).toContainText('nico@example.test');expect(cloud.calls.filter(c=>c.method!=='GET')).toEqual([]);
 const scopes=await page.evaluate(()=>(window as any).__googleScopes);expect(scopes).toContain('https://www.googleapis.com/auth/drive.file');expect(scopes).not.toMatch(/auth\/drive\s/);
 await recordAndExport(page,fx);await page.getByRole('button',{name:/^Tomas \(/}).click();await expect(page.getByText(/Subida a Drive verificada/)).toBeVisible();expect(cloud.calls.filter(c=>c.method==='PUT')).toHaveLength(1);
 expect(JSON.stringify(await browserRecords(page))).not.toContain('synthetic-oauth-token');expect(await page.evaluate(()=>JSON.stringify([localStorage,sessionStorage]))).not.toContain('synthetic-oauth-token');expect(fx.calls.filter((c:any)=>/recording-|\/save$/.test(c.path))).toEqual([]);
 if(process.env.TUTORIAL_QA_DIR){await page.getByRole('button',{name:'Cerrar tomas',exact:true}).click();await p.screenshot({path:process.env.TUTORIAL_QA_DIR+'/browser-drive.png'});}
});

test('reload requires fresh Drive consent and a different account cannot reuse the old folder',async({page})=>{
 const cloud=await googleFixture(page);await setup(page);await chooseDrive(page);await page.reload();await expect(page.getByRole('button',{name:'Grabar',exact:true})).toBeDisabled();const p=await panel(page);await expect(p).toContainText('volvé a autorizar');expect(await page.evaluate(()=>(window as any).__googleRequests)).toBe(0);
 cloud.account='annie@example.test';await p.getByRole('button',{name:'Preparar Drive',exact:true}).click();await p.getByRole('button',{name:'Conectar Drive',exact:true}).click();await expect(p).toContainText('Cuenta conectada: annie@example.test');await expect(p.getByRole('button',{name:'Guardar configuración de grabación',exact:true})).toBeDisabled();expect(cloud.calls.filter(c=>c.method!=='GET')).toEqual([]);
 await p.getByLabel('Destino de la grabación').selectOption('download');await save(page);await expect(page.getByRole('button',{name:'Grabar',exact:true})).toBeEnabled();
});

test('uncertain Google upload acknowledgement is resolved by exact ID without retransmission',async({page})=>{
 const cloud=await googleFixture(page,{loseUpload:true});const fx=await setup(page);await chooseDrive(page);await recordAndExport(page,fx);await page.getByRole('button',{name:/^Tomas \(/}).click();await expect(page.getByText(/Guardado sin confirmación/)).toBeVisible();await page.getByRole('button',{name:'Verificar guardado',exact:true}).click();await expect(page.getByText(/Subida a Drive verificada/)).toBeVisible();expect(cloud.calls.filter(c=>c.method==='PUT')).toHaveLength(1);expect(cloud.calls.filter(c=>c.path==='/upload/drive/v3/files'&&c.method==='POST')).toHaveLength(1);
});

test('a bad Drive checksum never becomes a successful upload',async({page})=>{
 const cloud=await googleFixture(page,{badChecksum:true});const fx=await setup(page);await chooseDrive(page);await recordAndExport(page,fx);await page.getByRole('button',{name:/^Tomas \(/}).click();await expect(page.getByText(/Guardado sin confirmación/)).toBeVisible();await expect(page.getByText(/Subida a Drive verificada/)).toHaveCount(0);expect(cloud.calls.filter(c=>c.method==='PUT')).toHaveLength(1);
});

test('recording setup fits narrow screens and explains the client destination',async({page})=>{
 await page.setViewportSize({width:390,height:844});await setup(page);const p=await panel(page);expect(await p.evaluate(el=>el.scrollWidth<=el.clientWidth+1)).toBe(true);await expect(p).toContainText('computadora donde abriste esta web');if(process.env.TUTORIAL_QA_DIR)await p.screenshot({path:process.env.TUTORIAL_QA_DIR+'/browser-recording-narrow.png'});
});
