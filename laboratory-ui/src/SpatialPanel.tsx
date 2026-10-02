import {useState} from 'react';
type Data=Record<string,any>;
const defaultClock={source_clock:'pts',common_clock:'session',offset_s:0,rate:1,uncertainty_s:0,method:'declared_assumption',evidence_id:null};
export function SpatialPanel({api}:{api:any}){
 const [text,setText]=useState('[]'),[person,setPerson]=useState(''),[clock,setClock]=useState(JSON.stringify(defaultClock,null,2));
 const [mode,setMode]=useState('convert'),[busy,setBusy]=useState(false),[error,setError]=useState(''),[result,setResult]=useState<Data|null>(null);
 const act=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');try{await fn();}catch(e){setError(String(e));}finally{setBusy(false);}};
 const exportResult=()=>{const blob=new Blob([JSON.stringify(result,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='r09-spatial-result.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
 return <section aria-label="Observaciones espaciales R09"><h2>R09 · Observaciones y relojes</h2>
 <p>Importación explícita para investigación. La conversión conserva el plano de imagen y sus unidades; validar un contrato no verifica profundidad, calibración ni sincronización.</p>
 <label>Modalidad R09<select disabled={busy} value={mode} onChange={e=>{setMode(e.target.value);setResult(null);}}><option value="convert">Convertir MotionFrames 2D</option><option value="validate">Validar Stream espacial</option></select></label>
 <label>Importar JSON local R09<input disabled={busy} type="file" accept="application/json,.json" onChange={e=>{const file=e.target.files?.[0];if(file)void act(async()=>{if(file.size>32*1024*1024)throw Error('JSON supera 32 MiB');const raw=await file.text();JSON.parse(raw);setText(raw);setResult(null);});e.target.value='';}}/></label>
 <label>Observaciones JSON R09<textarea disabled={busy} rows={10} value={text} onChange={e=>{setText(e.target.value);setResult(null);}}/></label>
 {mode==='convert'&&<><label>Slot explícito R09<input disabled={busy} value={person} onChange={e=>{setPerson(e.target.value);setResult(null);}}/></label>
 <label>Mapeo de reloj JSON R09<textarea disabled={busy} rows={8} value={clock} onChange={e=>{setClock(e.target.value);setResult(null);}}/></label>
 <p>t común = offset + rate × t fuente. El reloj inicial es una suposición editable, no una medición; incertidumbre cero no acredita sincronización.</p></>}
 {error&&<p role="alert">{error}</p>}
 <button disabled={busy||mode==='convert'&&!person} onClick={()=>void act(async()=>{setResult(null);if(text.length>32*1024*1024)throw Error('JSON supera límite');const observations=JSON.parse(text);setResult(await api(`research/r09/${mode}`,mode==='convert'?{frames:observations,person_id:person,clock:JSON.parse(clock)}:observations));})}>Procesar observaciones R09</button>
 {result&&<div><p>Contrato validado: {result.stream.provider} · {result.stream.dimensions}D · {result.stream.units} · slot {result.stream.subject_slot}.</p>
 {result.coverage&&<p>Cobertura R09: observados {result.coverage.observed}; sostenidos {result.coverage.held}; inferidos {result.coverage.inferred}; faltantes {result.coverage.missing}.</p>}
 <button onClick={exportResult}>Exportar resultado R09</button><details><summary>Resultado espacial R09</summary><pre>{JSON.stringify(result,null,2)}</pre></details></div>}
 </section>;
}
