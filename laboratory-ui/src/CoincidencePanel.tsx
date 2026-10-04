import {R03Comparison} from './R03Comparison';
import {useEffect,useState} from 'react';
type Data=Record<string,any>;
const defaults={high:1,low:.2,refractory_s:.2,max_gap_s:.1,tolerance_s:.2,mark_offset_s:0,timing_half_width_s:0,timing_steps_per_side:2};
export function CoincidencePanel({api,run}:Data){
 const [evaluations,setEvaluations]=useState<Data[]>([]),[jobs,setJobs]=useState<Data[]>([]);
 const [evaluation,setEvaluation]=useState(''),[report,setReport]=useState<Data|null>(null),[index,setIndex]=useState(0),[signal,setSignal]=useState('');
 const [marks,setMarks]=useState<Data|null>(null),[group,setGroup]=useState(''),[settings,setSettings]=useState<Data>(defaults);
 const [start,setStart]=useState(0),[end,setEnd]=useState(1),[support,setSupport]=useState(''),[config,setConfig]=useState(''),[error,setError]=useState('');
 const [offsets,setOffsets]=useState('[]'),[result,setResult]=useState<Data|null>(null),[busy,setBusy]=useState(false);
 const refresh=async()=>{try{
  const [e,m]=await Promise.all([api('evaluations'),api('marks/snapshot')]);
  setEvaluations(e.filter((j:Data)=>j.status==='complete'));setMarks(m);setGroup('');setError('');
 }catch(e){setError(String(e));}};
 useEffect(()=>{void refresh();},[api]);
 useEffect(()=>{let live=true;const poll=async()=>{try{const value=await api('research/r03');if(live)setJobs(value);}catch(e){if(live)setError(String(e));}};
  void poll();const timer=setInterval(poll,1000);return()=>{live=false;clearInterval(timer);};},[api]);
 useEffect(()=>{let live=true;setReport(null);setSignal('');if(evaluation)void api(`evaluations/${evaluation}/report`).then((value:Data)=>{if(live){setReport(value);setIndex(0);}}).catch((e:any)=>{if(live)setError(String(e));});return()=>{live=false;};},[evaluation,api]);
 const selected=report?.manifest.runs[index],source=selected && report?.manifest.request.sources[selected.source_index];
 useEffect(()=>{if(source){setStart(source.start_s);setEnd(Math.min(source.end_s,source.start_s+120));setSignal('');}},[report,index]);
 const groups:Data={};
 for(const row of marks?.marks || []){
  const event=row.event,p=event.payload;
  if(p.annotation_origin!=='human_button' || p.observed_epoch!==p.transport_epoch || !Number.isInteger(p.observed_epoch))continue;
  const context={source_id:p.source_id,person_id:p.person_id,session_id:event.session_id,observed_epoch:p.observed_epoch,category:p.annotation_category};
  if(!context.source_id || !context.person_id || !context.session_id || !context.category)continue;
  const key=JSON.stringify(context);groups[key] ??={context,count:0};groups[key].count++;
 }
 let intervals:unknown=null;
 try{intervals=JSON.parse(support);}catch{}
 const coverage=Array.isArray(intervals) && intervals.length>0 && intervals.length<=500 && intervals.every((v:any,i:number)=>Array.isArray(v) && v.length===2 && v.every((n:any)=>typeof n==='number' && Number.isFinite(n)) && v[0]>=0 && v[1]>v[0] && (!i || v[0]>=(intervals as any[])[i-1][1]));
 let shifts:unknown=null;try{shifts=JSON.parse(offsets);}catch{}
 const shiftsValid=Array.isArray(shifts) && shifts.length<=16 && new Set(shifts).size===shifts.length && shifts.every(v=>typeof v==='number' && Number.isFinite(v) && v!==0 && Math.abs(v)<=10 && Math.abs(v+settings.mark_offset_s)<=10);
 const context=groups[group]?.context;
 const valid=!!source && !!selected?.signals?.[signal] && !!context && source.person_id===context.person_id && end>start && start>=0 && end-start<=120 && coverage && shiftsValid && settings.refractory_s>=0 && settings.refractory_s<=10 && settings.max_gap_s>0 && settings.max_gap_s<=5 && settings.tolerance_s>=0 && settings.tolerance_s<=10 && Math.abs(settings.mark_offset_s)<=10 && settings.timing_half_width_s>=0 && settings.timing_half_width_s<=5 && Math.abs(settings.mark_offset_s)+settings.timing_half_width_s<=10 && Number.isInteger(settings.timing_steps_per_side) && settings.timing_steps_per_side>=1 && settings.timing_steps_per_side<=8 && settings.low<settings.high && Object.values(settings).every(v=>typeof v==='number' && Number.isFinite(v));
 const active=busy || jobs.some(j=>['queued','running'].includes(j.status));
 return <section>
  <h2>R03 · Coincidencia temporal</h2>
  <p>Contrasta marcas humanas con cruces de una señal causal. No demuestra intención ni causalidad. El reloj de los botones conserva la latencia de reacción.</p>
  <button onClick={()=>void refresh()}>Actualizar fuentes y corte de marcas R03</button>
  {error && <p role="alert">{error}</p>}
  <label>Comparación R03<select value={evaluation} onChange={e=>setEvaluation(e.target.value)}><option value="">Elegir comparación terminada</option>{evaluations.map(j=><option key={j.id} value={j.id}>{j.id}</option>)}</select></label>
  {report && <><label>Corrida R03<select value={index} onChange={e=>setIndex(+e.target.value)}>{report.manifest.runs.map((r:Data,i:number)=><option key={i} value={i}>Fuente {r.source_index+1} · {r.preset_id}</option>)}</select></label>
   <p>Persona del replay: {source?.person_id}</p>
   <label>Señal R03<select value={signal} onChange={e=>setSignal(e.target.value)}><option value="">Elegir señal</option>{Object.entries(selected?.signals || {}).map(([id,s]:[string,any])=><option key={id} value={id}>{id} · {s.unit}</option>)}</select></label></>}
  <label>Grupo de marcas R03<select value={group} onChange={e=>setGroup(e.target.value)}><option value="">Elegir sesión, época, persona y categoría</option>{Object.entries(groups).map(([key,g]:[string,any])=><option key={key} value={key}>{g.context.source_id} · {g.context.person_id} · {g.context.session_id} · época {g.context.observed_epoch} · {g.context.category} · {g.count} marcas</option>)}</select></label>
  <p>Corte congelado de marcas: {marks?.through_sequence ?? 'sin cargar'}. Actualizar cambia el corte y exige volver a elegir el grupo.</p>
  <label>Inicio R03 (s)<input type="number" value={start} onChange={e=>setStart(+e.target.value)}/></label>
  <label>Fin R03 (s)<input type="number" value={end} onChange={e=>setEnd(+e.target.value)}/></label>
  <label>Intervalos realmente observados R03 (JSON)<textarea value={support} placeholder="[[0,60]]" onChange={e=>setSupport(e.target.value)}/></label>
  <p>Declarar intervalos [inicio,fin) ordenados, sin solapamientos. No se deducen de las marcas ni se rellenan automáticamente.</p>
  {Object.entries(defaults).map(([key])=><label key={key}>{({high:'Umbral alto',low:'Umbral bajo',refractory_s:'Refractario (s)',max_gap_s:'Gap máximo (s)',tolerance_s:'Tolerancia (s)',mark_offset_s:'Offset manual de marcas (s)',timing_half_width_s:'Semiancho de sensibilidad temporal (s)',timing_steps_per_side:'Pasos temporales por lado'} as Data)[key]} R03<input type="number" step=".01" value={settings[key]} onChange={e=>setSettings({...settings,[key]:+e.target.value})}/></label>)}
  <p>Semiancho 0 desactiva el barrido. Declarar un rango alrededor del offset para ver la sensibilidad al tiempo de reacción/reloj. No mide latencia ni elige un mejor offset; los rangos muestreados no son intervalos de confianza. Todos los puntos usan soporte común.</p>
  <label>Desplazamientos de control R03 (JSON, segundos)<input value={offsets} onChange={e=>setOffsets(e.target.value)}/></label>
  <p>[] desactiva controles. Elegí hasta 16 desplazamientos distintos, no nulos, dentro de ±10 s. Cada condición usa la misma intersección de soporte; no se estima un offset óptimo ni significación.</p>
  <p>Umbrales en la unidad de la señal; el offset no se estima. Faltantes y gaps exigen un nuevo cruce desde abajo. El servidor verifica medio, cache y generación antes de ejecutar.</p>
  <button disabled={!valid || active} onClick={()=>run(async()=>{setBusy(true);try{await api('research/r03',{candidate:{evaluation_id:evaluation,run_index:index,signal_id:signal,start_s:start,end_s:end,high:settings.high,low:settings.low,refractory_s:settings.refractory_s,max_gap_s:settings.max_gap_s},...context,through_sequence:marks!.through_sequence,mark_support:intervals,control_offsets_s:shifts,tolerance_s:settings.tolerance_s,mark_offset_s:settings.mark_offset_s,timing_half_width_s:settings.timing_half_width_s,timing_steps_per_side:settings.timing_steps_per_side});setJobs(await api('research/r03'));}finally{setBusy(false);}})}>Correr contraste R03</button>
  <button onClick={()=>setConfig(JSON.stringify({settings,signal_id:signal,control_offsets_s:shifts},null,2))}>Exportar configuración R03</button>
  <textarea aria-label="Configuración R03 JSON" value={config} onChange={e=>setConfig(e.target.value)}/>
  <button onClick={()=>run(async()=>{const value=JSON.parse(config);if(typeof value.signal_id!=='string' || !value.settings || Object.entries(value.settings).some(([k,v])=>!(k in defaults) || typeof v!=='number' || !Number.isFinite(v)))throw Error('Configuración R03 inválida');if(value.control_offsets_s!==undefined && (!Array.isArray(value.control_offsets_s) || value.control_offsets_s.some((v:any)=>typeof v!=='number' || !Number.isFinite(v))))throw Error('Controles R03 inválidos');setSettings({...defaults,...value.settings});setSignal(value.signal_id);setOffsets(JSON.stringify(value.control_offsets_s || []));})}>Importar configuración R03</button>
  <p>La configuración portable conserva señal y algoritmo; persona, sesión, época y cobertura se eligen para cada fuente.</p>
  <R03Comparison api={api} jobs={jobs}/>
  {jobs.map(j=><div key={j.id}><p>{j.id} · {j.status} · {j.error || ''}</p>{['queued','running'].includes(j.status) && <button onClick={()=>run(async()=>{await api(`research/r03/${j.id}/cancel`,{});setJobs(await api('research/r03'));})}>Cancelar R03 {j.id}</button>}{j.status==='complete' && <><button onClick={()=>run(async()=>setResult(await api(`research/r03/${j.id}/artifacts/result.json`)))}>Ver resultado R03 {j.id}</button>{['result.json','request.json','marks.json','features.json','manifest.json'].map(name=><a key={name} href={`/api/research/r03/${j.id}/artifacts/${name}`}>{name} </a>)}</>}</div>)}
  {result && <><p>Soporte común: {result.comparison.support_duration_s} s · coincidencias: {result.comparison.matches.length} · precisión: {result.comparison.precision ?? 'sin denominador'} · recall: {result.comparison.recall ?? 'sin denominador'}</p>{result.temporal_controls && <table><thead><tr><th>Desplazamiento (s)</th><th>Soporte disponible (s)</th><th>Soporte común (s)</th><th>Marcas elegibles</th><th>Candidatos elegibles</th><th>Coincidencias</th><th>Precisión</th><th>Recall</th></tr></thead><tbody>{result.temporal_controls.conditions.map((c:Data)=><tr key={c.shift_s}><td>{c.shift_s}</td><td>{c.available.support_duration_s}</td><td>{c.paired.support_duration_s}</td><td>{c.paired.eligible_marks}</td><td>{c.paired.eligible_candidates}</td><td>{c.paired.matches.length}</td><td>{c.paired.precision ?? 'sin denominador'}</td><td>{c.paired.recall ?? 'sin denominador'}</td></tr>)}</tbody></table>}{result.timing_sensitivity && <><p>Sensibilidad temporal · soporte común: {result.timing_sensitivity.support_duration_s} s · precisión muestreada: {result.timing_sensitivity.sampled_metric_ranges.precision.min ?? 'sin denominador'} a {result.timing_sensitivity.sampled_metric_ranges.precision.max ?? 'sin denominador'} · recall muestreado: {result.timing_sensitivity.sampled_metric_ranges.recall.min ?? 'sin denominador'} a {result.timing_sensitivity.sampled_metric_ranges.recall.max ?? 'sin denominador'}</p><table><thead><tr><th>Offset total (s)</th><th>Marcas</th><th>Candidatos</th><th>Coincidencias</th><th>Precisión</th><th>Recall</th></tr></thead><tbody>{result.timing_sensitivity.conditions.map((c:Data)=><tr key={c.shift_s}><td>{result.timing_sensitivity.center_offset_s+c.shift_s}</td><td>{c.paired.eligible_marks}</td><td>{c.paired.eligible_candidates}</td><td>{c.paired.matches.length}</td><td>{c.paired.precision ?? 'sin denominador'}</td><td>{c.paired.recall ?? 'sin denominador'}</td></tr>)}</tbody></table></>}<pre>{JSON.stringify(result,null,2)}</pre></>}
 </section>;
}
