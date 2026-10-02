import {useEffect,useState} from 'react';
type Data=Record<string,any>;
export function RopeFlowBenchmark({api,revisions}:{api:any,revisions:Data[]}){
 const [flows,setFlows]=useState<Data[]>([]),[runs,setRuns]=useState<Data[]>([]);
 const [reference,setReference]=useState(''),[flow,setFlow]=useState('');
 const [a,setA]=useState(''),[b,setB]=useState('');
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[result,setResult]=useState<Data|null>(null);
 const refresh=async()=>{const [f,r]=await Promise.all([api('research/r08/flow'),api('research/r08/flow-benchmarks')]);setFlows(f);setRuns(r);};
 useEffect(()=>{let active=true;void Promise.all([api('research/r08/flow'),api('research/r08/flow-benchmarks')]).then(([f,r])=>{if(active){setFlows(f);setRuns(r);}}).catch(e=>{if(active)setError(String(e));});return()=>{active=false;};},[api]);
 const act=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');try{await fn();}catch(e){setError(String(e));}finally{setBusy(false);}};
 const valid=(s:string)=>s===''||/^\d+$/.test(s)&&Number.isSafeInteger(Number(s))&&Number(s)<=4095;
 const mappingValid=valid(a)&&valid(b)&&(a!==''||b!=='')&&(a===''||b===''||Number(a)!==Number(b));
 const start=async()=>{
  const endpoint_seeds:Data={};if(a!=='')endpoint_seeds.a=Number(a);if(b!=='')endpoint_seeds.b=Number(b);
  const saved=await api('research/r08/flow-benchmarks',{reference_id:reference,flow_id:flow,endpoint_seeds});
  setResult(await api(`research/r08/flow-benchmarks/${saved.id}/artifacts/result.json`));await refresh();
 };
 const fmt=(v:any)=>v==null?'sin soporte':Number(v).toFixed(3);
 return <section aria-label="Benchmark temporal de extremos R08"><h3>Evaluar tracking de extremos R08</h3>
 <p>Elegí una revisión manual y una corrida del mismo video. Declarás qué índice de semilla representa cada extremo; dejar vacío excluye esa etiqueta. El frame inicial no cuenta como predicción.</p>
 {error&&<p role="alert">{error}</p>}
 <button disabled={busy} onClick={()=>void act(refresh)}>Actualizar fuentes del benchmark R08</button>
 <label>Referencia temporal R08<select disabled={busy} value={reference} onChange={e=>setReference(e.target.value)}><option value="">Elegir revisión</option>{revisions.map(r=><option key={r.id} value={r.id}>{r.id}</option>)}</select></label>
 <label>Corrida temporal R08<select disabled={busy} value={flow} onChange={e=>{setFlow(e.target.value);setA('');setB('');}}><option value="">Elegir corrida</option>{flows.map(r=><option key={r.id} value={r.id}>{r.id} · {r.read_verification}</option>)}</select></label>
 <label>Semilla para extremo a R08<input disabled={busy} type="text" inputMode="numeric" value={a} onChange={e=>setA(e.target.value)}/></label>
 <label>Semilla para extremo b R08<input disabled={busy} type="text" inputMode="numeric" value={b} onChange={e=>setB(e.target.value)}/></label>
 <button disabled={busy||!reference||!flow||!mappingValid} onClick={()=>void act(start)}>Evaluar extremos R08</button>
 {result&&<div aria-label="Resultado de benchmark R08"><p>Soporte: {result.coverage.supported_endpoints}/{result.coverage.eligible_endpoints} extremos elegibles; sin candidato: {result.coverage.unsupported_eligible_endpoints}.</p>
 <p>Excluidos: fuera de ventana {result.coverage.outside_window_endpoints}; entrada de semillas {result.coverage.seed_input_endpoints}; etiqueta no seleccionada {result.coverage.unselected_label_endpoints}.</p>
 <p>Error sobre soporte: media {fmt(result.summary.mean_error_distance_px_on_supported)} px; máximo {fmt(result.summary.max_error_distance_px_on_supported)} px.</p>
 <p>Esto evalúa puntos sobre imágenes observadas, no forecasting ni identidad física. La calidad de la referencia manual requiere revisión humana.</p>
 <details><summary>Entradas, errores y causas congeladas R08</summary><pre>{JSON.stringify(result,null,2)}</pre></details></div>}
 {runs.map(r=><div key={r.id}>{r.id} · {r.read_verification==='recomputed'?'Métrica recalculada sobre entradas congeladas':'Histórico: sólo integridad, sin recálculo actual'}
 <button disabled={busy} onClick={()=>void act(async()=>setResult(await api(`research/r08/flow-benchmarks/${r.id}/artifacts/result.json`)))}>Ver benchmark R08</button>
 {['request.json','result.json','manifest.json'].map(n=><a key={n} href={`/api/research/r08/flow-benchmarks/${r.id}/artifacts/${n}`} download>{n} </a>)}</div>)}
 </section>;
}
