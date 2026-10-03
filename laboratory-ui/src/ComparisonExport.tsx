import { useEffect, useState } from "react";
type Data = Record<string, any>;
const defaults = {schema_version:1, fps:30, width:1280, height:720, format:"mkv", video_crf:18, audio_kbps:192, visual:null};
async function api(path:string, body?:Data) {
  const response=await fetch(`/api/${path}`, body === undefined ? {} : {method:"POST", headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
  const value=await response.json();
  if(!response.ok) throw Error(value.detail || JSON.stringify(value));
  return value;
}
export function ComparisonExport({report,run}: {report:Data;run:Data}) {
  const [settings,setSettings]=useState<Data>(defaults),[jobs,setJobs]=useState<Data[]>([]),[error,setError]=useState(""),[busy,setBusy]=useState(false);
  useEffect(()=>{
    let live=true;
    const poll=()=>api("comparison-exports").then(rows=>{if(live)setJobs(rows)}).catch(e=>{if(live)setError(String(e))});
    void poll();const timer=setInterval(poll,1000);
    return()=>{live=false;clearInterval(timer)};
  },[]);
  const action=async(path:string,body:Data)=>{
    setBusy(true);setError("");
    try {await api(path,body);setJobs(await api("comparison-exports"));} catch(e){setError(String(e))} finally{setBusy(false)}
  };
  const visual= settings.visual || report.manifest.request.presets[run.preset_index].visual;
  return <details><summary>Exportar video, audio y figura</summary>
    <p>Exporta el segmento y preset elegidos a velocidad 1×, sin el ajuste visual de reproducción. No recalcula tracking. Video a la izquierda; suma de todos los armónicos a la derecha. Los archivos quedan locales.</p>
    {([['fps','Fotogramas/s',1,60,1],['width','Ancho total',128,1920,4],['height','Alto',64,1080,2],['video_crf','CRF de video (menor = más calidad)',0,40,1],['audio_kbps','AAC kbps (sólo MP4)',64,320,1]] as const).map(([key,label,min,max,step])=><label key={key}>{label}<input type="number" value={settings[key]} min={min} max={max} step={step} onChange={e=>setSettings({...settings,[key]:+e.target.value})}/></label>)}
    <label>Formato<select aria-label="Formato" value={settings.format} onChange={e=>setSettings({...settings,format:e.target.value})}><option value="mkv">MKV — PCM conservado</option><option value="mp4">MP4 — AAC con pérdida</option></select></label>
    <label><input type="checkbox" checked={settings.visual!==null} onChange={e=>setSettings({...settings,visual:e.target.checked?{...visual}:null})}/>Personalizar figura; desmarcado usa el preset congelado</label>
    {settings.visual && <div>
      {([['window_periods','Períodos',.1,30,.1],['samples','Puntos',256,12000,1],['persistence','Persistencia por fotograma',0,.98,.01],['line_width','Grosor',.5,6,.5],['brightness','Brillo',.1,2,.1],['scale','Escala',.1,5,.1]] as const).map(([key,label,min,max,step])=><label key={key}>{label}<input type="number" value={visual[key]} min={min} max={max} step={step} onChange={e=>setSettings({...settings,visual:{...visual,[key]:+e.target.value}})}/></label>)}
      {([['auto_scale','Escala automática'],['components','Mostrar componentes'],['mirror_video','Espejar video']] as const).map(([key,label])=><label key={key}><input type="checkbox" checked={visual[key]} onChange={e=>setSettings({...settings,visual:{...visual,[key]:e.target.checked}})}/>{label}</label>)}
      <label>Color<select aria-label="Color" value={visual.color} onChange={e=>setSettings({...settings,visual:{...visual,color:e.target.value}})}>{['ice','gold','violet'].map(c=><option key={c}>{c}</option>)}</select></label>
    </div>}
    <button onClick={()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(settings,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='comparison-export-settings.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}}>Guardar configuración de exportación</button>
    <label>Importar configuración<input type="file" accept="application/json" onChange={async e=>{try{const file=e.target.files?.[0];if(!file)return;if(file.size>65536)throw Error('Máximo 64 KiB');const value=JSON.parse(await file.text());if(value.schema_version!==1 || Object.keys(value).some(k=>!(k in defaults)))throw Error('Configuración incompatible');setSettings({...defaults,...value});setError('')}catch(err){setError(String(err))}}}/></label>
    <button disabled={busy || jobs.some(j=>['preparing','rendering'].includes(j.status))} onClick={()=>void action(`evaluations/${report.job_id}/exports/${report.manifest.runs.findIndex((r:Data)=>r.pcm?.file===run.pcm.file)}`,settings)}>Exportar comparación elegida</button>
    <p>Figura de osciladores antes del timbre/limitador; no es cymatics físico ni una medición de latencia. Sin esqueletos. Persistencia depende de FPS; máximo 120 s de PCM incluida la cola.</p>
    {jobs.filter(j=>j.evaluation_id===report.job_id).map(j=><div key={j.id}><p>Corrida {j.run_index+1}: {j.status} · {j.frames}/{j.planned_frames || '?'} fotogramas {j.error && `· ${j.error}`}</p>
      {['preparing','rendering'].includes(j.status) && <button onClick={()=>void action(`comparison-exports/${j.id}/cancel`,{})}>Cancelar exportación</button>}
      {j.status==='complete' && <>{[j.output.file,'manifest.json','frames.jsonl'].map(file=><a key={file} download href={`/api/comparison-exports/${j.id}/artifacts/${file}`}>Descargar {file} </a>)}</>}
    </div>)}
    {error && <p role="alert">{error}</p>}
  </details>;
}
