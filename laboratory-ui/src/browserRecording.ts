/** Browser-owned destinations. No OAuth token or client folder handle reaches the server. */
type Data=Record<string,any>;
export const defaultRecording={schema_version:1,max_seconds:300,include_audio:true,skeleton_overlay:true,harmonic_figure:false,format:'mp4',destination_id:null};
const database='weaver-recording-v1';
const driveScope='https://www.googleapis.com/auth/drive.file';
const googleApi='https://www.googleapis.com';
const clone=(value:any)=>JSON.parse(JSON.stringify(value));
const uid=()=>crypto.randomUUID().replaceAll('-','');
const digest=async(blob:Blob)=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',await blob.arrayBuffer()))).map(x=>x.toString(16).padStart(2,'0')).join('');
function openDatabase():Promise<IDBDatabase>{return new Promise((resolve,reject)=>{
 const request=indexedDB.open(database,1);
 request.onupgradeneeded=()=>request.result.createObjectStore('state');
 request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(Error('No se pudieron abrir los ajustes de este navegador.'));
});}
async function read(key:string){const db=await openDatabase();try{return await new Promise<any>((resolve,reject)=>{const request=db.transaction('state').objectStore('state').get(key);request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(Error('No se pudo leer la configuración de este navegador.'));});}finally{db.close();}}
async function write(key:string,value:any){const db=await openDatabase();try{await new Promise<void>((resolve,reject)=>{const tx=db.transaction('state','readwrite');tx.objectStore('state').put(value,key);tx.oncomplete=()=>resolve();tx.onerror=tx.onabort=()=>reject(Error('No se pudo conservar la configuración en este navegador.'));});}finally{db.close();}}
function loadScript(src:string):Promise<void>{return new Promise((resolve,reject)=>{
 const script=document.createElement('script');script.src=src;script.async=true;
 script.onload=()=>resolve();script.onerror=()=>{script.remove();reject(Error('No se pudo cargar la conexión de Google.'));};document.head.append(script);
});}
export class BrowserRecording {
 private api:any;private ready:Promise<void>;private preferences:Data={...defaultRecording};private destinations:Data[]=[];private jobs:Data[]=[];
 private handles=new Map<string,any>();private busy=false;private token='';private expires=0;private account='';private tokenClient:any=null;private googlePrepared=false;
 private config:Data;private preparing:Promise<void>|null=null;
 constructor(api:any){this.api=api;const env=(import.meta as any).env||{};this.config={clientId:env.VITE_GOOGLE_CLIENT_ID||'',apiKey:env.VITE_GOOGLE_API_KEY||'',appId:env.VITE_GOOGLE_APP_ID||''};this.ready=this.load();}
 private async load(){
  const stored=await read('preferences');
  if(stored){if(stored.schema_version!==1||typeof stored.include_audio!=='boolean')throw Error('Los ajustes guardados no son compatibles.');this.preferences={...defaultRecording,...stored};}
  this.destinations=await read('destinations')||[];this.jobs=await read('deliveries')||[];
  for(const destination of this.destinations)if(destination.kind==='folder')this.handles.set(destination.id,await read('handle-'+destination.id));

 }
 private connected(){return !!this.token&&Date.now()<this.expires;}
 async provider(){await this.ready;return {account:this.connected()?this.account:'',account_available:this.connected(),connect_available:!!navigator.locks&&!!(this.config.clientId&&this.config.apiKey&&this.config.appId)&&window.isSecureContext,prepared:this.googlePrepared,
  folder_available:!!navigator.locks&&window.isSecureContext&&typeof (window as any).showDirectoryPicker==='function'};}
 async preferencesGet(){await this.ready;const value=await read('preferences');if(value)this.preferences={...defaultRecording,...value};return clone(this.preferences);}
 async save(value:Data){await this.ready;
  if(!Number.isFinite(value.max_seconds)||value.max_seconds<1||value.max_seconds>300||!['mp4','mkv','both'].includes(value.format)||['include_audio','skeleton_overlay','harmonic_figure'].some(k=>typeof value[k]!=='boolean'))throw Error('Revisá la configuración de grabación.');
  if(value.destination_id&&(!this.destinations.some(d=>d.id===value.destination_id)||!await this.canUse(value.destination_id)))throw Error('Elegí y autorizá tu destino en este navegador.');
  const next={...defaultRecording,...Object.fromEntries(Object.keys(defaultRecording).map(k=>[k,value[k]]))};await write('preferences',next);this.preferences=next;return clone(next);
 }
 async destinationList(){await this.ready;this.destinations=await read('destinations')||[];for(const d of this.destinations)if(d.kind==='folder'&&!this.handles.has(d.id))this.handles.set(d.id,await read('handle-'+d.id));return clone(this.destinations);}
 async pickFolder(){
  // Invoke before any awaited storage operation: the picker requires this click's activation.
  if(!window.isSecureContext||typeof (window as any).showDirectoryPicker!=='function')throw Error('Este navegador no permite elegir carpetas. Usá Descargar en esta computadora.');
  let handle:any;try{handle=await (window as any).showDirectoryPicker({mode:'readwrite',id:'weaver-recordings'});}catch(e:any){if(e.name==='AbortError')return {status:'cancelled'};throw Error('No se autorizó la carpeta.');}
  await this.ready;const row={id:uid(),kind:'folder',label:handle.name};await write('handle-'+row.id,handle);
  this.destinations.push(row);await write('destinations',this.destinations);this.handles.set(row.id,handle);return {status:'selected',destination:clone(row)};
 }
 async authorizeFolder(id:string){const handle=this.handles.get(id);if(!handle)throw Error('Volvé a elegir la carpeta en esta computadora.');if(await handle.requestPermission({mode:'readwrite'})!=='granted')throw Error('La carpeta no tiene permiso de escritura.');}
 async prepareGoogle(){
  if(!(await this.provider()).connect_available)throw Error('La instalación todavía no tiene configurada la conexión web de Google Drive.');
  if(this.googlePrepared)return;
  if(!this.preparing)this.preparing=(async()=>{
   if(!(window as any).google?.accounts?.oauth2)await loadScript('https://accounts.google.com/gsi/client');
   if(!(window as any).gapi)await loadScript('https://apis.google.com/js/api.js');
   await new Promise<void>((resolve,reject)=>(window as any).gapi.load('picker',{callback:resolve,onerror:()=>reject(Error('No se pudo cargar el selector de Drive.')),timeout:15000,ontimeout:()=>reject(Error('El selector de Drive no respondió.'))}));
   this.googlePrepared=true;
  })().finally(()=>{this.preparing=null;});
  return this.preparing;
 }
 connectGoogle():Promise<void>{
  if(!this.googlePrepared)return Promise.reject(Error('Prepará primero la conexión de Drive.'));
  this.token='';this.account='';this.expires=0;
  return new Promise((resolve,reject)=>{
   this.tokenClient=(window as any).google.accounts.oauth2.initTokenClient({client_id:this.config.clientId,scope:driveScope+' openid email',include_granted_scopes:false,
    callback:(response:Data)=>{void(async()=>{
     if(response.error||!response.access_token||!(window as any).google.accounts.oauth2.hasGrantedAllScopes(response,driveScope))throw Error('No se autorizó el acceso a los archivos elegidos.');
     const user=await fetch(googleApi+'/oauth2/v3/userinfo',{headers:{Authorization:'Bearer '+response.access_token},credentials:'omit'});
     if(!user.ok)throw Error('No se pudo comprobar la cuenta de Google.');const info=await user.json();
     if(!info.email||!info.sub||info.email_verified!==true)throw Error('Google no confirmó la cuenta.');
     this.token=response.access_token;this.account=info.email;this.expires=Date.now()+Math.max(0,Number(response.expires_in)-30)*1000;resolve();
    })().catch(()=>{this.token='';this.account='';this.expires=0;reject(Error('No se confirmó la conexión a Drive. Volvé a conectar tu cuenta.'));});},
    error_callback:()=>reject(Error('Se cerró o bloqueó la conexión de Google.'))});
   // Keep the popup inside the explicit click, with no awaited work before it.
   this.tokenClient.requestAccessToken({prompt:'select_account'});
  });
 }
 disconnectGoogle(){this.token='';this.account='';this.expires=0;this.tokenClient=null;}
 private async google(path:string,init:RequestInit={}){if(!this.connected())throw Error('Conectá de nuevo tu cuenta de Drive.');
  const response=await fetch(googleApi+path,{...init,credentials:'omit',headers:{...init.headers,Authorization:'Bearer '+this.token},signal:AbortSignal.timeout(120000)});
  if(!response.ok)throw Error('Google no confirmó la operación. Revisá la conexión y los permisos.');return response;
 }
 async pickDrive(){if(!this.connected())throw Error('Conectá tu cuenta antes de elegir una carpeta.');
  const account=this.account;const picker=(window as any).google.picker;
  const choice:any=await new Promise((resolve)=>{
   const view=new picker.DocsView(picker.ViewId.FOLDERS).setIncludeFolders(true).setSelectFolderEnabled(true).setMimeTypes('application/vnd.google-apps.folder');
   new picker.PickerBuilder().addView(view).setOAuthToken(this.token).setDeveloperKey(this.config.apiKey).setAppId(this.config.appId).setOrigin(window.location.origin)
    .setCallback((data:Data)=>{if(data.action===picker.Action.PICKED)resolve(data.docs?.[0]);else if(data.action===picker.Action.CANCEL)resolve(null);}).build().setVisible(true);
  });
  if(!choice)return {status:'cancelled'};if(account!==this.account||!this.connected())throw Error('La cuenta cambió; volvé a elegir la carpeta.');
  const info=await(await this.google('/drive/v3/files/'+encodeURIComponent(choice.id)+'?fields=id,name,mimeType,driveId,capabilities(canAddChildren)&supportsAllDrives=true')).json();
  if(info.driveId)throw Error('Por ahora elegí una carpeta de Mi unidad; las unidades compartidas requieren otra configuración.');
  if(info.mimeType!=='application/vnd.google-apps.folder'||!info.capabilities?.canAddChildren)throw Error('Elegí una carpeta con permiso para guardar archivos.');
  await this.ready;const row={id:uid(),kind:'drive',label:info.name,folder_id:info.id,account};this.destinations.push(row);await write('destinations',this.destinations);return {status:'selected',destination:clone(row)};
 }
 async canUse(id:string|null){await this.ready;if(!id)return true;const destination=this.destinations.find(d=>d.id===id);if(!destination)return false;
  if(destination.kind==='drive')return this.connected()&&this.account===destination.account;
  const handle=this.handles.get(id);return !!handle&&await handle.queryPermission({mode:'readwrite'})==='granted';
 }
 async list(){await this.ready;
  if(!navigator.locks)return clone(await read('deliveries')||[]);
  return navigator.locks.request('weaver-recording-copy',{ifAvailable:true},async lock=>{
   const rows:Data[]=await read('deliveries')||[];let changed=false;
   if(lock)for(const job of rows)if(['copying','verifying'].includes(job.status)){job.status='unconfirmed';changed=true;}
   if(changed)await write('deliveries',rows);return clone(rows);
  });
 }
 private lease(action:(resolve:(value:any)=>void)=>Promise<void>):Promise<any>{return new Promise((resolve,reject)=>{
  if(!navigator.locks){reject(Error('Este navegador no permite copias verificadas; elegí Descargar.'));return;}
  void navigator.locks.request('weaver-recording-copy',{ifAvailable:true},async lock=>{
   if(!lock)throw Object.assign(Error('Hay un guardado en curso en otra pestaña.'),{status:409});
   this.jobs=await read('deliveries')||[];await action(resolve);
  }).catch(reject);
 });}

 private async persist(){await write('deliveries',clone(this.jobs));}
 async start(exportId:string,request:Data){await this.ready;return this.lease(async resolve=>{
  const retained=this.jobs.find(j=>j.export_id===exportId&&j.destination.id===request.destination_id&&j.format===request.format&&j.status!=='not_saved');if(retained){resolve(clone(retained));return;}
  if(this.busy)throw Object.assign(Error('Esperá a que termine la copia en curso.'),{status:409});
  if(!['mp4','mkv','both'].includes(request.format))throw Error('Formato inválido.');
  const destination=this.destinations.find(d=>d.id===request.destination_id);if(!destination||!await this.canUse(destination.id))throw Error('Autorizá el destino en el menú Grabar.');
  // Recheck after asynchronous permission lookup so concurrent clicks cannot start two copies.
  if(this.busy)throw Object.assign(Error('Esperá a que termine la copia en curso.'),{status:409});
  const job={id:uid(),export_id:exportId,destination:clone(destination),format:request.format,status:'copying',files:[] as Data[],error:null};this.busy=true;this.jobs.push(job);
  try{await this.persist();}catch(e){this.jobs.pop();this.busy=false;throw e;}
  resolve(clone(job));await this.work(job,false);
 });}
 async verify(id:string){await this.ready;return this.lease(async resolve=>{if(this.busy)throw Error('Esperá a que termine el guardado.');const job=this.jobs.find(j=>j.id===id);if(!job)throw Error('Copia desconocida.');
  if(!await this.canUse(job.destination.id))throw Error('Autorizá el mismo destino y cuenta en Grabar antes de verificar.');
  if(this.busy)throw Error('Esperá a que termine el guardado.');this.busy=true;job.status='verifying';try{await this.persist();}catch(e){this.busy=false;throw e;}resolve(clone(job));await this.work(job,true);
 });}
 private async work(job:Data,verify:boolean){try{
  if(!verify){
   const exports:Data[]=await this.api('capture-exports/jobs');const exported=exports.find(j=>j.id===job.export_id&&j.status==='complete');if(!exported)throw Error('La exportación todavía no está lista.');
   const names=job.format==='both'?['preview.mp4','capture.mkv']:[job.format==='mkv'?'capture.mkv':'preview.mp4'];
   for(const name of names){const sha=name==='preview.mp4'?exported.preview?.sha256:exported.output?.sha256;if(!/^[0-9a-f]{64}$/.test(sha||''))throw Error('Falta la verificación del original.');job.files.push({artifact:name,filename:`HarmoCap-${job.export_id.slice(0,8)}-${job.id.slice(0,8)}.${name.split('.').pop()}`,sha256:sha});}
   if(job.destination.kind==='drive'){
    const generated=await(await this.google('/drive/v3/files/generateIds?count='+names.length+'&space=drive&type=files')).json();if(generated.ids?.length!==names.length)throw Error('No se confirmó la reserva de archivos de Drive.');job.files.forEach((f:Data,i:number)=>f.drive_id=generated.ids[i]);
   }
   // Persist planned names and pre-generated Drive IDs before any destination write.
   await this.persist();
  }
  if(!job.files.length){job.status='not_saved';job.error='No se inició la copia. Podés guardar el video de nuevo.';return;}
  for(const file of job.files){
   if(!verify){
    const response=await fetch(`/api/capture-exports/${encodeURIComponent(job.export_id)}/artifacts/${file.artifact}`,{credentials:'same-origin',signal:AbortSignal.timeout(120000)});if(!response.ok)throw Error('El video original no está disponible.');const blob=await response.blob();
    if(await digest(blob)!==file.sha256)throw Error('El video recibido no coincide con el original.');file.size=blob.size;await this.persist();
    if(job.destination.kind==='folder'){
     const folder=this.handles.get(job.destination.id);let target:any;
     try{target=await folder.getFileHandle(file.filename);}catch(e:any){if(e.name!=='NotFoundError')throw e;}
     if(target)throw Error('Ya existe ese archivo; verificá el guardado antes de repetirlo.');
     target=await folder.getFileHandle(file.filename,{create:true});const stream=await target.createWritable();try{await stream.write(blob);await stream.close();}catch(e){try{await stream.abort();}catch{}throw e;}
    }else{
     if(!this.connected()||job.destination.account!==this.account)throw Error('Conectá la cuenta que elegiste para esta copia.');
     const initiated=await this.google('/upload/drive/v3/files?uploadType=resumable&supportsAllDrives=true',{method:'POST',headers:{'Content-Type':'application/json','X-Upload-Content-Type':blob.type||'application/octet-stream','X-Upload-Content-Length':String(blob.size)},body:JSON.stringify({id:file.drive_id,name:file.filename,parents:[job.destination.folder_id]})});
     const location=initiated.headers.get('Location');if(!location)throw Error('Drive no confirmó la sesión de subida.');
     const url=new URL(location);if(url.origin!==googleApi||url.pathname!=='/upload/drive/v3/files')throw Error('Sesión de subida de Drive inválida.');
     // The upload session URL is private and deliberately never persisted or logged.
     const uploaded=await fetch(url.href,{method:'PUT',credentials:'omit',headers:{'Content-Type':blob.type||'application/octet-stream'},body:blob,signal:AbortSignal.timeout(300000)});if(!uploaded.ok)throw Error('La subida quedó sin confirmar.');
    }
   }
   if(job.destination.kind==='folder'){
    const handle=await this.handles.get(job.destination.id).getFileHandle(file.filename);const saved=await handle.getFile();
    if(saved.size!==file.size||await digest(saved)!==file.sha256)throw Error('La copia no coincide con el original.');
   }else{
    if(!this.connected()||job.destination.account!==this.account)throw Error('Conectá la misma cuenta para verificar.');
    const saved=await(await this.google('/drive/v3/files/'+encodeURIComponent(file.drive_id)+'?fields=id,name,size,sha256Checksum,parents,trashed&supportsAllDrives=true')).json();
    if(saved.trashed||saved.name!==file.filename||Number(saved.size)!==file.size||saved.sha256Checksum!==file.sha256||!saved.parents?.includes(job.destination.folder_id))throw Error('Drive todavía no confirmó la copia exacta.');
   }
  }
  job.status='complete';job.error=null;
 }catch{job.status='unconfirmed';job.error='No se confirmó la copia. Los originales siguen en Tomas; verificá antes de repetir.';}
 finally{try{await this.persist();}catch{job.status='unconfirmed';job.error='No se pudo conservar la confirmación en este navegador.';}this.busy=false;}}
}
