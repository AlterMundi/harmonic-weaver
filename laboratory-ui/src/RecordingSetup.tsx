import {useEffect,useState} from 'react';
import {useConfirmedPolling} from './useConfirmedPolling';
type Data=Record<string,any>;
export const defaultRecording={schema_version:1,max_seconds:300,include_audio:true,skeleton_overlay:true,harmonic_figure:false,format:'mp4',destination_id:null};
const paths=['captures','capture-exports','capture-exports/jobs','recording-deliveries'];

export function useRecordingSetup(api:any){
 const poll=useConfirmedPolling(api,paths,[{current:{status:'idle'},jobs:[]},{status:'idle'},[],[]],750);
 const [preferences,setPreferences]=useState<Data>(defaultRecording),[ready,setReady]=useState(false),[error,setError]=useState('');
 const [destinations,setDestinations]=useState<Data[]>([]),[provider,setProvider]=useState<Data>({});
 const reloadDestinations=async()=>{
  const value=await api('recording-destinations');
  if(!Array.isArray(value?.destinations))throw Error('No se pudieron consultar los destinos.');
  setDestinations(value.destinations);setProvider(value.provider||{});
 };
 useEffect(()=>{let live=true;
  void api('recording-preferences').then((value:Data)=>{
   if(value?.schema_version!==1||typeof value.include_audio!=='boolean')throw Error('Configuración de grabación no disponible.');
   if(live){setPreferences({...defaultRecording,...value});setReady(true);setError('');}
  }).catch((e:any)=>{if(live)setError(String(e));});
  void reloadDestinations().catch((e:any)=>{if(live)setError(String(e));});
  return()=>{live=false};
 },[api]);
 const save=async(value:Data)=>{const result=await api('recording-preferences',value);setPreferences(result);setReady(true);setError('');return result;};
 return {poll,preferences,ready,error,destinations,provider,reloadDestinations,save};
}

export function RecordingSetup({api,recording}:{api:any;recording:ReturnType<typeof useRecordingSetup>}){
 const {preferences,destinations,provider,poll}=recording;
 const [draft,setDraft]=useState<Data>(preferences),[dirty,setDirty]=useState(false),[mode,setMode]=useState('library');
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[status,setStatus]=useState('');
 const active=['starting','recording','stopping'].includes(poll.data[0].current?.status)||poll.data[1].status==='rendering';
 const blocked=active||busy||!recording.ready;
 useEffect(()=>{if(dirty)return;setDraft(preferences);setMode(preferences.destination_id?destinations.find(d=>d.id===preferences.destination_id)?.kind||'unknown':'library');},[preferences,destinations,dirty]);
 const change=(values:Data)=>{setDraft(previous=>({...previous,...values}));setDirty(true);setStatus('');};
 const act=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');try{await fn()}catch(e){setError(String(e))}finally{setBusy(false);}};
 const choose=()=>act(async()=>{
  const result=await api('recording-destinations/pick',{kind:mode});
  if(result.status==='cancelled')return;
  await recording.reloadDestinations();change({destination_id:result.destination.id});
 });
 const selected=destinations.find(d=>d.id===draft.destination_id);
 const savedDestination=destinations.find(d=>d.id===preferences.destination_id);
 return <section aria-label="Configuración de grabación">
  <h2>Grabar y guardar</h2>
  <p>Elegí qué incluir y dónde guardar una copia. El botón Grabar junto a la cámara usa esta configuración.</p>
  <p>Configuración actual: {savedDestination?`${savedDestination.kind==='drive'?'Drive':'Carpeta'} · ${savedDestination.label}`:preferences.destination_id?'Destino guardado sin conexión confirmada':'Biblioteca de HarmoCap'} · {preferences.format?.toUpperCase()}</p>
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
    <option value="library">Biblioteca de HarmoCap</option><option value="folder">Carpeta del laboratorio</option><option value="drive">Google Drive</option>{mode==='unknown'&&<option value="unknown">Destino guardado sin consultar</option>}
   </select></label>
   {mode==='drive'&&<>
    <p>Cuenta: <strong>{provider.account||'Todavía no configurada'}</strong></p>
    <p>{provider.account_available?'Cuenta detectada. Elegí la carpeta de Drive.':'Conectá esta cuenta en Cuentas en línea de la computadora del laboratorio.'}</p>
    <div className="actions"><button disabled={!provider.connect_available} onClick={()=>void act(async()=>{await api('recording-drive/connect',{});setStatus('Se abrió Cuentas en línea. Conectá Google y después pulsá Actualizar conexión.');})}>Conectar Drive</button>
     <button onClick={()=>void act(async()=>{await recording.reloadDestinations();setStatus('Conexión consultada.');})}>Actualizar conexión</button></div>
   </>}
   {['folder','drive'].includes(mode)&&<>
    <label>Carpeta elegida<select aria-label="Carpeta elegida" value={draft.destination_id||''} onChange={e=>change({destination_id:e.target.value||null})}>
     <option value="">Elegí una carpeta</option>{destinations.filter(d=>d.kind===mode).map(d=><option key={d.id} value={d.id}>{d.label}</option>)}
    </select></label>
    <button disabled={mode==='drive'&&!provider.account_available} onClick={()=>void choose()}>Elegir carpeta{mode==='drive'?' de Drive':''}</button>
    <p>El selector se abre en la computadora que ejecuta el laboratorio.</p>
    {selected&&<p>Destino: {selected.label}{selected.account?` · ${selected.account}`:''}</p>}
   </>}
   <p>Los originales quedan siempre en la biblioteca. La carpeta elegida recibe una copia verificada del video; elegir Drive autoriza esa subida al detener y guardar.</p>
  </fieldset>
  <button disabled={blocked||mode==='unknown'||mode==='drive'&&!provider.account_available||mode!=='library'&&!draft.destination_id||!Number.isFinite(draft.max_seconds)||draft.max_seconds<1||draft.max_seconds>300}
   onClick={()=>void act(async()=>{await recording.save(draft);setDirty(false);setStatus('Configuración guardada. La próxima toma usará estos ajustes.');})}>Guardar configuración de grabación</button>
  {dirty&&<p>Hay cambios sin guardar.</p>}{active&&<p>Terminá la toma y la preparación del video antes de cambiar estos ajustes.</p>}
  {(error||recording.error)&&<p role="alert">{error||recording.error}</p>}{status&&<p role="status">{status}</p>}
 </section>;
}
