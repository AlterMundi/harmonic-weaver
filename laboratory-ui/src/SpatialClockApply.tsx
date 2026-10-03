import {useState} from 'react';
export function SpatialClockApply({api,runs}:{api:any,runs:any[]}){
 const [id,setId]=useState(''),[text,setText]=useState('{}'),[extrapolate,setExtrapolate]=useState(false),[result,setResult]=useState<any>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 return <section aria-label="Aplicar reloj R09"><h4>Aplicar ajuste guardado a observaciones</h4><p>Reemplaza sólo el reloj del JSON declarado. Conserva timestamps, coordenadas y estados; no modifica la fuente ni el instrumento en vivo. El nombre del reloj de origen debe coincidir.</p>
 <label>Ajuste guardado R09<select disabled={busy} value={id} onChange={e=>{setId(e.target.value);setResult(null);}}><option value="">Elegir ajuste</option>{runs.map(r=><option key={r.id} value={r.id}>{r.id} · {r.read_verification}</option>)}</select></label>
 <label>Stream para aplicar reloj R09<textarea disabled={busy} rows={8} value={text} onChange={e=>{setText(e.target.value);setResult(null);}}/></label>
 <label>Permitir extrapolación reloj R09<input disabled={busy} type="checkbox" checked={extrapolate} onChange={e=>{setExtrapolate(e.target.checked);setResult(null);}}/></label>
 <button disabled={busy||!id} onClick={()=>void(async()=>{setBusy(true);setError('');setResult(null);try{setResult(await api('research/r09/apply-clock',{fit_id:id,stream:JSON.parse(text),allow_extrapolation:extrapolate}));}catch(e){setError(String(e));}finally{setBusy(false);}})()}>Aplicar reloj a stream R09</button>
 {error&&<p role="alert">{error}</p>}{result&&<><p>Reloj aplicado: {result.clock_fit_provenance.id} · frames extrapolados: {result.extrapolated_frame_indices.length}.</p><pre>{JSON.stringify(result,null,2)}</pre><button onClick={()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='r09-clock-applied.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}}>Exportar stream con reloj R09</button></>}
 </section>;
}
