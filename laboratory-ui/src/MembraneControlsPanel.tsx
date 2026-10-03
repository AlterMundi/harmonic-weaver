import {useEffect,useState} from 'react';
type Data=Record<string,any>;
export function MembraneControlsPanel({api}:Data){
 const [text,setText]=useState(''),[jobs,setJobs]=useState<Data[]>([]),[result,setResult]=useState<Data|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 useEffect(()=>{let live=true;void api('research/r07-controls/configuration',{}).then((v:Data)=>{if(live)setText(JSON.stringify(v,null,2));}).catch((e:any)=>{if(live)setError(String(e));});const poll=async()=>{try{const rows=await api('research/r07-controls');if(live)setJobs(rows);}catch(e){if(live)setError(String(e));}};void poll();const timer=setInterval(poll,1000);return()=>{live=false;clearInterval(timer);};},[api]);
 const act=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');try{await fn();}catch(e){setError(String(e));}finally{setBusy(false);}};
 const active=busy||jobs.some(j=>j.worker_active||['queued','running'].includes(j.status));
 return <section><h2>R07 · Controles transientes</h2><p>Impulso held, pulso, suma de componentes y ruido con semilla. Mismo medio y estado cero; dosis digitales diferentes, sin normalización automática.</p>{error&&<p role="alert">{error}</p>}
 <label>Preset portable de controles R07<textarea rows={18} value={text} onChange={e=>setText(e.target.value)}/></label>
 <button disabled={busy} onClick={()=>void act(async()=>setText(JSON.stringify(await api('research/r07-controls/configuration',JSON.parse(text)),null,2)))}>Validar preset de controles R07</button>
 <button disabled={active} onClick={()=>void act(async()=>{const c=await api('research/r07-controls/configuration',JSON.parse(text));await api('research/r07-controls',c.settings);})}>Calcular controles R07</button>
 {jobs.map(j=><div key={j.id}>{j.id} · {j.status}{['queued','running'].includes(j.status)&&<button onClick={()=>void act(async()=>{await api(`research/r07-controls/${j.id}/cancel`,{});})}>Cancelar controles R07</button>}{j.status==='complete'&&<><button disabled={busy} onClick={()=>void act(async()=>setResult(await api(`research/r07-controls/${j.id}/artifacts/result.json`)))}>Ver controles R07</button>{['request.json','result.json','manifest.json'].map(n=><a key={n} href={`/api/research/r07-controls/${j.id}/artifacts/${n}`} download>{n} </a>)}</>}</div>)}
 {result&&<><table><thead><tr><th>Entrada</th><th>Dosis Σx²</th><th>Peak entrada</th><th>RMS por punto</th><th>Energía modal proxy final</th></tr></thead><tbody>{Object.entries(result.conditions).map(([name,r]:[string,any])=><tr key={name}><td>{name}</td><td>{r.input_sum_squares}</td><td>{r.input_peak_abs}</td><td>{r.field.rms.join(', ')}</td><td>{r.final_modal_energy_proxy}</td></tr>)}</tbody></table><details><summary>Configuración y límites congelados del banco</summary><pre>{JSON.stringify(result,null,2)}</pre></details></>}
 </section>;
}
