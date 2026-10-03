import {useEffect,useState} from 'react';
type Data=Record<string,any>;
export function MembraneTransferPanel({api}:Data){
 const [text,setText]=useState(''),[jobs,setJobs]=useState<Data[]>([]),[result,setResult]=useState<Data|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const refresh=async()=>setJobs(await api('research/r07-transfer'));
 useEffect(()=>{let live=true;void Promise.all([api('research/r07-transfer/configuration',{}),api('research/r07-transfer')]).then(([c,j]:Data[])=>{if(live){setText(JSON.stringify(c,null,2));setJobs(j as any);}}).catch(e=>{if(live)setError(String(e));});return()=>{live=false;};},[api]);
 const act=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');try{await fn();}catch(e){setError(String(e));}finally{setBusy(false);}};
 return <section><h2>R07 · Transferencia y resolución modal</h2><p>Respuesta estacionaria de forcing unitario muestreado. Mismo medio/puntos/frecuencias; diferencias crudas entre resoluciones anidadas. No demuestra convergencia física.</p>{error&&<p role="alert">{error}</p>}
 <label>Configuración portable de transferencia R07<textarea rows={18} value={text} onChange={e=>setText(e.target.value)}/></label>
 <button disabled={busy} onClick={()=>void act(async()=>{setText(JSON.stringify(await api('research/r07-transfer/configuration',JSON.parse(text)),null,2));})}>Validar preset de transferencia R07</button>
 <button disabled={busy} onClick={()=>void act(async()=>{const c=await api('research/r07-transfer/configuration',JSON.parse(text));await api('research/r07-transfer',c.settings);await refresh();})}>Calcular transferencia R07</button>
 {jobs.map(j=><div key={j.id}>{j.id}<button disabled={busy} onClick={()=>void act(async()=>setResult(await api(`research/r07-transfer/${j.id}/artifacts/result.json`)))}>Ver transferencia R07</button>{['request.json','result.json','manifest.json'].map(n=><a key={n} href={`/api/research/r07-transfer/${j.id}/artifacts/${n}`} download>{n} </a>)}</div>)}
 {result&&<><table><thead><tr><th>Modos</th><th>Frecuencia Hz</th><th>Punto</th><th>Magnitud</th><th>Δ compleja</th><th>Δ fase rad</th></tr></thead><tbody>{result.conditions.flatMap((r:Data,ri:number)=>r.magnitude.flatMap((row:number[],fi:number)=>row.map((v,pi)=><tr key={`${ri}.${fi}.${pi}`}><td>{r.resolution.modes_x}×{r.resolution.modes_y}</td><td>{result.request.frequencies_hz[fi]}</td><td>{result.request.x[pi]}, {result.request.y[pi]}</td><td>{v}</td><td>{r.difference_magnitude_vs_previous?.[fi]?.[pi]??'sin previo'}</td><td>{r.phase_difference_rad_vs_previous?.[fi]?.[pi]??'no definida'}</td></tr>)))}</tbody></table><details><summary>Resultado y configuración congelados</summary><pre>{JSON.stringify(result,null,2)}</pre></details></>}
 </section>;
}
