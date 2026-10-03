import {useEffect,useState} from 'react';
type Data=Record<string,any>;
export function MembraneReadoutPanel({api}:Data){
 const [preset,setPreset]=useState(''),[cases,setCases]=useState('[]'),[projections,setProjections]=useState<Data[]>([]),[jobs,setJobs]=useState<Data[]>([]);
 const [projection,setProjection]=useState(''),[role,setRole]=useState('train'),[recording,setRecording]=useState(''),[group,setGroup]=useState(''),[targets,setTargets]=useState('');
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[result,setResult]=useState<Data|null>(null),[verification,setVerification]=useState<Data|null>(null),[resultId,setResultId]=useState('');
 const refresh=async()=>{const [p,j]=await Promise.all([api('research/r07'),api('research/r07-readout')]);setProjections(p.filter((r:Data)=>r.status==='complete'));setJobs(j);};
 useEffect(()=>{let live=true;void Promise.all([api('research/r07-readout/configuration',{}),api('research/r07'),api('research/r07-readout')]).then(([c,p,j])=>{if(live){setPreset(JSON.stringify(c,null,2));setProjections(p.filter((r:Data)=>r.status==='complete'));setJobs(j);}}).catch(e=>{if(live)setError(String(e));});return()=>{live=false;};},[api]);
 const act=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');try{await fn();}catch(e){setError(String(e));}finally{setBusy(false);}};
 const exportPreset=()=>{const u=URL.createObjectURL(new Blob([preset],{type:'application/json'}));const a=document.createElement('a');a.href=u;a.download='r07-readout-preset.json';a.click();URL.revokeObjectURL(u);};
 return <section><h2>R07 · Recuperación de atributos reservados</h2>
 <p>Lee figuras RMS derivadas del PCM, con entrenamiento y prueba separados. Compara campo completo, forma normalizada y magnitud, media de entrenamiento y etiquetas barajadas. Las etiquetas no modifican la figura.</p>
 {error&&<p role="alert">{error}</p>}
 <label>Preset portable de recuperación R07<textarea aria-label="Preset portable de recuperación R07" rows={12} value={preset} onChange={e=>setPreset(e.target.value)}/></label>
 <button disabled={busy} onClick={()=>void act(async()=>setPreset(JSON.stringify(await api('research/r07-readout/configuration',JSON.parse(preset)),null,2)))}>Validar preset de recuperación R07</button>
 <button disabled={busy||!preset} onClick={exportPreset}>Exportar preset de recuperación R07</button>
 <p>El preset contiene atributos/unidades, reserva, ridge, normalización, embargo y semilla. Importalo pegando JSON; no contiene fuentes, personas, calibración ni etiquetas.</p>
 <button disabled={busy} onClick={()=>void act(refresh)}>Actualizar figuras disponibles R07</button>
 <label>Figura para recuperar atributos<select aria-label="Figura para recuperar atributos" value={projection} onChange={e=>setProjection(e.target.value)}><option value="">Elegir figura calculada</option>{projections.map(p=><option key={p.id} value={p.id}>{p.id}</option>)}</select></label>
 <label>Rol del caso R07<select value={role} onChange={e=>setRole(e.target.value)}><option value="train">Entrenamiento</option><option value="test">Prueba reservada</option></select></label>
 <label>Grabación declarada R07<input value={recording} onChange={e=>setRecording(e.target.value)}/></label>
 <label>Grupo corporal declarado R07<input value={group} onChange={e=>setGroup(e.target.value)}/></label>
 <label>Atributos declarados R07<input value={targets} placeholder="Array JSON en el orden del preset" onChange={e=>setTargets(e.target.value)}/></label>
 <button disabled={busy||!projection||!recording||!group||!targets} onClick={()=>void act(async()=>{const rows=JSON.parse(cases);if(!Array.isArray(rows))throw Error('Casos debe ser un array');rows.push({id:`case-${rows.length+1}`,projection_run_id:projection,role,recording_id:recording,subject_group:group,targets:JSON.parse(targets)});setCases(JSON.stringify(rows,null,2));})}>Agregar caso de recuperación R07</button>
 <label>Casos locales de recuperación R07<textarea aria-label="Casos locales de recuperación R07" rows={14} value={cases} onChange={e=>setCases(e.target.value)}/></label>
 <p>Declarar IDs no certifica identidad. Misma toma debe conservar el mismo ID entre renders/presets. Mínimo tres casos de entrenamiento y dos de prueba; mismo medio/grilla. Los datos de esta selección quedan locales en el dataset congelado.</p>
 <button disabled={busy} onClick={()=>void act(async()=>{const c=await api('research/r07-readout/configuration',JSON.parse(preset));await api('research/r07-readout',{...c,cases:JSON.parse(cases)});await refresh();})}>Calcular recuperación R07</button>
 {jobs.map(j=><div key={j.id}>{j.id}<button disabled={busy} onClick={()=>void act(async()=>{setResult(null);setVerification(null);setResultId('');const [r,v]=await Promise.all([api(`research/r07-readout/${j.id}/artifacts/result.json`),api(`research/r07-readout/${j.id}/verification`)]);setResult(r);setVerification(v);setResultId(j.id);})}>Ver recuperación R07</button>{['dataset.json','result.json','manifest.json'].map(n=><a key={n} href={`/api/research/r07-readout/${j.id}/artifacts/${n}`} download>{n} </a>)}</div>)}
 {result&&<><p>Corrida recuperada: {resultId} · {result.common_count} casos comunes</p>{verification&&<p aria-label="Verificación de recuperación R07">{verification.read_verification==='integrity_only'?'Integridad verificada; sin recalcular':'Recalculado numéricamente con código actual'} · código {verification.implementation_matches?'coincidente':'distinto'} · entorno {verification.environment_matches?'coincidente':'distinto'}</p>}
 <button disabled={busy} onClick={()=>void act(async()=>{setVerification(null);setVerification(await api(`research/r07-readout/${resultId}/verification?recompute=true`));})}>Recalcular verificación de recuperación R07</button>
 <table aria-label="Errores de recuperación R07"><thead><tr><th>Lectura</th>{result.attribute_ids.map((id:string,i:number)=><th key={id}>{id} · MSE ({result.attribute_units[i]})²</th>)}</tr></thead><tbody>{Object.entries(result.mean_squared_error).map(([id,values])=><tr key={id}><td>{id}</td>{(values as number[]).map((v,i)=><td key={i}>{v}</td>)}</tr>)}</tbody></table>
 <details><summary>Modelos, casos reservados, predicciones y límites</summary><pre>{JSON.stringify(result,null,2)}</pre></details>
 <p>No demuestra HIT, una identidad natural entre gesto y figura, ni validación perceptual. Ajustar parámetros mirando la prueba convierte la comparación en exploratoria.</p></>}
 </section>;
}
