import {useEffect,useState} from 'react';
export function ExperienceSourcesPanel({api,onSaved}:{api:any,onSaved:()=>Promise<void>}){
 const key='weaver.r10.r05-protocol.pending.v1';
 const [jobs,setJobs]=useState<any[]>([]),[job,setJob]=useState(''),[arm,setArm]=useState('single'),[label,setLabel]=useState('stimulus-1');
 const [text,setText]=useState(JSON.stringify({config:{},participant_slot:'',role:'observer',order_index:0,stimuli:[]},null,2));
 const [preview,setPreview]=useState<any>(null),[selection,setSelection]=useState<any>(null),[pending,setPending]=useState<any>(null),[saved,setSaved]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
 useEffect(()=>{try{const raw=sessionStorage.getItem(key);if(!raw)return;if(raw.length>4*1024*1024)throw Error('oversize');const p=JSON.parse(raw);if(!p.stimuli||!p.expected_sources||!/^[a-f0-9]{32}$/.test(p.idempotency_key))throw Error('invalid');setPending(p);}catch{sessionStorage.removeItem(key);}},[]);
 const act=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');try{await fn();}catch(e){setError(String(e));}finally{setBusy(false);}};
 const paired=jobs.find(r=>r.id===job)?.kind==='mechanism_comparison';
 const save=async()=>{const body=pending||{...selection,expected_sources:preview.sources,idempotency_key:crypto.randomUUID().replaceAll('-','')};sessionStorage.setItem(key,JSON.stringify(body));setPending(body);let receipt:any;try{receipt=await api('research/r10/r05-protocols',body);}catch(e){const status=(e as any)?.status;if(status>=400&&status<500){sessionStorage.removeItem(key);setPending(null);setPreview(null);}throw e;}sessionStorage.removeItem(key);setPending(null);setSaved(receipt.id);await onSaved();};
 return <section aria-label="Estímulos R05 para R10"><h3>Protocolo con estímulos R05 verificados</h3><p>Selecciona corridas completas y conserva sus hashes de PCM/video. Preparar no publica ni reproduce; guardar requiere las mismas fuentes inspeccionadas.</p>
 <button disabled={busy} onClick={()=>void act(async()=>setJobs((await api('research/r05')).filter((r:any)=>r.status==='complete')))}>Actualizar estímulos R05 para R10</button>
 <label>Corrida R05 para R10<select disabled={busy} value={job} onChange={e=>{setJob(e.target.value);setArm(jobs.find(r=>r.id===e.target.value)?.kind==='mechanism_comparison'?'excited':'single');}}><option value="">Elegir corrida</option>{jobs.map(r=><option key={r.id} value={r.id}>{r.id} · {r.kind||'single'}</option>)}</select></label>
 <label>Brazo R05 para R10<select disabled={busy} value={arm} onChange={e=>setArm(e.target.value)}>{(paired?['excited','mapped']:['single']).map(a=><option key={a}>{a}</option>)}</select></label>
 <label>Etiqueta estímulo R10<input disabled={busy} value={label} onChange={e=>setLabel(e.target.value)}/></label>
 <button disabled={busy||!job||!label} onClick={()=>void act(async()=>{const p=JSON.parse(text);setText(JSON.stringify({...p,stimuli:[...p.stimuli,{id:label,r05_id:job,arm}]},null,2));setPreview(null);})}>Añadir estímulo R05 al protocolo</button>
 <label>Selección R05 JSON R10<textarea disabled={busy} rows={12} value={text} onChange={e=>{setText(e.target.value);setPreview(null);}}/></label>
 <button disabled={busy} onClick={()=>void act(async()=>{setPreview(null);const p=JSON.parse(text);const r=await api('research/r10/r05-preview',p);setSelection(p);setPreview(r);})}>Preparar estímulos resueltos R10</button>
 <button disabled={busy||!!pending||!preview} onClick={()=>void act(save)}>Guardar protocolo R05 R10</button>
 {pending&&<p role="status">Protocolo R05 pendiente. <button disabled={busy} onClick={()=>void act(save)}>Recuperar protocolo R05 R10</button></p>}{error&&<p role="alert">{error}</p>}
 {preview&&<><p>{preview.sources.length} estímulos resueltos · {preview.trials.length} ensayos planificados. Nivel y sincronización físicos no medidos.</p><pre>{JSON.stringify(preview,null,2)}</pre></>}
 {saved&&<p>Protocolo R05 guardado: {saved}. Reabrir en inventario R10.</p>}
 </section>;
}
