import {useCallback,useEffect,useMemo,useState} from 'react';
import {useConfirmedPolling} from './useConfirmedPolling';
import {BrowserRecording,defaultRecording} from './browserRecording';
export {defaultRecording} from './browserRecording';
type Data=Record<string,any>;
const paths=['captures','capture-exports','capture-exports/jobs','recording-deliveries'];

export function useRecordingSetup(api:any){
 const storage=useMemo(()=>new BrowserRecording(api),[api]);
 const destinationApi=useCallback((path:string,body?:Data)=>{
  if(path==='recording-deliveries')return storage.list();
  const copy=path.match(/^capture-exports\/([^/]+)\/save$/);if(copy)return storage.start(decodeURIComponent(copy[1]),body||{});
  const verify=path.match(/^recording-deliveries\/([^/]+)\/verify$/);if(verify)return storage.verify(decodeURIComponent(verify[1]));
  return api(path,body);
 },[api,storage]);
 const poll=useConfirmedPolling(destinationApi,paths,[{current:{status:'idle'},jobs:[]},{status:'idle'},[],[]],750);
 const [preferences,setPreferences]=useState<Data>(defaultRecording),[ready,setReady]=useState(false),[error,setError]=useState('');
 const [destinations,setDestinations]=useState<Data[]>([]),[provider,setProvider]=useState<Data>({}),[destinationReady,setDestinationReady]=useState(false);
 const reloadDestinations=useCallback(async()=>{
  const [prefs,rows,cloud]=await Promise.all([storage.preferencesGet(),storage.destinationList(),storage.provider()]);
  const available=await storage.canUse(prefs.destination_id);setPreferences(prefs);setDestinations(rows);setProvider(cloud);setDestinationReady(available);
 },[storage]);
 useEffect(()=>{let live=true;
  void reloadDestinations().then(()=>{if(live){setReady(true);setError('');}}).catch((e:any)=>{if(live)setError(String(e));});
  const interval=setInterval(()=>{void reloadDestinations().catch((e:any)=>{if(live)setError(String(e));});},5000);
  return()=>{live=false;clearInterval(interval);};
 },[reloadDestinations]);
 const save=async(value:Data)=>{const result=await storage.save(value);await reloadDestinations();setReady(true);setError('');return result;};
 return {poll,preferences,ready,error,destinations,provider,reloadDestinations,save,storage,destinationApi,destinationReady};
}

export function RecordingSetup({api,recording}:{api:any;recording:ReturnType<typeof useRecordingSetup>}){
 const {preferences,destinations,provider,poll}=recording;
 const [draft,setDraft]=useState<Data>(preferences),[dirty,setDirty]=useState(false),[mode,setMode]=useState('download');
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[status,setStatus]=useState('');
 const active=['starting','recording','stopping'].includes(poll.data[0].current?.status)||poll.data[1].status==='rendering'||poll.data[3].some((job:Data)=>['copying','verifying'].includes(job.status));
 const blocked=active||busy||!recording.ready;
 useEffect(()=>{if(dirty)return;setDraft(preferences);setMode(preferences.destination_id?destinations.find(d=>d.id===preferences.destination_id)?.kind||'unknown':'download');},[preferences,destinations,dirty]);
 const change=(values:Data)=>{setDraft(previous=>({...previous,...values}));setDirty(true);setStatus('');};
 const act=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');try{await fn()}catch(e){setError(String(e))}finally{setBusy(false);}};
 const choose=()=>act(async()=>{
  const result=await (mode==='folder'?recording.storage.pickFolder():recording.storage.pickDrive());
  if(result.status==='cancelled')return;
  await recording.reloadDestinations();change({destination_id:result.destination.id});
 });
 const selected=destinations.find(d=>d.id===draft.destination_id);
 const savedDestination=destinations.find(d=>d.id===preferences.destination_id);
 return <section aria-label="Configuración de grabación">
  <h2>Grabar y guardar</h2>
  <p>Elegí qué incluir y dónde guardar una copia en la computadora donde abriste esta web. Estos ajustes son propios de tu navegador.</p>
  <p>Configuración actual: {savedDestination?`${savedDestination.kind==='drive'?'Drive':'Carpeta'} · ${savedDestination.label}`:preferences.destination_id?'Destino guardado sin conexión confirmada':'Descarga en esta computadora'} · {preferences.format?.toUpperCase()}</p>
  <fieldset disabled={blocked}><legend>Qué incluir en el video</legend>
   <button onClick={()=>change({include_audio:true,skeleton_overlay:false,harmonic_figure:false})}>Solo video y música</button>
   <label className="check"><input type="checkbox" checked={draft.include_audio} onChange={e=>change({include_audio:e.target.checked})}/>Sonido de HarmoCap en el video</label>
   <label className="check"><input type="checkbox" checked={draft.skeleton_overlay} onChange={e=>change({skeleton_overlay:e.target.checked})}/>Líneas de movimiento sobre el cuerpo</label>
   <label className="check"><input type="checkbox" checked={draft.harmonic_figure} onChange={e=>change({harmonic_figure:e.target.checked})}/>Visualizador cimático junto al video</label>
   <p>La figura se dibuja con los armónicos grabados. Las líneas siguen los puntos corporales observados.</p>
   <div className="fields"><label>Duración máxima (segundos)<input aria-label="Duración máxima de grabación" type="number" min="1" max="300" value={draft.max_seconds} onChange={e=>change({max_seconds:Number(e.target.value)})}/></label>
   <label>Formato de la copia<select aria-label="Formato de la copia" value={draft.format} onChange={e=>change({format:e.target.value})}><option value="mp4">MP4 · fácil de reproducir</option><option value="mkv">MKV · original de trabajo</option><option value="both">MP4 y MKV</option></select></label></div>
  </fieldset>
  <fieldset disabled={blocked}><legend>Dónde guardar</legend>
   <label>Destino de la grabación<select aria-label="Destino de la grabación" value={mode} onChange={e=>{setMode(e.target.value);change({destination_id:null});}}>
    <option value="download">Descargar en esta computadora</option><option value="folder">Carpeta de esta computadora</option><option value="drive">Google Drive</option>{mode==='unknown'&&<option value="unknown">Destino guardado sin consultar</option>}
   </select></label>
   {mode==='folder'&&!provider.folder_available&&<p>Este navegador no permite elegir carpetas directamente. Usá Chrome o Edge con HTTPS o localhost, o elegí Descargar en esta computadora. También podés elegir una carpeta de Google Drive si la tenés sincronizada.</p>}
   {mode==='drive'&&<>
    <p>{provider.account_available?`Cuenta conectada: ${provider.account}`:'Cada persona conecta su propia cuenta de Google. Podés elegir la institucional o la tuya.'}</p>
    {!provider.connect_available&&<p>Esta instalación todavía no habilitó la conexión web de Drive. Mientras tanto, podés descargar el video o elegir una carpeta sincronizada con Drive. <a href="https://github.com/AlterMundi/harmonic-weaver/blob/main/docs/laboratory/RECORDING_SETUP.md#google-drive-in-the-browser" target="_blank" rel="noopener noreferrer">Cómo habilitar Drive</a></p>}
    <div className="actions">{!provider.account_available?<button disabled={!provider.connect_available} onClick={()=>void act(async()=>{if(!provider.prepared){await recording.storage.prepareGoogle();setStatus('Conexión preparada. Pulsá Conectar Drive para elegir tu cuenta.');}else{await recording.storage.connectGoogle();setStatus('Cuenta conectada. Elegí una carpeta de Drive.');}await recording.reloadDestinations();})}>{provider.prepared?'Conectar Drive':'Preparar Drive'}</button>:
     <button onClick={()=>void act(async()=>{recording.storage.disconnectGoogle();await recording.reloadDestinations();setStatus('Cuenta desconectada de esta página.');})}>Desconectar Drive</button>}</div>
   </>}
   {['folder','drive'].includes(mode)&&<>
    <label>Carpeta elegida<select aria-label="Carpeta elegida" value={draft.destination_id||''} onChange={e=>change({destination_id:e.target.value||null})}>
     <option value="">Elegí una carpeta</option>{destinations.filter(d=>d.kind===mode&&(mode!=='drive'||d.account===provider.account)).map(d=><option key={d.id} value={d.id}>{d.label}</option>)}
    </select></label>
    <button disabled={mode==='drive'?!provider.account_available:!provider.folder_available} onClick={()=>void choose()}>Elegir carpeta{mode==='drive'?' de Drive':''}</button>
    <p>El selector se abre en esta computadora. No se cambia la carpeta de otra persona.</p>
    {selected?.kind==='folder'&&!recording.destinationReady&&<button onClick={()=>void act(async()=>{await recording.storage.authorizeFolder(selected.id);await recording.reloadDestinations();setStatus('Carpeta autorizada en este navegador.');})}>Autorizar carpeta</button>}
    {selected&&<p>Destino: {selected.label}{selected.account?` · ${selected.account}`:''}</p>}
   </>}
   <p>Los originales quedan en la biblioteca del laboratorio que está procesando la cámara. La copia va a tu computadora o a la cuenta de Drive que elegiste; Drive no comparte archivos automáticamente.</p>
  </fieldset>
  <button disabled={blocked||mode==='unknown'||mode==='drive'&&(!provider.account_available||selected?.account!==provider.account)||mode!=='download'&&!draft.destination_id||!Number.isFinite(draft.max_seconds)||draft.max_seconds<1||draft.max_seconds>300}
   onClick={()=>void act(async()=>{await recording.save(draft);setDirty(false);setStatus('Configuración guardada. La próxima toma usará estos ajustes.');})}>Guardar configuración de grabación</button>
  {mode==='download'&&<p>Cuando el video esté listo, abrí Tomas y pulsá Descargar. El navegador decide la carpeta o te pregunta dónde guardarlo según tus preferencias.</p>}
  {!recording.destinationReady&&preferences.destination_id&&<p>Antes de grabar, volvé a autorizar tu carpeta o conectá la misma cuenta de Drive. También podés cambiar a Descargar.</p>}
  {dirty&&<p>Hay cambios sin guardar.</p>}{active&&<p>Terminá la toma y la preparación del video antes de cambiar estos ajustes.</p>}
  {(error||recording.error)&&<p role="alert">{error||recording.error}</p>}{status&&<p role="status">{status}</p>}
 </section>;
}
