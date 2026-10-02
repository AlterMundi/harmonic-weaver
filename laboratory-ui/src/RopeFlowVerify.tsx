import {useEffect,useRef,useState} from 'react';
type Data=Record<string,any>;
export function RopeFlowVerify({api,source,runId,disabled}:Data){
 const [history,setHistory]=useState<Data[]>([]);
 const [job,setJob]=useState<Data|null>(null),[error,setError]=useState('');
 const live=useRef(true),active=useRef(''),polling=useRef(false);
 useEffect(()=>{live.current=true;return()=>{live.current=false;if(active.current)void api(`research/r08/flow-verifications/${active.current}/cancel`,{}).catch(()=>{});};},[api]);
 useEffect(()=>{let current=true;void api(`research/r08/flow-verifications?source_run_id=${runId}`).then((rows:Data[])=>{if(current)setHistory(rows);}).catch((e:unknown)=>{if(current)setError(String(e));});return()=>{current=false;};},[api,runId]);
 const observe=async(id:string,initial?:Data)=>{
  if(polling.current)return;polling.current=true;setError('');
  try{
   let state=initial||await api(`research/r08/flow-verifications/${id}`);if(live.current)setJob(state);
   while(live.current&&state.status==='running'){await new Promise(r=>setTimeout(r,100));if(!live.current)return;state=await api(`research/r08/flow-verifications/${id}`);if(live.current)setJob(state);}
   if(live.current&&state.status==='complete'){const rows=await api(`research/r08/flow-verifications?source_run_id=${runId}`);if(!live.current)return;setHistory(rows);}
   if(live.current){active.current='';setJob(state);if(state.status==='failed')setError(state.error);}
  }catch(e){if(live.current){setError(String(e));setJob({id,status:'connection_lost'});}}
  finally{polling.current=false;}
 };
 const start=async()=>{
  setError('');setJob({status:'starting'});
  try{const j=await api(`research/r08/flow/${runId}/reverify`,{media_id:source});active.current=j.id;if(!live.current){await api(`research/r08/flow-verifications/${j.id}/cancel`,{});return;}await observe(j.id,j);}
  catch(e){if(live.current){setError(String(e));setJob({status:'failed'});}}
 };
 return <span>
 <button disabled={disabled||Boolean(active.current)||job?.status==='starting'} onClick={()=>void start()}>Recalcular corrida temporal R08</button>
 <button disabled={!active.current} onClick={()=>{const id=active.current;void api(`research/r08/flow-verifications/${id}/cancel`,{}).then((j:Data)=>{if(live.current&&!polling.current)void observe(id,j);}).catch((e:unknown)=>{if(live.current)setError(String(e));});}}>Cancelar recálculo temporal R08</button>
 <button disabled={!active.current||job?.status!=='connection_lost'} onClick={()=>void observe(active.current)}>Retomar recálculo temporal R08</button>
 {job&&<span role="status">Recálculo temporal R08: {job.status}{job.verification==='recomputed'?' · Coincidió contra la fuente en este recálculo.':''}</span>}
 {job?.verification==='recomputed'&&<details><summary>Evidencia del recálculo temporal R08</summary><pre>{JSON.stringify(job,null,2)}</pre><p>Manifest ligado al recálculo; comprobación de esta sesión; registro histórico descargable. No modifica originales ni valida identidad física.</p></details>}
 {history.map(h=><span key={h.id}>Evidencia histórica de recálculo: {h.checked_at_utc}. Lectura por integridad; no verifica la fuente actual. {['report.json','manifest.json'].map(name=><a key={name} href={`/api/research/r08/flow-verifications/${h.id}/artifacts/${name}`} download>{`Descargar evidencia temporal ${name}`} </a>)}</span>)}
 {error&&<span role="alert">{error}</span>}
 </span>;
}
