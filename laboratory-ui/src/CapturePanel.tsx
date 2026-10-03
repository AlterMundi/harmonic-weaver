import {useEffect,useState} from 'react';
import {CaptureProfiles} from './CaptureProfiles';
type Data=Record<string,any>;
const pollPaths={capture:['captures'],exports:['capture-exports','capture-exports/jobs'],recovery:['capture-recovery']};
function useCapturePolling(api:any,kind:keyof typeof pollPaths,initial:Data[]){
 const [data,setData]=useState(initial),[error,setError]=useState(''),[ready,setReady]=useState(false);
 useEffect(()=>{let live=true,inFlight=false;
  const poll=async()=>{
   if(inFlight)return;inFlight=true;
   try{
    const results=await Promise.allSettled(pollPaths[kind].map(async path=>{
     try{return await api(path)}catch(e){if(live)setError(String(e));throw e}
    }));
    const values=results.map(result=>{if(result.status==='rejected')throw result.reason;return result.value});
    if(live){setData(values);setError('');setReady(true)}
   }
   catch(e){if(live)setError(String(e))}
   finally{inFlight=false}
  };
  void poll();const timer=setInterval(()=>void poll(),500);return()=>{live=false;clearInterval(timer)};
 },[api,kind]);
 return {data,error,ready,setData};
}
export function CapturePanel({api,run}:Data){
 const [settings,setSettings]=useState<Data>({max_seconds:120,queue_blocks:128,timeline_hz:20,record_camera:false,camera_queue_frames:8,camera_max_frames:10000,camera_max_mb:256});
 const capturePoll=useCapturePolling(api,'capture',[{current:{status:'idle'},jobs:[]}]);
 const state=capturePoll.data[0];const setState=(value:Data)=>capturePoll.setData([value]);
 const [exportSettings,setExportSettings]=useState<Data>({fps:30,width:1280,height:720,offset_s:0,max_gap_s:.25,camera_clock:'collector_monotonic_s',browser_preview:false,preview_audio_kbps:192,harmonic_figure:false,figure_window_hz:40.4,skeleton_overlay:false,skeleton_people:'selected',skeleton_confidence:0,skeleton_max_offset_s:.1,skeleton_line_px:2});
 const [figureVisual,setFigureVisual]=useState('{}');
 const exportPayload=()=>({...exportSettings,figure_visual:JSON.parse(figureVisual)});
 const [preview,setPreview]=useState<string|null>(null);
 const exportPoll=useCapturePolling(api,'exports',[{status:'idle'},[]]);
 const [exportState,exportJobs]=exportPoll.data;const setExportState=(value:Data)=>exportPoll.setData(previous=>[value,previous[1]]);
 const recoveryPoll=useCapturePolling(api,'recovery',[{status:'idle'}]);
 const recovery=recoveryPoll.data[0];const setRecovery=(value:Data)=>recoveryPoll.setData([value]);
 const exporting=exportState.status==='rendering';
 const active=['starting','recording','stopping'].includes(state.current.status);
 return <>
  <h2>Captura de audio y bitácora</h2>
  {capturePoll.error&&<p role="alert">No se pudo actualizar el inventario de capturas: {capturePoll.error}. Se conserva el último estado confirmado; reintentando.</p>}
  {exportPoll.error&&<p role="alert">No se pudo actualizar las exportaciones: {exportPoll.error}. Se conserva el último estado confirmado; reintentando.</p>}
  {recoveryPoll.error&&<p role="alert">No se pudo actualizar la recuperación: {recoveryPoll.error}. Se conserva el último estado confirmado; reintentando.</p>}
  <CaptureProfiles api={api} disabled={active||exporting} getDraft={()=>({capture:settings,export:exportPayload()})} onApply={(p:Data)=>{setSettings(p.capture);const {figure_visual,...rest}=p.export;setExportSettings(rest);setFigureVisual(JSON.stringify(figure_visual));}}/>
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
  <button disabled={active||!capturePoll.ready||!!capturePoll.error} onClick={()=>run(async()=>{await api('captures/start',settings);setState(await api('captures'));})}>Iniciar captura</button>
  <button disabled={!active} onClick={()=>run(async()=>{await api('captures/stop',{});setState(await api('captures'));})}>Detener captura</button>
  <p role="status">{capturePoll.ready?state.current.status:'Esperando inventario de capturas'} · {state.current.error || ''}</p>
  <h3>Exportar video + audio</h3>
  <p>Alineación estimada desde observaciones del servidor. Huecos o cámara sin grabación aparecen en negro. Conserva el PCM grabado; no mide latencia física.</p>
  <div className="fields">{[
   ['fps','Fotogramas por segundo',1,120,1],['width','Ancho de exportación',64,1920,2],
   ['height','Alto de exportación',64,1080,2],['offset_s','Offset de alineación (s)',-5,5,.01],
   ['max_gap_s','Edad máxima de observación (s)',.001,5,.01],
   ['figure_window_hz','Frecuencia de referencia de la ventana de figura (Hz)',.001,20000,.1],
   ['skeleton_confidence','Confianza mínima del esqueleto',0,1,.05],
   ['skeleton_max_offset_s','Desfase máximo pose/video (s)',0,1,.01],
   ['skeleton_line_px','Grosor del esqueleto (px)',1,12,1],
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
  <label><input type="checkbox" checked={exportSettings.skeleton_overlay} disabled={exporting} onChange={e=>setExportSettings({...exportSettings,skeleton_overlay:e.target.checked})}/>Incluir esqueleto observado en la exportación</label>
  <label>Personas en el esqueleto<select value={exportSettings.skeleton_people} disabled={exporting} onChange={e=>setExportSettings({...exportSettings,skeleton_people:e.target.value})}><option value="selected">Persona seleccionada en cada observación</option><option value="all">Todas las personas observadas</option></select></label>
  <small>Sin interpolar poses. Omite huecos, cambios de época, coordenadas sin proyección y poses que no coincidan con el video.</small>
  <label><input type="checkbox" checked={exportSettings.harmonic_figure} disabled={exporting} onChange={e=>setExportSettings({...exportSettings,harmonic_figure:e.target.checked})}/>Incluir figura de todos los osciladores grabados</label>
  <label>Estilo de figura exportada (JSON)<textarea value={figureVisual} disabled={exporting} onChange={e=>setFigureVisual(e.target.value)}/></label>
  <small>Panel junto al video. JSON acepta window_periods, samples, persistence, line_width, brightness, scale, auto_scale, components y color (ice/gold/violet). La frecuencia de referencia determina la ventana visual; no cambia la afinación. Usa fase y ganancia del bloque PCM, antes de waveshaping/limiter; no es una medición de cymatics físico.</small>
  <p>Preview con audio AAC comprimido; el MKV conserva PCM exacto. No se reproduce automáticamente.</p>
  <p>Exportación: {exportPoll.ready?exportState.status:'sin estado confirmado'} · {exportState.frames || 0} frames · {exportState.error || ''}</p>
  {exportState.directory && <small>Salida local: {exportState.directory}</small>}
  <button disabled={!exporting} onClick={()=>run(async()=>{setExportState(await api('capture-exports/cancel',{}));})}>Cancelar exportación</button>
  {exportJobs.map((j:Data)=><div key={j.id}><p>Exportación {j.id.slice(0,8)} · {j.status} · {j.error || ''}</p>
    {j.harmonic_figure?.enabled && <p>Figura: {j.harmonic_figure.frames} frames · omisiones: {JSON.stringify(j.harmonic_figure.omissions)}</p>}
    {j.skeleton_overlay?.enabled && <p>Esqueleto: {j.skeleton_overlay.frames} frames · omisiones: {JSON.stringify(j.skeleton_overlay.omissions)}</p>}
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
  <p>Recuperación: {recoveryPoll.ready?recovery.status:'sin estado confirmado'} · {recovery.error || ''}</p>
  {recovery.persistence_error && <p role="alert">No se pudo guardar el estado de recuperación: {recovery.persistence_error}. El resultado mostrado sólo está confirmado en memoria.</p>}
  {recovery.result && <p>Prefijo recuperado: {recovery.result.recovered_samples} muestras. Carpeta local: {recovery.result.directory}. No equivale a una captura completa.</p>}
  {recovery.journal?.files && <p>Bitácora parcial: {recovery.journal.files['events.jsonl'].rows} eventos · {recovery.journal.files['timeline.jsonl'].rows} observaciones · {recovery.journal.directory}. Puede haber un final desconocido.</p>}
  {recovery.journal?.error && <p>Bitácora no recuperada: {recovery.journal.error}. El prefijo PCM confirmado se conserva.</p>}
  {recovery.camera?.status==='recovered' && <p>Imágenes verificadas: {recovery.camera.verified_frames} · {recovery.camera.directory} · corte: {recovery.camera.stop_reason}. Prefijo parcial, sin exportación audiovisual automática.</p>}
  {recovery.camera?.error && <p>Imágenes no recuperadas: {recovery.camera.error}. El audio recuperado se conserva.</p>}
  {state.jobs.map((j:Data)=><div key={j.id}><p>{j.status} · {j.events || 0} eventos · {j.timeline_rows || 0} observaciones · {j.error}</p>
    <button disabled={j.status!=='complete' || exporting || !exportPoll.ready || !!exportPoll.error} onClick={()=>run(async()=>{
      setExportState(await api(`captures/${j.id}/export`,exportPayload()));
    })}>Exportar captura {j.id.slice(0,8)}</button>
    {['failed','interrupted'].includes(j.status) && j.recovery?.result && j.recovery?.journal?.status==='partial' &&
      <button disabled={exporting || !exportPoll.ready || !!exportPoll.error || j.recovery.status==='recovering'} onClick={()=>run(async()=>{
        setExportState(await api(`captures/${j.id}/export`,{...exportPayload(),recovered_prefix:true}));
      })}>Exportar prefijo recuperado {j.id.slice(0,8)}</button>}
    {['failed','interrupted'].includes(j.status) && <button disabled={!recoveryPoll.ready || !!recoveryPoll.error || recovery.status==='recovering' || j.recovery?.status==='recovering' || !j.shaper?.id}
      onClick={()=>run(async()=>setRecovery(await api(`captures/${j.id}/recover`,{})))}>Recuperar audio {j.id.slice(0,8)}</button>}
    {j.camera && <p>Cámara: {j.camera.status} · {j.camera.written_frames}/{j.camera.accepted_frames} previews · {j.camera.observed_sequence_gaps} saltos de secuencia · {j.camera.error || ''}</p>}
    {j.recovery && <p>Recuperación de esta captura: {j.recovery.status} · {j.recovery.phase || ''} · {j.recovery.error || ''}</p>}
    {j.recovery?.persistence_error && <p role="alert">Estado de recuperación sin guardar: {j.recovery.persistence_error}</p>}
    {j.recovery?.result && <p>Audio recuperado: {j.recovery.result.recovered_samples} muestras · {j.recovery.result.directory}</p>}
    <small>Bitácora local: {j.directory}</small><br/><small>Audio local: {j.shaper?.directory || 'Pendiente de confirmación'}</small></div>)}
  <p>La grabación es opcional. El audio corresponde a la salida digital de Shaper; la sincronía física sigue pendiente de medición.</p>
 </>;
}
