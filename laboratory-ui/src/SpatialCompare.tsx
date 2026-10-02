import {useEffect,useState} from 'react';
type Data=Record<string,any>;
export function SpatialCompare({api}:{api:any}){
 const [reference,setReference]=useState('{}'),[candidate,setCandidate]=useState('{}'),[labels,setLabels]=useState('["joint-0"]');
 const [age,setAge]=useState(.05),[uncertainty,setUncertainty]=useState(.02),[inferred,setInferred]=useState(false),[held,setHeld]=useState(false);
 const [runs,setRuns]=useState<Data[]>([]),[result,setResult]=useState<Data|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 useEffect(()=>{let live=true;void api('research/r09/comparisons').then((r:Data[])=>{if(live)setRuns(r);}).catch((e:unknown)=>{if(live)setError(String(e));});return()=>{live=false;};},[api]);
 const act=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');try{await fn();}catch(e){setError(String(e));}finally{setBusy(false);}};
 return <section aria-label="Comparación espacial R09"><h3>Comparar streams R09</h3>
 <p>Mismos marcos, unidades y reloj común declarados. El candidato sólo puede venir del presente o pasado; no ajustamos escala, rotación ni desfase para mejorar error.</p>
 <label>Stream referencia R09<textarea disabled={busy} rows={8} value={reference} onChange={e=>setReference(e.target.value)}/></label>
 <label>Stream candidato R09<textarea disabled={busy} rows={8} value={candidate} onChange={e=>setCandidate(e.target.value)}/></label>
 <label>Etiquetas de comparación R09<textarea disabled={busy} value={labels} onChange={e=>setLabels(e.target.value)}/></label>
 <label>Edad máxima de candidato R09<input disabled={busy} type="number" min={0} max={10} step={.01} value={age} onChange={e=>setAge(Number(e.target.value))}/></label>
 <label>Incertidumbre combinada máxima R09<input disabled={busy} type="number" min={0} max={10} step={.01} value={uncertainty} onChange={e=>setUncertainty(Number(e.target.value))}/></label>
 <label>Admitir puntos inferidos R09<input disabled={busy} type="checkbox" checked={inferred} onChange={e=>setInferred(e.target.checked)}/></label>
 <label>Admitir puntos sostenidos R09<input disabled={busy} type="checkbox" checked={held} onChange={e=>setHeld(e.target.checked)}/></label>
 {error&&<p role="alert">{error}</p>}
 <button disabled={busy} onClick={()=>void act(async()=>{const saved=await api('research/r09/comparisons',{comparison:{reference:JSON.parse(reference),candidate:JSON.parse(candidate),labels:JSON.parse(labels),max_age_s:age,max_combined_clock_uncertainty_s:uncertainty,allow_inferred:inferred,allow_held:held}});setResult(await api(`research/r09/comparisons/${saved.id}/artifacts/result.json`));setRuns(await api('research/r09/comparisons'));})}>Guardar comparación espacial R09</button>
 {result&&<div><p>Soporte espacial: {result.coverage.supported_points}/{result.coverage.eligible_points} puntos elegibles. Unidad: {result.unit}.</p><p>Error medio sobre soporte: {result.mean_error_on_support??'sin soporte'}; máximo: {result.max_error_on_support??'sin soporte'}.</p><details><summary>Causas y entradas de comparación espacial R09</summary><pre>{JSON.stringify(result,null,2)}</pre></details></div>}
 {runs.map(r=><div key={r.id}>{r.id} · {r.read_verification==='recomputed'?'Comparación recalculada':'Histórico: sólo integridad'}<button disabled={busy} onClick={()=>void act(async()=>setResult(await api(`research/r09/comparisons/${r.id}/artifacts/result.json`)))}>Abrir comparación espacial R09</button>{['request.json','result.json','manifest.json'].map(n=><a key={n} href={`/api/research/r09/comparisons/${r.id}/artifacts/${n}`} download>{n} </a>)}</div>)}
 </section>;
}
