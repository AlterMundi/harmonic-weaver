import {expect} from '@playwright/test';
import {createHash} from 'node:crypto';

/** Native browser OPFS exercises serializable handles and real writes, never human folders. */
export async function browserFolder(page:any,{cancel=false,loseClose=false,unavailable=false}={}){
 await page.addInitScript(({cancel,loseClose,unavailable}:any)=>{
  const w=window as any;w.__folderWrites=0;w.__pickerCalls=0;w.__folderPermission='granted';
  if(unavailable){w.showDirectoryPicker=undefined;return;}
  FileSystemHandle.prototype.queryPermission=async()=>w.__folderPermission;
  FileSystemHandle.prototype.requestPermission=async()=>{w.__folderPermission='granted';return 'granted';};
  w.showDirectoryPicker=async()=>{w.__pickerCalls++;if(cancel)throw new DOMException('Cancelled','AbortError');const root=await navigator.storage.getDirectory();return root.getDirectoryHandle('Mis tomas',{create:true});};
  const original=FileSystemWritableFileStream.prototype.write;
  FileSystemWritableFileStream.prototype.write=async function(data:any){w.__folderWrites++;return original.call(this,data);};
  const close=FileSystemWritableFileStream.prototype.close;
  FileSystemWritableFileStream.prototype.close=async function(){await close.call(this);if(loseClose){loseClose=false;throw Error('Synthetic lost close acknowledgement');}};
 },{cancel,loseClose,unavailable});
}

export async function googleFixture(page:any,{loseUpload=false,badChecksum=false}={}){
 const calls:any[]=[];const files=new Map<string,any>();const cloud={account:'nico@example.test',calls,files};
 await page.addInitScript(()=>{
  const w=window as any;w.__googleRequests=0;w.__googleScopes='';w.__googlePicker=0;
  w.google={accounts:{oauth2:{hasGrantedAllScopes:()=>true,initTokenClient:(config:any)=>{
   w.__googleScopes=config.scope;
   return {requestAccessToken:()=>{w.__googleRequests++;config.callback({access_token:'synthetic-oauth-token',expires_in:3600,scope:config.scope});}};
  }}}};
  w.gapi={load:(_name:any,options:any)=>{
   class View{constructor(_id:any){}setIncludeFolders(){return this;}setSelectFolderEnabled(){return this;}setMimeTypes(){return this;}}
   class Picker{callback:any;addView(){return this;}setOAuthToken(){return this;}setDeveloperKey(){return this;}setAppId(){return this;}setOrigin(){return this;}setCallback(cb:any){this.callback=cb;return this;}build(){return this;}setVisible(){w.__googlePicker++;this.callback({action:'picked',docs:[{id:'chosen-folder'}]});}}
   w.google.picker={DocsView:View,ViewId:{FOLDERS:'folders'},PickerBuilder:Picker,Action:{PICKED:'picked',CANCEL:'cancel'}};options.callback();
  }};
 });
 await page.route('https://www.googleapis.com/**',async(route:any)=>{
  const req=route.request(),url=new URL(req.url()),path=url.pathname,body=req.method()==='POST'?req.postDataJSON():null;
  const fulfill=(value:any)=>route.fulfill({...value,headers:{'Access-Control-Allow-Origin':'*','Access-Control-Expose-Headers':'Location',...value.headers}});
  if(req.method()==='OPTIONS')return fulfill({status:204,headers:{'Access-Control-Allow-Headers':'Authorization, Content-Type, X-Upload-Content-Type, X-Upload-Content-Length','Access-Control-Allow-Methods':'GET,POST,PUT'},body:''});
  calls.push({method:req.method(),path,body});
  if(path==='/oauth2/v3/userinfo')return fulfill({json:{sub:cloud.account,email:cloud.account,email_verified:true}});
  if(path==='/drive/v3/files/chosen-folder')return fulfill({json:{id:'chosen-folder',name:'Mi estudio',mimeType:'application/vnd.google-apps.folder',capabilities:{canAddChildren:true}}});
  if(path==='/drive/v3/files/generateIds')return fulfill({json:{ids:Array.from({length:Number(url.searchParams.get('count'))},(_,i)=>'generated-'+i)}});
  if(path==='/upload/drive/v3/files'&&req.method()==='POST'){
   files.set(body.id,{id:body.id,name:body.name,parents:body.parents});return fulfill({status:200,headers:{Location:'https://www.googleapis.com/upload/drive/v3/files?upload_id='+body.id},body:''});
  }
  if(path==='/upload/drive/v3/files'&&req.method()==='PUT'){
   const id=url.searchParams.get('upload_id'),bytes=req.postDataBuffer();Object.assign(files.get(id),{size:String(bytes.length),sha256Checksum:badChecksum?'0'.repeat(64):createHash('sha256').update(bytes).digest('hex')});
   if(loseUpload){loseUpload=false;return route.abort();}return fulfill({json:{id}});
  }
  if(path.startsWith('/drive/v3/files/generated-'))return fulfill({json:files.get(path.split('/').pop())});
  throw Error('Unexpected synthetic Google operation: '+req.method()+' '+path);
 });
 return cloud;
}

export async function recordingPanel(page:any){await page.getByRole('button',{name:'Configurar grabación',exact:true}).click();return page.getByRole('region',{name:'Configuración de grabación',exact:true});}
export async function saveRecording(page:any){const p=page.getByRole('region',{name:'Configuración de grabación',exact:true});await p.getByRole('button',{name:'Guardar configuración de grabación',exact:true}).click();await expect(p.getByRole('status')).toContainText('Configuración guardada');}
export async function recordAndExport(page:any,fx:any){
 await page.getByRole('button',{name:'Grabar',exact:true}).click();await expect(page.getByRole('button',{name:'Detener y guardar',exact:true})).toBeEnabled();
 await page.getByRole('button',{name:'Detener y guardar',exact:true}).click();fx.finish();
 await expect.poll(()=>fx.calls.filter((c:any)=>c.path==='/api/captures/take-one/export').length).toBe(1);fx.saved();
}
export async function browserRecords(page:any){return page.evaluate(()=>new Promise<any>((resolve,reject)=>{const open=indexedDB.open('weaver-recording-v1',1);open.onsuccess=()=>{const db=open.result;const request=db.transaction('state').objectStore('state').getAll();request.onsuccess=()=>{db.close();resolve(request.result);};request.onerror=reject;};open.onerror=reject;}));}
