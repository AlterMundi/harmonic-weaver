import {useEffect,useRef,useState} from 'react';
type Data=Record<string,any>;
const defaults={frames:10,settings:{window_px:21,pyramid_levels:3,iterations:30,epsilon:.01,min_eigenvalue:.0001,max_forward_backward_error_px:1,max_displacement_px:100,max_gap_s:.2,max_points:128}};
export function RopeFlowPanel({api,media,source,index,endpoints,ready,onFrame}:Data){
 const [presets,setPresets]=useState<Data[]>([]),[presetName,setPresetName]=useState(''),[presetBusy,setPresetBusy]=useState(false);
 const [config,setConfig]=useState(JSON.stringify(defaults,null,2)),[seeds,setSeeds]=useState('[]');
 const [jobs,setJobs]=useState<Data[]>([]),[status,setStatus]=useState<Data|null>(null),[result,setResult]=useState<Data|null>(null),[error,setError]=useState('');
 const alive=useRef(true),active=useRef('');const pending=useRef<Data|null>(null),sending=useRef(false);const observing=useRef(false);const busy=presetBusy||Boolean(pending.current)||Boolean(active.current)||status?.status==='starting'||status?.status==='running';
 useEffect(()=>{alive.current=true;void api('research/r08/flow').then((j:Data[])=>{if(alive.current)setJobs(j);}).catch((e:unknown)=>{if(alive.current)setError(String(e));});return()=>{alive.current=false;if(active.current)void api(`research/r08/flow/${active.current}/cancel`,{}).catch(()=>{});};},[api]);
 const receiptKey=`r08-flow-pending-v1:${source}:${media.media_sha256}`;
 useEffect(()=>{
  try{
   const raw=sessionStorage.getItem(receiptKey);if(!raw)return;
   if(raw.length>1_000_000)throw Error('Recibo temporal supera presupuesto');
   const saved=JSON.parse(raw);
   if(saved.version!==1||saved.body?.media_id!==source||saved.body?.request?.media_sha256!==media.media_sha256||!(/^[a-f0-9]{32}$/).test(saved.body?.idempotency_key||''))throw Error('Recibo temporal incompatible con fuente');
   if(saved.id){if(!(/^[a-f0-9]{32}$/).test(saved.id))throw Error('ID temporal inválido');active.current=saved.id;setStatus({id:saved.id,status:'connection_lost'});}
   else{pending.current=saved.body;setStatus({status:'start_unknown'});}
  }catch(e){setError(String(e));}
 },[receiptKey,source,media.media_sha256]);
 useEffect(()=>{let live=true;void api('research/r08/flow-presets').then((p:Data[])=>{if(live)setPresets(p);}).catch((e:unknown)=>{if(live)setError(String(e));});return()=>{live=false;};},[api]);
 const savePreset=async(body:Data)=>{
  setPresetBusy(true);setError('');
  try{await api('research/r08/flow-presets',body);const p=await api('research/r08/flow-presets');if(alive.current)setPresets(p);}
  catch(e){if(alive.current)setError(String(e));}finally{if(alive.current)setPresetBusy(false);}
 };
 useEffect(()=>{setSeeds('[]');},[source,index]);
 const observe=async(id:string,initial?:Data)=>{
  if(observing.current)return;observing.current=true;setError('');
  try{
   let state=initial||await api(`research/r08/flow/${id}`);if(alive.current)setStatus(state);
   while(alive.current&&state.status==='running'){await new Promise(r=>setTimeout(r,100));if(!alive.current)return;state=await api(`research/r08/flow/${id}`);if(alive.current)setStatus(state);}
   if(!alive.current)return;
   if(state.status==='complete'){
    const r=await api(`research/r08/flow/${id}/artifacts/result.json`);if(!alive.current)return;
    setResult(r);const j=await api('research/r08/flow');if(!alive.current)return;setJobs(j);
   }
   sessionStorage.removeItem(receiptKey);active.current='';setStatus(state);
   if(state.status==='failed')setError(state.error||'Falló corrida temporal');
  }catch(e){if(alive.current){setError(String(e));setStatus({id,status:'connection_lost'});}}
  finally{observing.current=false;}
 };
 const submit=async()=>{
  if(sending.current||!pending.current)return;sending.current=true;setError('');setStatus({status:'starting'});
  try{
   const job=await api('research/r08/flow',pending.current);
   sessionStorage.setItem(receiptKey,JSON.stringify({version:1,body:pending.current,id:job.id}));
   pending.current=null;active.current=job.id;
   if(!alive.current){await api(`research/r08/flow/${job.id}/cancel`,{});return;}
   await observe(job.id,job);
  }catch(e){if(alive.current){
   const code=(e as Data)?.status;
   if(code>=400&&code<500){sessionStorage.removeItem(receiptKey);pending.current=null;}
   setError(String(e));setStatus({status:pending.current?'start_unknown':'failed'});
  }}finally{sending.current=false;}
 };
 const start=async()=>{
  setError('');setStatus({status:'starting'});setResult(null);
  try{
   const c=JSON.parse(config);if(Object.keys(c).some(k=>!['frames','settings'].includes(k)))throw Error('Configuración portable admite sólo frames y settings');
   if(!Number.isInteger(c.frames)||c.frames<2||c.frames>120)throw Error('Elegí entre 2 y 120 cuadros');
   const times=media.frame_times_s.slice(index,index+c.frames);if(times.length!==c.frames)throw Error('No quedan suficientes cuadros; ajustá rango');
   const body={media_id:source,idempotency_key:crypto.randomUUID().replaceAll('-',''),request:{media_sha256:media.media_sha256,width_px:media.width_px,height_px:media.height_px,start_frame_index:index,frame_times_s:times,seeds:JSON.parse(seeds),settings:c.settings}};
   const receipt=JSON.stringify({version:1,body});if(receipt.length>1_000_000)throw Error('Recibo temporal supera presupuesto');
   sessionStorage.setItem(receiptKey,receipt);pending.current=body;
   await submit();
  }catch(e){if(alive.current){setError(String(e));setStatus({status:'failed'});}}
 };
 const frame=ready&&result&&result.request.media_sha256===media.media_sha256&&result.request.width_px===media.width_px&&result.request.height_px===media.height_px?result.frames.find((f:Data)=>f.frame_index===index&&f.time_s===media.frame_times_s[index]):null;
 useEffect(()=>{onFrame(frame?{...frame,media_sha256:media.media_sha256}:null);return()=>onFrame(null);},[frame,onFrame,media.media_sha256]);
 return <section><h3>R08 · Candidatos temporales</h3><p>Flujo óptico desde seeds explícitos. No identifica material ni acepta anotaciones. Descargas verifican integridad; no recalculan contra el video.</p>
 {error&&<p role="alert">{error}</p>}
 <label>Configuración temporal portable R08<textarea rows={12} value={config} disabled={busy} onChange={e=>setConfig(e.target.value)}/></label>
 <p>El intento pendiente se conserva sólo en esta pestaña para retomar explícitamente tras recargar; contiene seeds de esta fuente, separados del preset.</p><p>Podés copiar y recuperar este JSON entre fuentes: no incluye seeds, video ni calibración. El rango empieza en el cuadro actual {index}.</p>
 <label>Nombre de preset temporal R08<input value={presetName} disabled={busy} maxLength={80} onChange={e=>setPresetName(e.target.value)}/></label>
 <button disabled={busy||!presetName.trim()} onClick={()=>{try{void savePreset({name:presetName.trim(),config:JSON.parse(config)});}catch(e){setError(String(e));}}}>Guardar preset temporal R08</button>
 <label>Importar preset temporal R08<input type="file" accept="application/json,.json" disabled={busy} onChange={e=>{const file=e.target.files?.[0];e.target.value='';if(!file)return;if(file.size>65536){setError('Preset supera 64 KiB');return;}setPresetBusy(true);void file.text().then(t=>savePreset(JSON.parse(t))).catch((e:unknown)=>{if(alive.current){setError(String(e));setPresetBusy(false);}});}}/></label>
 {presets.map(p=><div key={p.id}>{p.name} <button disabled={busy} onClick={()=>setConfig(JSON.stringify(p.config,null,2))}>Aplicar preset temporal R08 {p.name}</button><a href={`/api/research/r08/flow-presets/${p.id}`} download>Exportar preset temporal R08 {p.name}</a></div>)}
 <label>Seeds temporales R08<textarea rows={4} value={seeds} disabled={busy} onChange={e=>setSeeds(e.target.value)}/></label>
 <button disabled={busy||!ready||!Object.keys(endpoints).length} onClick={()=>setSeeds(JSON.stringify(['a','b'].filter(k=>endpoints[k]).map(k=>endpoints[k]),null,2))}>Copiar extremos actuales como seeds R08</button>
 <button disabled={busy||!ready} onClick={()=>void start()}>Iniciar corrida temporal R08</button>
 <button disabled={!active.current} onClick={()=>{const id=active.current;void api(`research/r08/flow/${id}/cancel`,{}).then((state:Data)=>{if(alive.current&&!observing.current)void observe(id,state);}).catch((e:unknown)=>{if(alive.current)setError(String(e));});}}>Cancelar corrida temporal R08</button>
 {status&&<p role="status">Corrida temporal R08: {status.status}{status.id?` · ${status.id}`:''}</p>}
 <button disabled={!pending.current||status?.status!=='start_unknown'} onClick={()=>void submit()}>Reintentar mismo inicio temporal R08</button>
 <button disabled={!active.current||status?.status!=='connection_lost'} onClick={()=>void observe(active.current)}>Retomar consulta temporal R08</button>
 {result&&<><p>Resultado temporal R08: {result.frames.length} cuadros. {frame?`Cuadro actual: ${frame.status}, ${frame.rows.filter((r:Data)=>r.point).length} puntos con soporte.`:'Cuadro actual fuera de la corrida.'}</p>
 {frame&&<svg aria-label="Candidatos temporales R08" viewBox={`0 0 ${media.width_px} ${media.height_px}`} style={{width:'100%',maxWidth:600,background:'#171717'}}>{frame.rows.filter((r:Data)=>r.point).map((r:Data)=><g key={r.seed_index}><circle cx={r.point.x*media.width_px} cy={r.point.y*media.height_px} r={3} fill="cyan"/><text x={r.point.x*media.width_px+5} y={r.point.y*media.height_px} fill="white">{r.seed_index}</text></g>)}</svg>}
 <details><summary>Resultado temporal congelado R08</summary><pre>{JSON.stringify(result,null,2)}</pre></details>
 <button disabled={busy} onClick={()=>setConfig(JSON.stringify({frames:result.frames.length,settings:result.request.settings},null,2))}>Recuperar sólo configuración temporal R08</button></>}
 {jobs.map(j=><div key={j.id}>{j.id} · Integridad verificada, sin recálculo de video. <button disabled={busy} onClick={()=>{setError('');void api(`research/r08/flow/${j.id}/artifacts/result.json`).then((r:Data)=>{if(alive.current)setResult(r);}).catch((e:unknown)=>{if(alive.current)setError(String(e));});}}>Ver corrida temporal R08</button>{['request.json','result.json','manifest.json'].map(n=><a key={n} href={`/api/research/r08/flow/${j.id}/artifacts/${n}`} download>{n} </a>)}</div>)}
 </section>;
}
