import {useEffect,useState} from 'react';
type Data=Record<string,any>;
export function RopeFlowBenchmark({api,revisions}:{api:any,revisions:Data[]}){
 const [flows,setFlows]=useState<Data[]>([]),[runs,setRuns]=useState<Data[]>([]);
 const [reference,setReference]=useState(''),[flow,setFlow]=useState('');
 const [a,setA]=useState(''),[b,setB]=useState('');
 const [preview,setPreview]=useState<Data|null>(null),[previewError,setPreviewError]=useState('');
 useEffect(()=>{
  let active=true;setPreview(null);setPreviewError('');
  if(reference&&flow)void Promise.all([api(`research/r08/${reference}/artifacts/annotation.json`),api(`research/r08/flow/${flow}/artifacts/request.json`)]).then(([r,f])=>{
   if(active)setPreview({reference:r,flow:f});
  }).catch(e=>{if(active)setPreviewError(String(e));});
  return()=>{active=false;};
 },[api,reference,flow]);
 const compatible=preview&&preview.reference.media_sha256===preview.flow.media_sha256&&preview.reference.width_px===preview.flow.width_px&&preview.reference.height_px===preview.flow.height_px;
 const initialReference=preview?.reference.frames.find((f:Data)=>f.frame_index===preview.flow.start_frame_index);

 const receiptKey='weaver.r08.endpoint-benchmark.pending.v1';
 const [pending,setPending]=useState<Data|null>(null);
 useEffect(()=>{try{const raw=sessionStorage.getItem(receiptKey);if(!raw)return;if(raw.length>4096)throw Error('oversize');const p=JSON.parse(raw);if(!/^[a-f0-9]{32}$/.test(p.idempotency_key)||! /^[a-f0-9]{32}$/.test(p.reference_id)||! /^[a-f0-9]{32}$/.test(p.flow_id)||!p.endpoint_seeds||Object.keys(p.endpoint_seeds).some(k=>!['a','b'].includes(k)||!Number.isInteger(p.endpoint_seeds[k])))throw Error('invalid');setPending(p);}catch{sessionStorage.removeItem(receiptKey);}},[]);
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[result,setResult]=useState<Data|null>(null);
 const refresh=async()=>{const [f,r]=await Promise.all([api('research/r08/flow'),api('research/r08/flow-benchmarks')]);setFlows(f);setRuns(r);};
 useEffect(()=>{let active=true;void Promise.all([api('research/r08/flow'),api('research/r08/flow-benchmarks')]).then(([f,r])=>{if(active){setFlows(f);setRuns(r);}}).catch(e=>{if(active)setError(String(e));});return()=>{active=false;};},[api]);
 const act=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');try{await fn();}catch(e){setError(String(e));}finally{setBusy(false);}};
 const valid=(s:string)=>s===''||/^\d+$/.test(s)&&Number.isSafeInteger(Number(s))&&Number(s)<=4095;
 const seedExists=(s:string)=>s===''||preview&&Number(s)<preview.flow.seeds.length;
 const mappingValid=valid(a)&&valid(b)&&seedExists(a)&&seedExists(b)&&(a!==''||b!=='')&&(a===''||b===''||Number(a)!==Number(b));
 const start=async()=>{
  const endpoint_seeds:Data={};if(a!=='')endpoint_seeds.a=Number(a);if(b!=='')endpoint_seeds.b=Number(b);
  const body=pending||{reference_id:reference,flow_id:flow,endpoint_seeds,idempotency_key:crypto.randomUUID().replaceAll('-','')};
  sessionStorage.setItem(receiptKey,JSON.stringify(body));setPending(body);
  try{
   const saved=await api('research/r08/flow-benchmarks',body);
   setResult(await api(`research/r08/flow-benchmarks/${saved.id}/artifacts/result.json`));
   sessionStorage.removeItem(receiptKey);setPending(null);await refresh();
  }catch(e){const status=(e as any)?.status;if(status>=400&&status<500){sessionStorage.removeItem(receiptKey);setPending(null);}throw e;}
 };
 const fmt=(v:any)=>v==null?'sin soporte':Number(v).toFixed(3);
 return <section aria-label="Benchmark temporal de extremos R08"><h3>Evaluar tracking de extremos R08</h3>
 <p>Elegí una revisión manual y una corrida del mismo video. Declarás qué índice de semilla representa cada extremo; dejar vacío excluye esa etiqueta. El frame inicial no cuenta como predicción.</p>
 {error&&<p role="alert">{error}</p>}
 <button disabled={busy} onClick={()=>void act(refresh)}>Actualizar fuentes del benchmark R08</button>
 <label>Referencia temporal R08<select disabled={busy||!!pending} value={reference} onChange={e=>setReference(e.target.value)}><option value="">Elegir revisión</option>{revisions.map(r=><option key={r.id} value={r.id}>{r.id}</option>)}</select></label>
 <label>Corrida temporal R08<select disabled={busy||!!pending} value={flow} onChange={e=>{setFlow(e.target.value);setA('');setB('');}}><option value="">Elegir corrida</option>{flows.map(r=><option key={r.id} value={r.id}>{r.id} · {r.read_verification}</option>)}</select></label>
 {previewError&&<p role="alert">No se pudo cargar el contexto del mapeo: {previewError}</p>}
 {preview&&<div aria-label="Contexto del mapeo temporal R08">
 <p>Ventana: frame {preview.flow.start_frame_index} a {preview.flow.start_frame_index+preview.flow.frame_times_s.length-1}; {preview.flow.frame_times_s[0]}–{preview.flow.frame_times_s.at(-1)} s. Semillas: {preview.flow.seeds.length}.</p>
 {!compatible?<p role="alert">Referencia y corrida tienen distinta fuente o dimensiones. Elegí entradas compatibles.</p>:<>
 <svg aria-label="Semillas y extremos en frame inicial R08" viewBox={`0 0 ${preview.flow.width_px} ${preview.flow.height_px}`} style={{width:'100%',maxWidth:480,background:'#20232a'}}>
 {preview.flow.seeds.map((p:Data,i:number)=><g key={i}><circle cx={p.x*preview.flow.width_px} cy={p.y*preview.flow.height_px} r={preview.flow.width_px*.012} fill="none" stroke="#66ccff"/><text x={p.x*preview.flow.width_px} y={p.y*preview.flow.height_px} fill="#66ccff" fontSize={preview.flow.width_px*.04}>{i}</text></g>)}
 {Object.entries(initialReference?.endpoints||{}).map(([label,p]:[string,any])=><g key={label}><circle cx={p.x*preview.flow.width_px} cy={p.y*preview.flow.height_px} r={preview.flow.width_px*.006} fill="#ffcc66"/><text x={p.x*preview.flow.width_px} y={p.y*preview.flow.height_px-preview.flow.width_px*.04} fill="#ffcc66" fontSize={preview.flow.width_px*.04}>{label}</text></g>)}
 </svg>
 <p>Azul: índices de semillas; amarillo: etiquetas manuales en el mismo frame inicial. Esquema en plano de imagen, sin video. {initialReference?'':'La referencia no anota el frame inicial; no se trasladan extremos de otro tiempo.'}</p>
 <table><thead><tr><th>Semilla</th><th>x normalizada</th><th>y normalizada</th></tr></thead><tbody>{preview.flow.seeds.map((p:Data,i:number)=><tr key={i}><td>{i}</td><td>{p.x}</td><td>{p.y}</td></tr>)}</tbody></table>
 </>}
 </div>}
 <label>Semilla para extremo a R08<input disabled={busy||!!pending} type="text" inputMode="numeric" value={a} onChange={e=>setA(e.target.value)}/></label>
 <label>Semilla para extremo b R08<input disabled={busy||!!pending} type="text" inputMode="numeric" value={b} onChange={e=>setB(e.target.value)}/></label>
 <button disabled={busy||!!pending||!compatible||!mappingValid} onClick={()=>void act(start)}>Evaluar extremos R08</button>
 {pending&&<p role="status">Comparación pendiente de confirmar: {pending.reference_id} / {pending.flow_id}. <button disabled={busy} onClick={()=>void act(start)}>Recuperar comparación pendiente R08</button></p>}
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
