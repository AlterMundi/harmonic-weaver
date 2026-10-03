import {MultiviewPanel} from './MultiviewPanel';
import {SpatialClockFit} from './SpatialClockFit';
import {SpatialCompare} from './SpatialCompare';
import {SpatialView} from './SpatialView';
import {useEffect,useState} from 'react';
type Data=Record<string,any>;
const defaultClock={source_clock:'pts',common_clock:'session',offset_s:0,rate:1,uncertainty_s:0,method:'declared_assumption',evidence_id:null};
export function SpatialPanel({api}:{api:any}){
 const receiptKey='weaver.r09.save.pending.v1';
 const [pending,setPending]=useState<Data|null>(null);
 useEffect(()=>{try{const raw=sessionStorage.getItem(receiptKey);if(!raw)return;if(raw.length>32*1024*1024)throw Error('oversize');const p=JSON.parse(raw);if(!['conversions','source-conversions'].includes(p.route)||!p.body||!/^[a-f0-9]{32}$/.test(p.body.idempotency_key))throw Error('invalid');setPending(p);}catch{sessionStorage.removeItem(receiptKey);}},[]);
 const [runs,setRuns]=useState<Data[]>([]);
 useEffect(()=>{let live=true;void api('research/r09/conversions').then((r:Data[])=>{if(live)setRuns(r);}).catch(()=>{});return()=>{live=false;};},[api]);
 const [text,setText]=useState('[]'),[person,setPerson]=useState(''),[clock,setClock]=useState(JSON.stringify(defaultClock,null,2));
 const [sources,setSources]=useState<Data[]>([]),[job,setJob]=useState(''),[start,setStart]=useState(0),[end,setEnd]=useState(1);
 const [mode,setMode]=useState('convert'),[busy,setBusy]=useState(false),[error,setError]=useState(''),[result,setResult]=useState<Data|null>(null);
 const act=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');try{await fn();}catch(e){setError(String(e));}finally{setBusy(false);}};
 const save=async(route:string,body:Data)=>{
  const attempt=pending||{route,body:{...body,idempotency_key:crypto.randomUUID().replaceAll('-','')}};
  sessionStorage.setItem(receiptKey,JSON.stringify(attempt));setPending(attempt);
  try{await api(`research/r09/${attempt.route}`,attempt.body);sessionStorage.removeItem(receiptKey);setPending(null);setRuns(await api('research/r09/conversions'));}
  catch(e){const status=(e as any)?.status;if(status>=400&&status<500){sessionStorage.removeItem(receiptKey);setPending(null);}throw e;}
 };
 const exportResult=()=>{const blob=new Blob([JSON.stringify(result,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='r09-spatial-result.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
 return <section aria-label="Observaciones espaciales R09"><h2>R09 · Observaciones y relojes</h2>
 <p>Importación explícita para investigación. La conversión conserva el plano de imagen y sus unidades; validar un contrato no verifica profundidad, calibración ni sincronización.</p>
 <label>Modalidad R09<select disabled={busy} value={mode} onChange={e=>{setMode(e.target.value);setResult(null);}}><option value="convert">Convertir MotionFrames 2D</option><option value="source">Desde tracking completo</option><option value="validate">Validar Stream espacial</option></select></label>
 <label>Importar JSON local R09<input disabled={busy} type="file" accept="application/json,.json" onChange={e=>{const file=e.target.files?.[0];if(file)void act(async()=>{if(file.size>32*1024*1024)throw Error('JSON supera 32 MiB');const raw=await file.text();JSON.parse(raw);setText(raw);setResult(null);});e.target.value='';}}/></label>
 <label>Observaciones JSON R09<textarea disabled={busy} rows={10} value={text} onChange={e=>{setText(e.target.value);setResult(null);}}/></label>
 {mode!=='validate'&&<><label>Slot explícito R09<input disabled={busy} value={person} onChange={e=>{setPerson(e.target.value);setResult(null);}}/></label>
 <label>Mapeo de reloj JSON R09<textarea disabled={busy} rows={8} value={clock} onChange={e=>{setClock(e.target.value);setResult(null);}}/></label>
 <p>t común = offset + rate × t fuente. El reloj inicial es una suposición editable, no una medición; incertidumbre cero no acredita sincronización.</p></>}
 {mode==='source'&&<div><button disabled={busy} onClick={()=>void act(async()=>setSources(await api('research/r09/sources')))}>Actualizar tracking R09</button>
 <label>Tracking completo R09<select disabled={busy} value={job} onChange={e=>{setJob(e.target.value);setPerson('');setResult(null);}}><option value="">Elegir generación</option>{sources.map(s=><option key={s.job_id} value={s.job_id}>{s.job_id} · {s.generation} · {s.effective_device}</option>)}</select></label>
 <p>Slots disponibles: {sources.find(s=>s.job_id===job)?.person_ids.join(', ')||'ninguno listado'}</p>
 <label>Inicio de segmento R09<input disabled={busy} type="number" min={0} value={start} onChange={e=>{setStart(Number(e.target.value));setResult(null);}}/></label>
 <label>Fin de segmento R09<input disabled={busy} type="number" min={0} value={end} onChange={e=>{setEnd(Number(e.target.value));setResult(null);}}/></label></div>}
 {pending&&<p role="status">Guardado R09 pendiente de confirmar. <button disabled={busy} onClick={()=>void act(async()=>save(pending.route,pending.body))}>Recuperar guardado R09</button></p>}
 {error&&<p role="alert">{error}</p>}
 <button disabled={busy||mode!=='validate'&&!person||mode==='source'&&!job} onClick={()=>void act(async()=>{setResult(null);if(mode==='source'){setResult(await api('research/r09/source',{job_id:job,start_s:start,end_s:end,person_id:person,clock:JSON.parse(clock)}));return;}if(text.length>32*1024*1024)throw Error('JSON supera límite');const observations=JSON.parse(text);setResult(await api(`research/r09/${mode}`,mode==='convert'?{frames:observations,person_id:person,clock:JSON.parse(clock)}:observations));})}>Procesar observaciones R09</button>
 {result&&<div><SpatialView key={JSON.stringify([result.stream.source_id,result.stream.subject_slot,result.stream.frames[0].source_time_s,result.stream.dimensions])} stream={result.stream} api={api}/><p>Contrato validado: {result.stream.provider} · {result.stream.dimensions}D · {result.stream.units} · slot {result.stream.subject_slot}.</p>
 {result.coverage&&<p>Cobertura R09: observados {result.coverage.observed}; sostenidos {result.coverage.held}; inferidos {result.coverage.inferred}; faltantes {result.coverage.missing}.</p>}
 {result.tracking_provenance&&<button disabled={busy||!!pending} onClick={()=>void act(async()=>{const p=result.tracking_provenance;await save('source-conversions',{job_id:p.job_id,start_s:p.start_s,end_s:p.end_s,person_id:result.request.person_id,clock:result.request.clock,expected_generation:p.generation});})}>Guardar desde generación R09</button>}
 {result.request?.frames&&result.request?.person_id&&<button disabled={busy||!!pending} onClick={()=>void act(async()=>{await save('conversions',{conversion:result.request});})}>Guardar conversión declarada R09</button>}
 <button disabled={busy||!!pending} onClick={()=>void act(async()=>save('conversions',{stream:result.stream}))}>Guardar stream declarado R09</button><p>Guardar stream declarado conserva su contrato; no incorpora como verificada la procedencia de un JSON importado.</p>
 <button onClick={exportResult}>Exportar resultado R09</button><details><summary>Resultado espacial R09</summary><pre>{JSON.stringify(result,null,2)}</pre></details></div>}
 <p>Guardar conserva la conversión y sus observaciones declaradas; no autentica el origen. Guardar desde generación resuelve la procedencia en el servidor; no revalida bytes del cache/video.</p>
 {runs.map(r=><div key={r.id}>{r.id} · {r.read_verification==='recomputed'?'Conversión recalculada':'Histórico: sólo integridad'}<button disabled={busy} onClick={()=>void act(async()=>setResult(await api(`research/r09/conversions/${r.id}/artifacts/result.json`)))}>Abrir conversión R09</button>{['request.json','result.json','manifest.json'].map(n=><a key={n} href={`/api/research/r09/conversions/${r.id}/artifacts/${n}`} download>{n} </a>)}</div>)}
 <MultiviewPanel api={api} onStream={stream=>{setMode('validate');setText(JSON.stringify(stream,null,2));setResult(null);}}/>
 <SpatialClockFit api={api}/>
 <SpatialCompare api={api}/>
 </section>;
}
