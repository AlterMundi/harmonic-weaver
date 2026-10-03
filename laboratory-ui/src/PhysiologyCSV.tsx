import {useEffect,useState,useRef} from 'react';
type Data=Record<string,any>;
const initial={delimiter:',',skip_rows:0,index_column:'index',time_column:'time_s',time_units:'seconds',channel_columns:{},missing_tokens:[''],missing_cause:'declared_csv_missing'};
const metadataKeys=['provider','source_id','subject_slot','task','constraints','clock','channels','trials','max_gap_s','common_channel_ids','evaluation_binding'];
export function PhysiologyCSV({api,protocol,onApply}:{api:any,protocol:Data|null,onApply:(r:Data)=>void}){
 const [csv,setCSV]=useState(''),[mapping,setMapping]=useState(JSON.stringify(initial,null,2)),[preview,setPreview]=useState<Data|null>(null),[frozen,setFrozen]=useState<Data|null>(null),[rows,setRows]=useState<Data[]>([]),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const current=useRef('');current.current=JSON.stringify([protocol,csv,mapping]);
 const act=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');try{await fn()}catch(e){setError(String(e))}finally{setBusy(false)}};
 const refresh=async()=>setRows(await api('research/r12/csv/imports'));
 useEffect(()=>{void refresh().catch(e=>setError(String(e)))},[api]);
 useEffect(()=>{setPreview(null);setFrozen(null)},[protocol,csv,mapping]);
 const download=(value:unknown)=>{const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='r12-csv-mapping.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
 return <details><summary>Importar tabla CSV R12</summary>
 <p>Usa el proveedor, slot, reloj, canales, tarea e intentos del protocolo JSON actual; reemplaza sus muestras por las de la tabla. Declarar primero esos metadatos. La plantilla sigue siendo sintética hasta que declares una importación real. Valores ya en bpm, W o dimensionless según el canal; no convierte amplitudes ni infiere calibración. Datos locales.</p>
 <label>Archivo CSV R12<input type="file" accept=".csv,.tsv,text/csv" disabled={busy} onChange={e=>{const file=e.target.files?.[0];e.target.value='';if(file)void act(async()=>{if(file.size>16*1024*1024)throw Error('Máximo 16 MiB UTF-8');setCSV(new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(await file.arrayBuffer()))})}}/></label>
 <label>Tabla CSV R12<textarea aria-label="Tabla CSV R12" rows={5} value={csv} disabled={busy} onChange={e=>setCSV(e.target.value)}/></label>
 <label>Mapeo CSV R12 JSON<textarea aria-label="Mapeo CSV R12 JSON" rows={8} value={mapping} disabled={busy} onChange={e=>setMapping(e.target.value)}/></label>
 <p>Declarar separador, preámbulo, columnas de índice/tiempo, unidades temporales (seconds/milliseconds/microseconds), channel_columns y tokens faltantes. No genera índices ni rellena gaps. Hasta 20.000 muestras.</p>
 <button disabled={busy} onClick={()=>void act(async()=>download(JSON.parse(mapping)))}>Exportar mapeo CSV R12</button>
 <label>Importar mapeo CSV R12<input type="file" accept=".json,application/json" disabled={busy} onChange={e=>{const file=e.target.files?.[0];e.target.value='';if(file)void act(async()=>{if(file.size>65536)throw Error('Máximo 64 KiB');setMapping(JSON.stringify(JSON.parse(await file.text()),null,2))})}}/></label>
 <p>Mapeo portable no incluye cuerpo, reloj, calibración, ventanas ni datos de la tabla.</p>
 <button disabled={busy||!protocol||!csv} onClick={()=>void act(async()=>{setPreview(null);setFrozen(null);const context=current.current;const metadata=Object.fromEntries(metadataKeys.filter(k=>protocol![k]!==undefined).map(k=>[k,protocol![k]]));const body={csv_text:csv,mapping:JSON.parse(mapping),metadata};const value=await api('research/r12/csv/inspect',body);if(context!==current.current)throw Error('El contexto CSV cambió durante la inspección; inspeccionar de nuevo');setFrozen(body);setPreview(value)})}>Inspeccionar CSV R12</button>
 {preview&&<><p>CSV R12: {preview.request.samples.length} muestras · columnas ignoradas: {preview.import_provenance.ignored_columns.join(', ')||'ninguna'} · proveedor {preview.request.provider}</p>
 <button disabled={busy||!frozen} onClick={()=>void act(async()=>{await api('research/r12/csv/imports',frozen);await refresh()})}>Guardar original y conversión CSV R12</button>
 <button disabled={busy} onClick={()=>void act(async()=>{const context=current.current;await api('research/r12/csv/imports',frozen);await refresh();if(context!==current.current)throw Error('Import guardado; contexto actual cambió, recuperar desde la lista para aplicarlo');onApply(preview.request)})}>Guardar y usar conversión CSV en análisis R12</button></>}
 <button disabled={busy} onClick={()=>void act(refresh)}>Actualizar imports CSV R12</button>
 {rows.map(row=><div key={row.id}>{row.id} · {row.samples} muestras · {row.read_verification}<button disabled={busy} onClick={()=>void act(async()=>{const result=await api(`research/r12/csv/imports/${row.id}/artifacts/result.json`);onApply(result.request)})}>Usar import CSV R12 {row.id}</button>{['source.csv','request.json','result.json','manifest.json'].map(name=><a key={name} download href={`/api/research/r12/csv/imports/${row.id}/artifacts/${name}`}>{name} </a>)}</div>)}
 {error&&<p role="alert">{error}</p>}
 </details>;
}
