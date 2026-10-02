import {RopeEditor} from './RopeEditor';
import {useEffect,useState} from 'react';
type Data=Record<string,any>;
export function RopePanel({api}:Data){
 const [assets,setAssets]=useState<Data[]>([]),[jobs,setJobs]=useState<Data[]>([]),[source,setSource]=useState(''),[text,setText]=useState(''),[parent,setParent]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const [media,setMedia]=useState<Data|null>(null);
 const act=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');try{await fn();}catch(e){setError(String(e));}finally{setBusy(false);}};
 useEffect(()=>{let live=true;void Promise.all([api('media'),api('research/r08')]).then(([a,j]:Data[])=>{if(live){setAssets(a as any);setJobs(j as any);}}).catch(e=>{if(live)setError(String(e));});return()=>{live=false;};},[api]);
 return <section><h2>R08 · Soga visible</h2><p>Anotación manual por segmentos. Longitud proyectada en píxeles; los cruces no prueban profundidad ni nudos. Cada guardado crea una revisión nueva.</p>{error&&<p role="alert">{error}</p>}
 <label>Video de biblioteca R08<select value={source} disabled={busy} onChange={e=>{setSource(e.target.value);setMedia(null);setParent('');setText('');}}><option value="">Elegir video</option>{assets.map(a=><option key={a.id} value={a.id}>{a.name}</option>)}</select></label>
 <button disabled={busy||!source} onClick={()=>void act(async()=>{const m=await api('research/r08/probe',{media_id:source});setMedia(m);setParent('');setText(JSON.stringify({schema_version:1,media_sha256:m.media_sha256,width_px:m.width_px,height_px:m.height_px,frames:[]},null,2));})}>Preparar anotación R08</button>
 <p>Frames con índice y tiempo real del archivo; curvas normalizadas [0,1]. Estados: observed, partial, unidentifiable, absent. Partial/unidentifiable requieren causas: blur, occlusion, crossing_ambiguity, out_of_frame. No unir tramos ocultos.</p>
 {media&&source&&<RopeEditor key={source} media={media} source={source} text={text} onChange={setText}/>}
 <label>Anotación R08 JSON<textarea rows={18} value={text} onChange={e=>setText(e.target.value)}/></label>
 <p>Revisión previa: {parent||'ninguna'}</p>
 <button disabled={busy||!source||!text} onClick={()=>void act(async()=>{const j=await api('research/r08',{media_id:source,annotation:JSON.parse(text),parent_id:parent||null});setParent(j.id);setJobs(await api('research/r08'));})}>Guardar revisión R08</button>
 {jobs.map(j=><div key={j.id}>{j.id}<button disabled={busy} onClick={()=>void act(async()=>{setText(JSON.stringify(await api(`research/r08/${j.id}/artifacts/annotation.json`),null,2));setParent(j.id);setMedia(null);})}>Abrir revisión R08</button><button disabled={busy||!source} onClick={()=>void act(async()=>{setMedia(await api(`research/r08/${j.id}/rebind`,{media_id:source}));})}>Verificar video R08</button>{['annotation.json','media.json','result.json','manifest.json'].map(n=><a key={n} href={`/api/research/r08/${j.id}/artifacts/${n}`} download>{n} </a>)}</div>)}
 </section>;
}
