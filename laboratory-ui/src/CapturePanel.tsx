import {useEffect,useState} from 'react';
type Data=Record<string,any>;
export function CapturePanel({api,run}:Data){
 const [settings,setSettings]=useState<Data>({max_seconds:120,queue_blocks:128,timeline_hz:20});
 const [state,setState]=useState<Data>({current:{status:'idle'},jobs:[]});
 useEffect(()=>{let live=true;const poll=()=>api('captures').then((s:Data)=>{if(live)setState(s)}).catch(()=>{});
 void poll();const id=setInterval(poll,500);return()=>{live=false;clearInterval(id)};},[api]);
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
  {state.jobs.map((j:Data)=><div key={j.id}><p>{j.status} · {j.events || 0} eventos · {j.timeline_rows || 0} observaciones · {j.error}</p>
    <small>Bitácora local: {j.directory}</small><br/><small>Audio local: {j.shaper?.directory || 'Pendiente de confirmación'}</small></div>)}
  <p>La grabación es opcional. El audio corresponde a la salida digital de Shaper; la sincronía audiovisual y la exportación de video siguen pendientes.</p>
 </>;
}
