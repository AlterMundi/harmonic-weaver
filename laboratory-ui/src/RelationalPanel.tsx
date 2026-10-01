import {RelationalBodyPanel} from './RelationalBodyPanel';
import {useEffect,useState} from 'react';
type Data=Record<string,any>;
const fields:[string,string,number,number,number][]=[
 ['samples','Muestras R04',10,600,1],['hz','Frecuencia R04 (Hz)',10,120,1],
 ['history_s','Historia R04 (s)',.05,5,.05],['noise_velocity','Ruido de velocidad R04',.0001,2,.001],
 ['noise_delta','Ruido de contribución R04',.0001,2,.001],['max_gap_s','Gap R04 (s)',.05,2,.05],
 ['rotation_deg','Rotación uniforme R04 (grados)',-360,360,1],
 ['common_velocity_x','Velocidad común X R04',-10,10,.1],['common_velocity_y','Velocidad común Y R04',-10,10,.1]];
const defaults={samples:120,hz:30,history_s:.25,noise_velocity:.02,noise_delta:.015,max_gap_s:.25,relation_reference:'history',rotation_deg:73,common_velocity_x:2,common_velocity_y:-1};
function valid(value:Data){return fields.every(([k,,min,max])=>typeof value[k]==='number' && Number.isFinite(value[k]) && value[k]>=min && value[k]<=max) && Number.isInteger(value.samples) && ['history','instantaneous'].includes(value.relation_reference);}
export function RelationalPanel({api,run}:Data){
 const [settings,setSettings]=useState<Data>(defaults),[jobs,setJobs]=useState<Data[]>([]),[text,setText]=useState(''),[error,setError]=useState('');
 const [result,setResult]=useState<Data|null>(null),[trace,setTrace]=useState(''),[sample,setSample]=useState(0),[busy,setBusy]=useState(false);
 useEffect(()=>{let live=true;const poll=async()=>{try{const value=await api('research/r04');if(live)setJobs(value);}catch(e){if(live)setError(String(e));}};void poll();const timer=setInterval(poll,1000);return()=>{live=false;clearInterval(timer);};},[api]);
 const rows=result?.traces[trace] || [],row=rows[sample];
 return <section><h2>R04 · Interferencia relacional sintética</h2>
  <p>Pruebas del estimador de producción sobre velocidades 2D construidas. No mide fuerzas ni eficiencia, no demuestra intención o HIT y no cambia el sonido.</p>
  {error && <p role="alert">{error}</p>}
  {fields.map(([key,label,min,max,step])=><label key={key}>{label}<input type="number" min={min} max={max} step={step} value={settings[key]} onChange={e=>setSettings({...settings,[key]:+e.target.value})}/></label>)}
  <label>Referencia relacional R04<select value={settings.relation_reference} onChange={e=>setSettings({...settings,relation_reference:e.target.value})}><option value="history">Historia anterior</option><option value="instantaneous">Velocidad instantánea</option></select></label>
  <p>Umbrales de ruido sintéticos, sin calibración corporal. Cinco escenarios × original, rotación uniforme, inversión de ambos extremos y velocidad común. Invertir ambos extremos no equivale a oposición local favorable.</p>
  <button disabled={!valid(settings) || busy || jobs.some(j=>['queued','running'].includes(j.status))} onClick={()=>run(async()=>{setBusy(true);try{await api('research/r04',settings);setJobs(await api('research/r04'));}finally{setBusy(false);}})}>Correr banco R04</button>
  <button onClick={()=>setText(JSON.stringify(settings,null,2))}>Exportar configuración R04</button>
  <textarea aria-label="Configuración R04 JSON" value={text} onChange={e=>setText(e.target.value)}/>
  <button onClick={()=>run(async()=>{const value=JSON.parse(text);if(!value || Array.isArray(value) || Object.keys(value).some(k=>!(k in defaults)))throw Error('Configuración R04 inválida');const next={...defaults,...value};if(!valid(next))throw Error('Parámetros R04 fuera de rango');setSettings(next);})}>Importar configuración R04</button>
  <RelationalBodyPanel api={api} run={run} settings={settings} settingsValid={valid(settings)} active={busy || jobs.some(j=>['queued','running'].includes(j.status))} onStarted={async()=>setJobs(await api('research/r04'))}/>
  {jobs.map(j=><div key={j.id}><p>{j.id} · {j.status} · {j.error || ''}</p>{['queued','running'].includes(j.status) && <button onClick={()=>run(async()=>{await api(`research/r04/${j.id}/cancel`,{});setJobs(await api('research/r04'));})}>Cancelar R04 {j.id}</button>}{j.status==='complete' && <><button onClick={()=>run(async()=>{const value=await api(`research/r04/${j.id}/artifacts/result.json`);setResult(value);setTrace(Object.keys(value.traces)[0]);setSample(0);})}>Ver resultado R04 {j.id}</button>{['request.json','result.json','manifest.json'].map(name=><a key={name} href={`/api/research/r04/${j.id}/artifacts/${name}`}>{name} </a>)}</>}</div>)}
  {result && <><label>Traza R04<select value={trace} onChange={e=>{setTrace(e.target.value);setSample(0);}}>{Object.keys(result.traces).map(k=><option key={k} value={k}>{k}</option>)}</select></label>
   <label>Muestra de traza R04<input type="range" min={0} max={Math.max(0,rows.length-1)} value={sample} onChange={e=>setSample(+e.target.value)}/></label>
   {row && <><p>t={row.time_s} s · {row.relative.state} · {row.relative.reason || ''}</p><table><thead><tr><th>I</th><th>R</th><th>A</th><th>Velocidad proximal</th><th>Velocidad distal</th></tr></thead><tbody><tr><td>{row.relative.I ?? 'indefinido'}</td><td>{row.relative.R ?? 'indefinido'}</td><td>{row.relative.A ?? 'indefinido'}</td><td>{JSON.stringify(row.parent_velocity)}</td><td>{JSON.stringify(row.child_velocity)}</td></tr></tbody></table></>}
   <p>Un estado faltante no es neutralidad. El giro usa pasos finitos y modo pasado: I no tiene por qué ser exactamente cero.</p>
   <ul>{result.limits.map((limit:string)=><li key={limit}>{limit}</li>)}</ul></>}
 </section>;
}
