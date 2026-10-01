import {useEffect,useState} from 'react';
type Data=Record<string,any>;
export function CapturePanel({api,run}:Data){
 const [settings,setSettings]=useState<Data>({max_seconds:120,queue_blocks:128,timeline_hz:20,record_camera:false,camera_queue_frames:8,camera_max_frames:10000,camera_max_mb:256});
 const [state,setState]=useState<Data>({current:{status:'idle'},jobs:[]});
 useEffect(()=>{let live=true;const poll=()=>api('captures').then((s:Data)=>{if(live)setState(s)}).catch(()=>{});
 void poll();const id=setInterval(poll,500);return()=>{live=false;clearInterval(id)};},[api]);
 const [exportSettings,setExportSettings]=useState<Data>({fps:30,width:1280,height:720,offset_s:0,max_gap_s:.25,camera_clock:'collector_monotonic_s',browser_preview:false,preview_audio_kbps:192});
 const [preview,setPreview]=useState<string|null>(null);
 const [exportJobs,setExportJobs]=useState<Data[]>([]);
 const [exportState,setExportState]=useState<Data>({status:'idle'});
 useEffect(()=>{let live=true;const poll=()=>Promise.all([api('capture-exports'),api('capture-exports/jobs')]).then(([s,jobs]:Data[])=>{if(live){setExportState(s);setExportJobs(jobs as Data[])}}).catch(()=>{});
 void poll();const id=setInterval(poll,500);return()=>{live=false;clearInterval(id)};},[api]);
 const [recovery,setRecovery]=useState<Data>({status:'idle'});
 useEffect(()=>{let live=true;const poll=()=>api('capture-recovery').then((s:Data)=>{if(live)setRecovery(s)}).catch(()=>{});
 void poll();const id=setInterval(poll,500);return()=>{live=false;clearInterval(id)};},[api]);
 const exporting=exportState.status==='rendering';
 const active=['starting','recording','stopping'].includes(state.current.status);
 return <>
  <h2>Captura de audio y bitácora</h2>
  <p>Guarda audio de Shaper, configuración, calibración, cambios y timeline local. La preview de cámara se guarda sólo si activás la opción siguiente. El video de archivo se referencia en su ruta.</p>
  <label><input type="checkbox" checked={settings.record_camera} disabled={active}
    onChange={e=>setSettings({...settings,record_camera:e.target.checked})}/>Grabar preview de cámara durante esta captura</label>
  <small>Preview procesada por tracking; no es el flujo bruto ni garantiza FPS de cámara. No activa una cámara.</small>
  <div className="fields">{[
   ['max_seconds','Duración máxima (s)',.1,3600,.1],
   ['queue_blocks','Capacidad de cola de audio (bloques)',4,1024,1],
   ['timeline_hz','Frecuencia del timeline (Hz)',1,60,1],
   ['camera_queue_frames','Cola de imágenes de cámara',1,128,1],
   ['camera_max_frames','Máximo de imágenes de cámara',1,216000,1],
   ['camera_max_mb','Presupuesto JPEG de cámara (MiB)',1,8192,1],
  ].map(([key,label,min,max,step])=><label key={key}>{label}<input type="number" value={settings[key]} min={min} max={max} step={step} disabled={active}
    onChange={e=>setSettings({...settings,[key]:+e.target.value})}/></label>)}</div>
  <button disabled={active} onClick={()=>run(async()=>{await api('captures/start',settings);setState(await api('captures'));})}>Iniciar captura</button>
  <button disabled={!active} onClick={()=>run(async()=>{await api('captures/stop',{});setState(await api('captures'));})}>Detener captura</button>
  <p role="status">{state.current.status} · {state.current.error || ''}</p>
  <h3>Exportar video + audio</h3>
  <p>Alineación estimada desde observaciones del servidor. Huecos o cámara sin grabación aparecen en negro. Conserva el PCM grabado; no mide latencia física.</p>
  <div className="fields">{[
   ['fps','Fotogramas por segundo',1,120,1],['width','Ancho de exportación',64,1920,2],
   ['height','Alto de exportación',64,1080,2],['offset_s','Offset de alineación (s)',-5,5,.01],
   ['max_gap_s','Edad máxima de observación (s)',.001,5,.01],
   ['preview_audio_kbps','Bitrate AAC de preview (kbps)',64,320,1],
  ].map(([key,label,min,max,step])=><label key={key}>{label}<input type="number" value={exportSettings[key]} min={min} max={max} step={step} disabled={exporting}
    onChange={e=>setExportSettings({...exportSettings,[key]:+e.target.value})}/></label>)}</div>
  <label>Reloj de cámara para alinear<select value={exportSettings.camera_clock} disabled={exporting}
    onChange={e=>setExportSettings({...exportSettings,camera_clock:e.target.value})}>
    <option value="collector_monotonic_s">Observada por el recolector</option>
    <option value="available_monotonic_s">Disponible después del tracking</option>
    <option value="captured_monotonic_s">Capturada por la cámara</option>
  </select></label>
  <label><input type="checkbox" checked={exportSettings.browser_preview} disabled={exporting} onChange={e=>setExportSettings({...exportSettings,browser_preview:e.target.checked})}/>Generar preview MP4 para navegador</label>
  <p>Preview con audio AAC comprimido; el MKV conserva PCM exacto. No se reproduce automáticamente.</p>
  <p>Exportación: {exportState.status} · {exportState.frames || 0} frames · {exportState.error || ''}</p>
  {exportState.directory && <small>Salida local: {exportState.directory}</small>}
  <button disabled={!exporting} onClick={()=>run(async()=>{setExportState(await api('capture-exports/cancel',{}));})}>Cancelar exportación</button>
  {exportJobs.map((j:Data)=><div key={j.id}><p>Exportación {j.id.slice(0,8)} · {j.status} · {j.error || ''}</p>
    {j.capture_completeness==='recovered_partial' && <p>Exportación de prefijo recuperado: captura parcial; sólo incluye imágenes recuperadas verificadas.</p>}
    {j.status==='complete' && <><a href={`/api/capture-exports/${j.id}/artifacts/capture.mkv`} download>Descargar video + PCM</a>{' · '}
    <a href={`/api/capture-exports/${j.id}/artifacts/frames.jsonl`} download>Timeline de fotogramas</a>{' · '}</>}
    {j.status==='complete' && j.preview?.status==='complete' && <>
      <button onClick={()=>setPreview(preview===j.id?null:j.id)}>{preview===j.id?'Cerrar preview':'Ver preview de captura'}</button>
      <a href={`/api/capture-exports/${j.id}/artifacts/preview.mp4`} download>Descargar preview MP4 (AAC)</a>
      {preview===j.id && <video controls playsInline preload="metadata" src={`/api/capture-exports/${j.id}/artifacts/preview.mp4`}/>}
    </>}
    {j.preview?.status==='failed' && <p>Preview no disponible: {j.preview.error}. El MKV con PCM se conserva.</p>}
    <a href={`/api/capture-exports/${j.id}/artifacts/manifest.json`} download>Manifest de exportación</a>
  </div>)}
  <p>Recuperación: {recovery.status} · {recovery.error || ''}</p>
  {recovery.persistence_error && <p role="alert">No se pudo guardar el estado de recuperación: {recovery.persistence_error}. El resultado mostrado sólo está confirmado en memoria.</p>}
  {recovery.result && <p>Prefijo recuperado: {recovery.result.recovered_samples} muestras. Carpeta local: {recovery.result.directory}. No equivale a una captura completa.</p>}
  {recovery.journal?.files && <p>Bitácora parcial: {recovery.journal.files['events.jsonl'].rows} eventos · {recovery.journal.files['timeline.jsonl'].rows} observaciones · {recovery.journal.directory}. Puede haber un final desconocido.</p>}
  {recovery.journal?.error && <p>Bitácora no recuperada: {recovery.journal.error}. El prefijo PCM confirmado se conserva.</p>}
  {recovery.camera?.status==='recovered' && <p>Imágenes verificadas: {recovery.camera.verified_frames} · {recovery.camera.directory} · corte: {recovery.camera.stop_reason}. Prefijo parcial, sin exportación audiovisual automática.</p>}
  {recovery.camera?.error && <p>Imágenes no recuperadas: {recovery.camera.error}. El audio recuperado se conserva.</p>}
  {state.jobs.map((j:Data)=><div key={j.id}><p>{j.status} · {j.events || 0} eventos · {j.timeline_rows || 0} observaciones · {j.error}</p>
    <button disabled={j.status!=='complete' || exporting} onClick={()=>run(async()=>{
      setExportState(await api(`captures/${j.id}/export`,exportSettings));
    })}>Exportar captura {j.id.slice(0,8)}</button>
    {['failed','interrupted'].includes(j.status) && j.recovery?.result && j.recovery?.journal?.status==='partial' &&
      <button disabled={exporting || j.recovery.status==='recovering'} onClick={()=>run(async()=>{
        setExportState(await api(`captures/${j.id}/export`,{...exportSettings,recovered_prefix:true}));
      })}>Exportar prefijo recuperado {j.id.slice(0,8)}</button>}
    {['failed','interrupted'].includes(j.status) && <button disabled={recovery.status==='recovering' || j.recovery?.status==='recovering' || !j.shaper?.id}
      onClick={()=>run(async()=>setRecovery(await api(`captures/${j.id}/recover`,{})))}>Recuperar audio {j.id.slice(0,8)}</button>}
    {j.camera && <p>Cámara: {j.camera.status} · {j.camera.written_frames}/{j.camera.accepted_frames} previews · {j.camera.observed_sequence_gaps} saltos de secuencia · {j.camera.error || ''}</p>}
    {j.recovery && <p>Recuperación de esta captura: {j.recovery.status} · {j.recovery.phase || ''} · {j.recovery.error || ''}</p>}
    {j.recovery?.persistence_error && <p role="alert">Estado de recuperación sin guardar: {j.recovery.persistence_error}</p>}
    {j.recovery?.result && <p>Audio recuperado: {j.recovery.result.recovered_samples} muestras · {j.recovery.result.directory}</p>}
    <small>Bitácora local: {j.directory}</small><br/><small>Audio local: {j.shaper?.directory || 'Pendiente de confirmación'}</small></div>)}
  <p>La grabación es opcional. El audio corresponde a la salida digital de Shaper; la sincronía física sigue pendiente de medición.</p>
 </>;
}
