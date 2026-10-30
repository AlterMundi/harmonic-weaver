import {useEffect,useRef,useState} from 'react';
import {useConfirmedPolling} from './useConfirmedPolling';
import './QuickRecorder.css';

type Data=Record<string,any>;
const paths=['captures','capture-exports','capture-exports/jobs'];
const activeStates=['starting','recording','stopping'];
const captureSettings={max_seconds:300,queue_blocks:128,timeline_hz:20,
  record_camera:true,camera_queue_frames:8,camera_max_frames:18000,camera_max_mb:512};
const exportSettings={fps:30,width:1280,height:720,browser_preview:true,
  skeleton_overlay:true,skeleton_people:'selected',harmonic_figure:false};
const media=(id:string,name:string)=>`/api/capture-exports/${encodeURIComponent(id)}/artifacts/${name}`;
const hasVideo=(take:Data)=>take.settings?.record_camera
  ? Number(take.camera?.written_frames)>0
  : (take.initial_source_identity?.kind||take.initial?.state?.source?.kind)==='video';

/** A simple front door to the existing durable capture and export services. */
export function QuickRecorder({api,state,onAdvanced}: {api:any;state:Data;onAdvanced:()=>void}) {
  const poll=useConfirmedPolling(api,paths,[{current:{status:'idle'},jobs:[]},{status:'idle'},[]],750);
  const [inventory,exportState,exports]=poll.data;
  const current=inventory.current||{},takes:Data[]=inventory.jobs||[];
  const active=activeStates.includes(current.status),encoding=exportState.status==='rendering';
  const [busy,setBusy]=useState(false),[error,setError]=useState('');
  const [pending,setPending]=useState<string|null>(null),[blocked,setBlocked]=useState<string|null>(null);
  const sent=useRef(new Set<string>()),locked=useRef(false);
  const [started,setStarted]=useState<number|null>(null),[now,setNow]=useState(Date.now());
  const [preview,setPreview]=useState<string|null>(null);
  const dialog=useRef<HTMLDialogElement>(null),libraryButton=useRef<HTMLButtonElement>(null);
  const source=state.source||{};
  const sourceReady=Boolean(state.session?.playing &&
    (source.kind==='video'||source.kind==='camera'&&source.camera?.status==='ready'&&!(source.camera?.sample_age_ms>2000)));
  const confirmed=poll.ready&&!poll.error;
  const matching=(id:string,rows:Data[]=exports)=>rows.filter(j=>j.capture_id===id).find(j=>j.status==='rendering'||j.status==='complete'&&j.skeleton_overlay?.enabled&&j.preview?.status==='complete');

  useEffect(()=>{if(!active||started===null)return;
    const timer=setInterval(()=>setNow(Date.now()),500);return()=>clearInterval(timer);
  },[active,started]);
  useEffect(()=>{
    if(!pending||!confirmed||active||encoding||sent.current.has(pending)||blocked===pending)return;
    const take=takes.find(j=>j.id===pending);
    if(!take||activeStates.includes(take.status))return;
    if(take.status!=='complete'){
      setError('La toma quedó incompleta. Conservamos lo registrado; revisala en Tomas.');setBlocked(pending);setPending(null);return;
    }
    if(!hasVideo(take)){
      setError('Se conservó el audio, pero no llegaron imágenes de video. Revisá la cámara antes de otra toma.');setBlocked(pending);setPending(null);return;
    }
    if(matching(pending)){setPending(null);return;}
    const id=pending;sent.current.add(id);
    // Never replay a lost export acknowledgement. Inventory readback resolves it.
    void api(`captures/${encodeURIComponent(id)}/export`,exportSettings).then(()=>setPending(null)).catch((e:any)=>{
      setError(`No pudimos confirmar el guardado del video. Revisá Tomas antes de reintentarlo. ${String(e)}`);
    });
  },[pending,confirmed,active,encoding,inventory,exports,blocked,api]);
  useEffect(()=>{if(pending&&sent.current.has(pending)&&matching(pending)){
    setPending(null);setError('');
  }},[pending,exports]);

  const start=async()=>{
    if(locked.current||!confirmed||active||encoding||pending||!sourceReady)return;
    locked.current=true;setBusy(true);setError('');
    try{
      const result=await api('captures/start',{...captureSettings,record_camera:source.kind==='camera'});
      if(!result?.id)throw Error('El servidor no confirmó una toma identificada.');
      setPending(result.id);setBlocked(null);setStarted(Date.now());setNow(Date.now());
      poll.setData((old:any[])=>[{...old[0],current:result},old[1],old[2]]);
    }catch(e){setError(`No pudimos confirmar el inicio. El inventario mostrará si comenzó; no lo repetimos automáticamente. ${String(e)}`);}
    finally{locked.current=false;setBusy(false);}
  };
  const stop=async()=>{
    if(locked.current||!active||!current.id)return;
    locked.current=true;setBusy(true);setError('');setPending(current.id);setBlocked(null);
    try{const result=await api('captures/stop',{});
      poll.setData((old:any[])=>[{...old[0],current:result},old[1],old[2]]);
    }catch(e){setError(`No pudimos confirmar el cierre. Revisá el estado de esta toma; no reiniciamos la grabación. ${String(e)}`);}
    finally{locked.current=false;setBusy(false);}
  };
  const prepare=async(id:string)=>{
    if(locked.current||active||encoding||!confirmed)return;
    locked.current=true;setBusy(true);setError('');
    try{
      // Re-read before any human-requested retry, including an uncertain receipt.
      const rows:Data[]=await api('capture-exports/jobs');
      if(matching(id,rows)){setPending(null);return;}
      sent.current.delete(id);setBlocked(null);setPending(id);
    }catch(e){setError(`No se pudo revisar el guardado. La toma original sigue conservada. ${String(e)}`);}
    finally{locked.current=false;setBusy(false);}
  };
  const openLibrary=()=>{setPreview(null);dialog.current?.showModal();};
  const closeLibrary=()=>{dialog.current?.close();setPreview(null);libraryButton.current?.focus();};
  const elapsed=started===null?'':`${Math.floor((now-started)/60000)}:${String(Math.floor((now-started)/1000)%60).padStart(2,'0')}`;
  const pendingTake=takes.find(j=>j.id===pending);
  const waiting=Boolean(pending&&!active&&!blocked&&!encoding);
  const shortStatus=active ? `● Grabando ${elapsed}` : encoding ? 'Preparando video…' : waiting ? 'Guardando toma…' : '';
  return <div className="quick-recorder">
    <button className={active?'recording-button':'record-button'} title={!sourceReady&&!active?'Encendé la cámara o reproducí un video para grabar.':undefined} disabled={busy||(!active&&(!confirmed||encoding||!!pending||!sourceReady))}
      onClick={()=>void(active?stop():start())}>{busy?'Confirmando…':active?'Detener y guardar':'Grabar'}</button>
    <button ref={libraryButton} onClick={openLibrary}>Tomas ({takes.length})</button>
    {shortStatus&&<span className="recording-status" role="status">{shortStatus}</span>}
    {(error||poll.error)&&<span className="recording-notice" role="alert">{error||'No se pudo actualizar el estado. Revisá Tomas.'}</span>}
    <dialog className="takes-dialog" ref={dialog} aria-labelledby="takes-title" onCancel={()=>setPreview(null)}
      onClose={()=>{setPreview(null);libraryButton.current?.focus();}}>
      <div className="takes-heading"><h2 id="takes-title">Tomas guardadas</h2><button onClick={closeLibrary}>Cerrar tomas</button></div>
      <p>Grabar conserva video, puntos del cuerpo y el sonido de HarmoCap en esta compu. Al terminar se prepara un MP4 con las líneas sobre el cuerpo. Tomas de hasta 5 minutos.</p>
      {!sourceReady&&!active&&<p>Para una toma nueva, encendé la cámara o reproducí un video antes de pulsar Grabar.</p>}
      {error&&<p role="alert">{error}</p>}
      {poll.error&&<p role="alert">No se pudo actualizar el inventario. Se muestra el último estado confirmado.</p>}
      {active&&<p role="status">Hay una toma en curso. Detener y guardar cierra la grabación y prepara el video.</p>}
      {pendingTake?.status==='complete'&&encoding&&<p role="status">Los originales ya están guardados. Se está preparando el video para ver y descargar.</p>}
      {!takes.length&&<p>{poll.ready?'Todavía no hay tomas guardadas.':'Consultando tomas…'}</p>}
      <div className="takes-list">{[...takes].reverse().map(take=>{
        const jobs:Data[]=exports.filter((j:Data)=>j.capture_id===take.id);
        const complete=jobs.find(j=>j.status==='complete'&&j.skeleton_overlay?.enabled&&j.preview?.status==='complete');
        const original=complete||jobs.find(j=>j.status==='complete'&&j.skeleton_overlay?.enabled);
        const rendering=jobs.find(j=>j.status==='rendering');
        const failed=jobs.find(j=>['failed','interrupted'].includes(j.status));
        const status=complete?'Video listo':rendering?'Preparando video…':take.status==='complete'?'Originales guardados':activeStates.includes(take.status)?'Grabación en curso':'Toma incompleta';
        return <article className="saved-take" key={take.id}>
          <h3>Toma {take.id.slice(0,8)}</h3><p>{status}</p>
          {rendering&&<p role="status">{rendering.frames||0} fotogramas preparados</p>}
          {complete&&<div className="take-actions">
            <button onClick={()=>setPreview(preview===complete.id?null:complete.id)}>{preview===complete.id?'Cerrar video':'Ver video'}</button>
            <a href={media(complete.id,'preview.mp4')} download={`HarmoCap-${take.id.slice(0,8)}.mp4`}>Descargar MP4</a>
          </div>}
          {original&&<p><a href={media(original.id,'capture.mkv')} download={`HarmoCap-${take.id.slice(0,8)}.mkv`}>Descargar original MKV · audio sin comprimir</a></p>}
          {preview&&complete?.id===preview&&<video controls playsInline preload="metadata" src={media(complete.id,'preview.mp4')}/>}
          {original?.preview?.status==='failed'&&<p>No se pudo crear el MP4. El original MKV y la toma se conservan.</p>}
          {take.status==='complete'&&hasVideo(take)&&!complete&&!rendering&&<button disabled={busy||active||encoding||!confirmed||pending===take.id&&blocked!==take.id&&!sent.current.has(take.id)}
            onClick={()=>void prepare(take.id)}>Preparar video de esta toma</button>}
          {take.status==='complete'&&!hasVideo(take)&&<p>Esta toma no tiene imágenes guardadas. El audio y los datos originales se conservan.</p>}
          {failed&&<p role="alert">No se terminó el video: {failed.error||failed.status}. Los originales se conservan.</p>}
          {take.error&&<p role="alert">{take.error}</p>}
          {original?.gaps&&Object.values(original.gaps).some(n=>Number(n)>0)&&<p>Hay tramos sin imagen en esta toma. Se conservaron como huecos, junto con el audio y los datos disponibles.</p>}
          {original?.skeleton_overlay?.enabled&&original.skeleton_overlay.frames===0&&<p>El video no tuvo puntos corporales que pudieran alinearse. Revisá el seguimiento antes de otra toma.</p>}
        </article>;
      })}</div>
      <p className="takes-help">Esperá a “Video listo” antes de cerrar la página. Si la cerrás antes, retomá desde “Preparar video de esta toma”.</p>
      <p className="takes-help">El MP4 incluye audio comprimido para reproducirlo fácilmente. El MKV conserva el audio digital original. Guardamos también imágenes, movimientos y configuración para trabajar después; las líneas corresponden a puntos observados. La sincronía audiovisual es estimada.</p>
      <button onClick={()=>{closeLibrary();onAdvanced();}}>Abrir herramientas de captura</button>
    </dialog>
  </div>;
}
