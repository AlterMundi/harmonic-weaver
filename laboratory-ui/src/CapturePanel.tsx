import {useEffect,useState} from 'react';
type Data=Record<string,any>;
export function CapturePanel({api,run}:Data){
 const [settings,setSettings]=useState<Data>({max_seconds:120,queue_blocks:128,timeline_hz:20});
 const [state,setState]=useState<Data>({current:{status:'idle'},jobs:[]});
 useEffect(()=>{let live=true;const poll=()=>api('captures').then((s:Data)=>{if(live)setState(s)}).catch(()=>{});
 void poll();const id=setInterval(poll,500);return()=>{live=false;clearInterval(id)};},[api]);
 const [exportSettings,setExportSettings]=useState<Data>({fps:30,width:1280,height:720,offset_s:0,max_gap_s:.25});
 const [exportJobs,setExportJobs]=useState<Data[]>([]);
 const [exportState,setExportState]=useState<Data>({status:'idle'});
 useEffect(()=>{let live=true;const poll=()=>Promise.all([api('capture-exports'),api('capture-exports/jobs')]).then(([s,jobs]:Data[])=>{if(live){setExportState(s);setExportJobs(jobs as Data[])}}).catch(()=>{});
 void poll();const id=setInterval(poll,500);return()=>{live=false;clearInterval(id)};},[api]);
 const exporting=exportState.status==='rendering';
 const active=['starting','recording','stopping'].includes(state.current.status);
 return <>
  <h2>Captura de audio y bitácora</h2>
  <p>Guarda audio de Shaper, configuración, calibración, cambios y timeline local. Esta entrega no guarda imágenes de video o cámara.</p>
  <div className="fields">{[
   ['max_seconds','Duración máxima (s)',.1,3600,.1],
   ['queue_blocks','Capacidad de cola de audio (bloques)',4,1024,1],
   ['timeline_hz','Frecuencia del timeline (Hz)',1,60,1],
  ].map(([key,label,min,max,step])=><label key={key}>{label}<input type="number" value={settings[key]} min={min} max={max} step={step} disabled={active}
    onChange={e=>setSettings({...settings,[key]:+e.target.value})}/></label>)}</div>
  <button disabled={active} onClick={()=>run(async()=>{await api('captures/start',settings);setState(await api('captures'));})}>Iniciar captura</button>
  <button disabled={!active} onClick={()=>run(async()=>{await api('captures/stop',{});setState(await api('captures'));})}>Detener captura</button>
  <p role="status">{state.current.status} · {state.current.error || ''}</p>
  <h3>Exportar video de archivo + audio</h3>
  <p>Alineación estimada desde observaciones del servidor. Huecos o cámara aparecen en negro. Conserva el PCM grabado; no mide latencia física.</p>
  <div className="fields">{[
   ['fps','Fotogramas por segundo',1,120,1],['width','Ancho de exportación',64,1920,2],
   ['height','Alto de exportación',64,1080,2],['offset_s','Offset de alineación (s)',-5,5,.01],
   ['max_gap_s','Edad máxima de observación (s)',.001,5,.01],
  ].map(([key,label,min,max,step])=><label key={key}>{label}<input type="number" value={exportSettings[key]} min={min} max={max} step={step} disabled={exporting}
    onChange={e=>setExportSettings({...exportSettings,[key]:+e.target.value})}/></label>)}</div>
  <p>Exportación: {exportState.status} · {exportState.frames || 0} frames · {exportState.error || ''}</p>
  {exportState.directory && <small>Salida local: {exportState.directory}</small>}
  <button disabled={!exporting} onClick={()=>run(async()=>{setExportState(await api('capture-exports/cancel',{}));})}>Cancelar exportación</button>
  {exportJobs.map((j:Data)=><div key={j.id}><p>Exportación {j.id.slice(0,8)} · {j.status} · {j.error || ''}</p>
    {j.status==='complete' && <><a href={`/api/capture-exports/${j.id}/artifacts/capture.mkv`} download>Descargar video + PCM</a>{' · '}
    <a href={`/api/capture-exports/${j.id}/artifacts/frames.jsonl`} download>Timeline de fotogramas</a>{' · '}</>}
    <a href={`/api/capture-exports/${j.id}/artifacts/manifest.json`} download>Manifest de exportación</a>
  </div>)}
  {state.jobs.map((j:Data)=><div key={j.id}><p>{j.status} · {j.events || 0} eventos · {j.timeline_rows || 0} observaciones · {j.error}</p>
    <button disabled={j.status!=='complete' || exporting} onClick={()=>run(async()=>{
      setExportState(await api(`captures/${j.id}/export`,exportSettings));
    })}>Exportar captura {j.id.slice(0,8)}</button>
    <small>Bitácora local: {j.directory}</small><br/><small>Audio local: {j.shaper?.directory || 'Pendiente de confirmación'}</small></div>)}
  <p>La grabación es opcional. El audio corresponde a la salida digital de Shaper; la sincronía física sigue pendiente de medición.</p>
 </>;
}
