import {useEffect,useState} from 'react';
type Data=Record<string,any>;
export function RopeFlowPaired({api,benchmarks}:{api:any,benchmarks:Data[]}){
 const [selected,setSelected]=useState<string[]>([]),[runs,setRuns]=useState<Data[]>([]),[result,setResult]=useState<Data|null>(null);
 const [busy,setBusy]=useState(false),[error,setError]=useState('');
 useEffect(()=>{let live=true;void api('research/r08/flow-paired').then((r:Data[])=>{if(live)setRuns(r);}).catch((e:unknown)=>{if(live)setError(String(e));});return()=>{live=false;};},[api]);
 const act=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');try{await fn();}catch(e){setError(String(e));}finally{setBusy(false);}};
 const fmt=(n:any)=>n==null?'sin soporte':Number(n).toFixed(3);
 return <section aria-label="Comparación pareada R08"><h3>Comparar configuraciones sobre soporte común R08</h3>
 <p>Seleccioná entre dos y dieciséis benchmarks con la misma referencia y etiquetas. Conservamos la cobertura individual; el error se compara sólo donde todas las condiciones tienen candidato.</p>
 {error&&<p role="alert">{error}</p>}
 {benchmarks.map(r=><label key={r.id}><input type="checkbox" disabled={busy||selected.length>=16&&!selected.includes(r.id)} checked={selected.includes(r.id)} onChange={e=>setSelected(e.target.checked?[...selected,r.id]:selected.filter(id=>id!==r.id))}/>{r.id}</label>)}
 <button disabled={busy||selected.length<2} onClick={()=>void act(async()=>{
  const conditions=Object.fromEntries(selected.map(id=>[id,id]));
  const saved=await api('research/r08/flow-paired',{conditions});
  setResult(await api(`research/r08/flow-paired/${saved.id}/artifacts/result.json`));
  setRuns(await api('research/r08/flow-paired'));
 })}>Comparar soporte común R08</button>
 {result&&<div><p>Soporte común: {result.common_supported_endpoints}/{result.common_eligible_endpoints} extremos elegibles comunes.</p>
 <table><thead><tr><th>Condición</th><th>Soporte individual / elegibles</th><th>Soporte sobre elegibilidad común</th><th>Error medio común (px)</th><th>Error máximo común (px)</th></tr></thead><tbody>{Object.entries(result.conditions).map(([name,r]:[string,any])=><tr key={name}><td>{name}</td><td>{r.coverage.supported_endpoints} / {r.coverage.eligible_endpoints}</td><td>{r.supported_on_common_eligible}</td><td>{fmt(r.mean_error_px_on_common_support)}</td><td>{fmt(r.max_error_px_on_common_support)}</td></tr>)}</tbody></table>
 {result.paired_differences.map((p:Data)=><p key={`${p.left}-${p.right}`}>{p.right} menos {p.left}: {fmt(p.mean_right_minus_left_error_px)} px sobre {p.endpoints} extremos.</p>)}
 <p>El soporte común puede seleccionar observaciones más fáciles. Estas diferencias no indican significancia estadística ni validación física.</p>
 <details><summary>Banco pareado congelado R08</summary><pre>{JSON.stringify(result,null,2)}</pre></details></div>}
 {runs.map(r=><div key={r.id}>{r.id} · {r.read_verification==='recomputed'?'Banco recalculado':'Histórico: sólo integridad'}<button disabled={busy} onClick={()=>void act(async()=>setResult(await api(`research/r08/flow-paired/${r.id}/artifacts/result.json`)))}>Ver banco pareado R08</button>{['request.json','result.json','manifest.json'].map(n=><a key={n} href={`/api/research/r08/flow-paired/${r.id}/artifacts/${n}`} download>{n} </a>)}</div>)}
 </section>;
}
