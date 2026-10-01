import {useEffect,useState} from 'react';
type Data=Record<string,any>;
const joints=['Nariz','Ojo izquierdo','Ojo derecho','Oreja izquierda','Oreja derecha','Hombro izquierdo','Hombro derecho','Codo izquierdo','Codo derecho','Muñeca izquierda','Muñeca derecha','Cadera izquierda','Cadera derecha','Rodilla izquierda','Rodilla derecha','Tobillo izquierdo','Tobillo derecho'];
export function RelationalBodyPanel({api,run,settings,settingsValid,active,onStarted}:Data){
 const [jobs,setJobs]=useState<Data[]>([]),[evaluation,setEvaluation]=useState(''),[report,setReport]=useState<Data|null>(null),[index,setIndex]=useState(0);
 const [parent,setParent]=useState(7),[child,setChild]=useState(9),[start,setStart]=useState(0),[end,setEnd]=useState(1),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 useEffect(()=>{let live=true;void api('evaluations').then((value:Data[])=>{if(live)setJobs(value.filter(j=>j.status==='complete'));}).catch((e:any)=>{if(live)setError(String(e));});return()=>{live=false;};},[api]);
 useEffect(()=>{let live=true;setReport(null);if(evaluation)void api(`evaluations/${evaluation}/report`).then((value:Data)=>{if(live){setReport(value);setIndex(0);}}).catch((e:any)=>{if(live)setError(String(e));});return()=>{live=false;};},[evaluation,api]);
 const selected=report?.manifest.runs[index],source=selected && report?.manifest.request.sources[selected.source_index];
 useEffect(()=>{if(source){setStart(source.start_s);setEnd(Math.min(source.end_s,source.start_s+120));}},[report,index]);
 const calibrated=source && typeof source.torso_scale==='number' && source.torso_scale>0 && !!source.calibration_provenance;
 const valid=calibrated && settingsValid && parent!==child && Number.isFinite(start) && Number.isFinite(end) && start>=source.start_s && end<=source.end_s && end>start && end-start<=120;
 return <section><h3>R04 · Extremos desde pose congelada</h3>
  <p>Usa los parámetros relacionales de arriba. samples/hz no se aplican: conserva timestamps de pose. El cálculo causal se calienta desde el inicio elegido.</p>
  {error && <p role="alert">{error}</p>}
  <label>Comparación corporal R04<select value={evaluation} onChange={e=>setEvaluation(e.target.value)}><option value="">Elegir comparación terminada</option>{jobs.map(j=><option key={j.id} value={j.id}>{j.id}</option>)}</select></label>
  {report && <label>Corrida corporal R04<select value={index} onChange={e=>setIndex(+e.target.value)}>{report.manifest.runs.map((r:Data,i:number)=><option key={i} value={i}>Fuente {r.source_index+1} · {r.preset_id}</option>)}</select></label>}
  {source && <p>Persona congelada: {source.person_id} · escala: {source.torso_scale ?? 'no disponible'} · procedencia: {source.calibration_provenance || 'no disponible'}</p>}
  {source && !calibrated && <p role="alert">Esta fuente no tiene escala y procedencia de calibración explícitas. Elegí una corrida calibrada; no se transfiere calibración.</p>}
  <label>Extremo proximal R04<select value={parent} onChange={e=>setParent(+e.target.value)}>{joints.map((name,i)=><option key={i} value={i}>{i} · {name}</option>)}</select></label>
  <label>Extremo distal R04<select value={child} onChange={e=>setChild(+e.target.value)}>{joints.map((name,i)=><option key={i} value={i}>{i} · {name}</option>)}</select></label>
  <label>Inicio corporal R04 (s)<input type="number" step=".1" value={start} onChange={e=>setStart(+e.target.value)}/></label>
  <label>Fin corporal R04 (s)<input type="number" step=".1" value={end} onChange={e=>setEnd(+e.target.value)}/></label>
  <p>Elegir dos extremos no afirma adyacencia anatómica ni identidad correcta del tracking. Faltantes reinician la relación; no se interpolan.</p>
  <button disabled={!valid || active || busy} onClick={()=>run(async()=>{setBusy(true);try{await api('research/r04/trace',{settings,selection:{evaluation_id:evaluation,run_index:index,parent_joint:parent,child_joint:child,start_s:start,end_s:end}});await onStarted();}finally{setBusy(false);}})}>Correr R04 con pose congelada</button>
 </section>;
}
