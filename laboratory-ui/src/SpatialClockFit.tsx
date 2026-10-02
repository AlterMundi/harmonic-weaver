import {useState} from 'react';
export function SpatialClockFit({api}:{api:any}){
 const [text,setText]=useState(JSON.stringify({source_clock:'camera',common_clock:'session',evidence_id:'',anchor_uncertainty_s:.01,anchors:[]},null,2));
 const [result,setResult]=useState<any>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 return <section aria-label="Ajuste de reloj R09"><h3>Sincronización por marcas pareadas</h3><p>Ingresar al menos tres marcas ordenadas de ambos relojes, incertidumbre de lectura y referencia de evidencia. El ajuste usa todas las marcas; sus residuos no son validación independiente. No aplica el reloj automáticamente.</p>
 <label>Marcas de reloj JSON R09<textarea disabled={busy} rows={10} value={text} onChange={e=>{setText(e.target.value);setResult(null);}}/></label>
 <button disabled={busy} onClick={()=>void(async()=>{setBusy(true);setError('');setResult(null);try{setResult(await api('research/r09/clock-fit',JSON.parse(text)));}catch(e){setError(String(e));}finally{setBusy(false);}})()}>Ajustar reloj R09</button>
 {error&&<p role="alert">{error}</p>}{result&&<><p>Desfase: {result.clock.offset_s} s · tasa: {result.clock.rate} · residuo máximo: {result.max_abs_residual_s} s.</p><p>Intervalo de marcas: {result.source_interval_s.join('–')} s. Fuera del intervalo no se verificó extrapolación. Incertidumbre empírica, sin garantía estadística.</p><pre>{JSON.stringify(result,null,2)}</pre><button onClick={()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(result,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='r09-clock-fit.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}}>Exportar ajuste reloj R09</button></>}
 </section>;
}
