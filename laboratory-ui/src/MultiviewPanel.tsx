import {useState} from 'react';
import {MultiviewRuns} from './MultiviewRuns';
import {SpatialView} from './SpatialView';
type Data=Record<string,any>;
const defaults={max_time_difference_s:.01,max_clock_uncertainty_s:.01,min_ray_angle_deg:1,max_reprojection_error_px:2};
export function MultiviewPanel({api,onStream}:{api:any,onStream:(stream:Data)=>void}){
 const [text,setText]=useState('{}'),[result,setResult]=useState<Data|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 let request:Data|null=null;try{request=JSON.parse(text);if(!request||Array.isArray(request)||typeof request!=='object')request=null}catch{}
 const settings={...defaults,...request?.settings};
 const edit=(value:string)=>{setText(value);setResult(null);setError('')};
 const act=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');try{await fn()}catch(e){setError(String(e))}finally{setBusy(false)}};
 const download=(value:unknown,name:string)=>{const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
 return <section aria-label="Reconstrucción multivista R09"><h3>R09 · Pares de cámaras calibradas</h3>
 <p>Triangulación offline con correspondencias declaradas y píxeles ya sin distorsión. Declarar K, rotación mundo→cámara, traslación en metros, marco común, calibración y relojes de ambas cámaras. No estima calibración ni identidad, sincroniza video o reconstruye profundidad desde una sola cámara. Todo resultado 3D permanece inferido.</p>
 <button disabled={busy} onClick={()=>void act(async()=>edit(JSON.stringify(await api('research/r09/multiview/example'),null,2)))}>Cargar control sintético multivista R09</button>
 <label>Importar pares multivista R09<input type="file" accept=".json,application/json" disabled={busy} onChange={e=>{const file=e.target.files?.[0];e.target.value='';if(file)void act(async()=>{if(file.size>16*1024*1024)throw Error('Máximo 16 MiB');edit(JSON.stringify(JSON.parse(await file.text()),null,2))})}}/></label>
 <label>Pares y calibración JSON R09<textarea rows={12} value={text} disabled={busy} onChange={e=>edit(e.target.value)}/></label>
 <fieldset><legend>Umbrales multivista R09</legend>{([
 ['max_time_difference_s','Diferencia temporal máxima multivista (s)',0,1],
 ['max_clock_uncertainty_s','Incertidumbre declarada máxima de relojes (s)',0,1],
 ['min_ray_angle_deg','Paralaje mínimo multivista (grados)',.001,90],
 ['max_reprojection_error_px','Error máximo de reproyección multivista (px)',.001,100]
 ] as const).map(([key,label,min,max])=><label key={key}>{label}<input type="number" step="any" min={min} max={max} disabled={busy||!request} value={settings[key]} onChange={e=>edit(JSON.stringify({...request,settings:{...settings,[key]:Number(e.target.value)}},null,2))}/></label>)}</fieldset>
 <button disabled={busy||!request} onClick={()=>void act(async()=>download({schema_version:1,settings:await api('research/r09/multiview/configuration',settings)},'r09-multiview-settings.json'))}>Exportar ajustes multivista R09</button>
 <label>Importar ajustes multivista R09<input type="file" accept=".json,application/json" disabled={busy||!request} onChange={e=>{const file=e.target.files?.[0];e.target.value='';if(file)void act(async()=>{if(file.size>65536)throw Error('Máximo 64 KiB');const config=JSON.parse(await file.text());if(config.schema_version!==1||!config.settings||Object.keys(config).some(k=>!['schema_version','settings'].includes(k)))throw Error('Preset multivista v1 requerido');const validated=await api('research/r09/multiview/configuration',config.settings);edit(JSON.stringify({...request,settings:validated},null,2))})}}/></label>
 <p>Ajustes portables contienen sólo umbrales; no cámaras, calibración, identidad, relojes ni observaciones. Cargar un preset no ejecuta el cálculo.</p>
 <button disabled={busy||!request} onClick={()=>void act(async()=>{setResult(null);if(text.length>16*1024*1024)throw Error('Máximo 16 MiB');setResult(await api('research/r09/multiview',request))})}>Reconstruir pares multivista R09</button>
 <MultiviewRuns api={api} request={request} onOpen={r=>{setText(JSON.stringify(r.request,null,2));setResult(r);setError('')}}/>
 {error&&<p role="alert">{error}</p>}
 {result&&<><p>Multivista R09: {result.coverage.inferred} puntos inferidos; {result.coverage.missing} faltantes. Calibración {result.request.calibration_kind}. Baja reproyección no valida profundidad.</p>
 <SpatialView stream={result.stream} api={api}/>
 <table aria-label="Diagnóstico multivista R09"><thead><tr><th>Índice</th><th>Etiqueta</th><th>Δt (s)</th><th>Paralaje (°)</th><th>Reproyección (px)</th><th>Causa</th></tr></thead><tbody>{result.diagnostics.slice(0,200).map((r:Data)=><tr key={`${r.index}:${r.label}`}><td>{r.index}</td><td>{r.label}</td><td>{r.common_time_difference_s}</td><td>{r.ray_angle_deg??'sin soporte'}</td><td>{r.reprojection_error_px?.join(' / ')??'sin soporte'}</td><td>{r.cause||'inferido'}</td></tr>)}</tbody></table>
 <p>Tabla limitada a 200 filas; exportación conserva todos los pares y diagnósticos. Tiempos de salida son la media de tiempos comunes pareados, sin interpolar; entradas originales permanecen en el resultado.</p>
 <button onClick={()=>download(result,'r09-multiview-result.json')}>Exportar resultado multivista R09</button>
 <button onClick={()=>onStream(result.stream)}>Usar stream multivista declarado R09</button>
 <p>Usar stream lo carga como entrada declarada para validación/guardado R09; no autentica su calibración ni conserva como verificada la procedencia del cálculo. Conservar también el resultado completo para repetir triangulación.</p></>}
 </section>;
}
