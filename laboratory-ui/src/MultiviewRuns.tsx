import {useEffect,useRef,useState} from 'react';
import {multiviewPending} from './multiviewPending';
type Data=Record<string,any>;
const root='research/r09/multiview/runs';
export function MultiviewRuns({api,request,revision,onOpen}:{api:any,request:Data|null,revision:number,onOpen:(result:Data)=>void}){
 const context=useRef(revision);context.current=revision;
 const mounted=useRef(true);useEffect(()=>{mounted.current=true;return()=>{mounted.current=false}},[]);
 const [rows,setRows]=useState<Data[]>([]),[pending,setPending]=useState<Data|null>(null),[loaded,setLoaded]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [id,setId]=useState(''),[report,setReport]=useState<Data|null>(null),[attempt,setAttempt]=useState(0);
 const running=report&&['queued','running'].includes(report.status);
 const refresh=async()=>setRows(await api(root));
 useEffect(()=>{let active=true;void multiviewPending().then(p=>{if(!active)return;if(p){setPending(p);if(!/^[a-f0-9]{32}$/.test(p.body?.idempotency_key||''))throw Error('Intento multivista local inválido; descartarlo para continuar')}setLoaded(true)}).catch((e:unknown)=>{if(active)setError(String(e))});void api(root).then((r:Data[])=>{if(active)setRows(r)}).catch((e:unknown)=>{if(active)setError(String(e))});return()=>{active=false};},[api]);
 useEffect(()=>{
  if(!id)return;let active=true;
  void(async()=>{try{while(active){const r=await api(`${root}/${id}`);if(!active)return;setReport(r);if(!['queued','running'].includes(r.status)){await refresh();return}await new Promise(resolve=>setTimeout(resolve,200))}}catch(e){if(active)setError(`Seguimiento no confirmado: ${String(e)}. Retomar consulta del mismo ID.`)}})();
  return()=>{active=false};
 },[api,id,attempt]);
 const act=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');try{await fn()}catch(e){setError(String(e))}finally{setBusy(false)}};
 const start=async(body:Data,recover=false)=>{
  const frozen=recover?pending:{body:{...JSON.parse(JSON.stringify(body)),idempotency_key:crypto.randomUUID().replaceAll('-','')}};
  if(!frozen)throw Error('No hay intento pendiente');
  await multiviewPending(frozen);setPending(frozen);
  try{const r=await api(root,frozen.body);setReport(r);setId(r.id);setAttempt(a=>a+1);await multiviewPending(null);setPending(null);await refresh()}
  catch(e){const status=(e as any)?.status;if(status>=400&&status<500){await multiviewPending(null);setPending(null)}throw e}
 };
 return <section aria-label="Cálculos multivista guardados R09"><h4>Calcular y guardar en worker</h4>
 <p>Guarda cámaras, calibración declarada, correspondencias, relojes, parámetros y resultado completos en esta máquina. Worker independiente cancelable; cerrar la pestaña no cancela el cálculo. No altera sonido ni tracking.</p>
 <button disabled={!loaded||busy||!!pending||!!running||!request} onClick={()=>void act(async()=>start(request!))}>Guardar y reconstruir multivista R09</button>
 <button disabled={busy} onClick={()=>void act(refresh)}>Actualizar cálculos multivista R09</button>
 {pending&&<><p role="status">Inicio multivista pendiente de confirmar; recuperar usa el mismo cuerpo y clave, sin iniciar otra corrida.</p><button disabled={busy||!loaded} onClick={()=>void act(async()=>start(pending.body,true))}>Recuperar inicio multivista R09</button><button disabled={busy} onClick={()=>void act(async()=>{await multiviewPending(null);setPending(null);setLoaded(true)})}>Descartar intento multivista pendiente</button></>}
 {report&&<p role="status">Cálculo multivista {report.id}: {report.status}. {report.error||''}<button disabled={busy} onClick={()=>{setError('');setAttempt(a=>a+1)}}>Retomar consulta multivista R09</button>{running&&<button disabled={busy} onClick={()=>void act(async()=>setReport(await api(`${root}/${id}/cancel`,{})))}>Cancelar cálculo multivista R09</button>}</p>}
 {error&&<p role="alert">{error}</p>}
 {rows.map(row=><div key={row.id}>{row.id} · {row.status} · {row.read_verification==='recomputed'?'Recálculo verificado':row.read_verification==='integrity_only'?'Integridad, sin recálculo':'Sin resultado completo'}
 {['queued','running'].includes(row.status)&&<button disabled={busy} onClick={()=>{setError('');setId(row.id);setReport(row);setAttempt(a=>a+1)}}>Seguir cálculo multivista {row.id}</button>}
 {row.status==='complete'&&<><button disabled={busy} onClick={()=>void act(async()=>{const selected=context.current;const result=await api(`${root}/${row.id}/artifacts/result.json`);if(!mounted.current)return;if(context.current!==selected){setError('Apertura descartada: las entradas cambiaron mientras se descargaba el cálculo. Abrir nuevamente para reemplazarlas explícitamente.');return}onOpen(result)})}>Abrir cálculo multivista {row.id}</button>
 <button disabled={busy||!!pending||!!running} onClick={()=>void act(async()=>start(await api(`${root}/${row.id}/artifacts/request.json`)))}>Repetir cálculo multivista {row.id}</button>
 <button disabled={busy} onClick={()=>void act(async()=>{const verified=await api(`${root}/${row.id}/verification?recompute=true`);setRows(current=>current.map(r=>r.id===row.id?{...r,...verified}:r))})}>Verificar recálculo multivista {row.id}</button>
 {['request.json','result.json','manifest.json'].map(name=><a key={name} download href={`/api/${root}/${row.id}/artifacts/${name}`}>{name} </a>)}</>}
 </div>)}
 <p>Reabrir comprueba integridad y vínculo de entradas; no recalcula. Verificar recálculo es explícito y requiere implementación/entorno coincidentes. Eso no verifica cámaras, calibración ni profundidad físicas.</p>
 </section>;
}
