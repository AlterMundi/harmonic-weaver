import {useEffect,useState} from 'react';
type Data=Record<string,any>;
export function SpatialClockConversion({api,fits}:{api:any,fits:Data[]}){
 const key='weaver.r09.clock-conversion.pending.v1';
 const [conversions,setConversions]=useState<Data[]>([]),[source,setSource]=useState(''),[fit,setFit]=useState(''),[extrapolate,setExtrapolate]=useState(false);
 const [pending,setPending]=useState<Data|null>(null),[saved,setSaved]=useState<Data|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 useEffect(()=>{try{const raw=sessionStorage.getItem(key);if(!raw)return;if(raw.length>4096)throw Error('oversize');const p=JSON.parse(raw);if(![p.conversion_id,p.fit_id,p.idempotency_key].every(v=>typeof v==='string'&&/^[a-f0-9]{32}$/.test(v))||typeof p.allow_extrapolation!=='boolean')throw Error('invalid');setPending(p);}catch{sessionStorage.removeItem(key);}},[]);
 const act=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');try{await fn();}catch(e){setError(String(e));}finally{setBusy(false);}};
 const save=async()=>{const body=pending||{conversion_id:source,fit_id:fit,allow_extrapolation:extrapolate,idempotency_key:crypto.randomUUID().replaceAll('-','')};sessionStorage.setItem(key,JSON.stringify(body));setPending(body);let receipt:Data;try{receipt=await api('research/r09/clock-conversions',body);}catch(e){const status=(e as any)?.status;if(status>=400&&status<500){sessionStorage.removeItem(key);setPending(null);}throw e;}sessionStorage.removeItem(key);setPending(null);setSaved({id:receipt.id,result:await api(`research/r09/conversions/${receipt.id}/artifacts/result.json`)});setConversions(await api('research/r09/conversions'));};
 return <section aria-label="Guardar conversión con reloj R09"><h4>Guardar aplicación desde fuentes verificadas</h4><p>El servidor resuelve ambos IDs y conserva las entradas y hashes para repetir la transformación. No modifica originales ni aplica reloj al instrumento en vivo.</p>
 <button disabled={busy} onClick={()=>void act(async()=>setConversions(await api('research/r09/conversions')))}>Actualizar conversiones para reloj R09</button>
 <label>Conversión original para reloj R09<select disabled={busy} value={source} onChange={e=>setSource(e.target.value)}><option value="">Elegir conversión</option>{conversions.map(r=><option key={r.id} value={r.id}>{r.id} · {r.read_verification}</option>)}</select></label>
 <label>Ajuste para guardar conversión R09<select disabled={busy} value={fit} onChange={e=>setFit(e.target.value)}><option value="">Elegir ajuste</option>{fits.map(r=><option key={r.id} value={r.id}>{r.id} · {r.read_verification}</option>)}</select></label>
 <label>Extrapolar conversión guardada R09<input disabled={busy} type="checkbox" checked={extrapolate} onChange={e=>setExtrapolate(e.target.checked)}/></label>
 <button disabled={busy||!!pending||!source||!fit} onClick={()=>void act(save)}>Guardar conversión con reloj R09</button>
 {pending&&<p role="status">Pedido pendiente: conversión {pending.conversion_id} · ajuste {pending.fit_id}. <button disabled={busy} onClick={()=>void act(save)}>Recuperar conversión con reloj R09</button></p>}
 {error&&<p role="alert">{error}</p>}{saved&&<div><p>Conversión con reloj guardada: {saved.id}.</p><pre>{JSON.stringify(saved.result,null,2)}</pre>{['request.json','result.json','manifest.json'].map(n=><a key={n} href={`/api/research/r09/conversions/${saved.id}/artifacts/${n}`} download>{n} </a>)}</div>}
 </section>;
}
