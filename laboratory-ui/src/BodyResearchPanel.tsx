import {ForecastControls,defaultPredictors} from './ForecastControls';
import {useEffect,useState} from 'react';
type Data=Record<string,any>;
const defaults={seed:0,components:2,window_s:2,noise_threshold:.02,ridge:.1,horizon_steps:1,max_gap_s:.1,predictors:defaultPredictors,autoregressive_lags:3};
export function BodyResearchPanel({api,run,onStarted}:Data){
 const [jobs,setJobs]=useState<Data[]>([]),[evaluation,setEvaluation]=useState(''),[report,setReport]=useState<Data|null>(null);
 const [index,setIndex]=useState(0),[signals,setSignals]=useState<string[]>([]),[settings,setSettings]=useState<Data>(defaults);
 const [start,setStart]=useState(0),[end,setEnd]=useState(1),[text,setText]=useState(''),[error,setError]=useState('');
 const refresh=async()=>{try{setJobs((await api('evaluations')).filter((j:Data)=>j.status==='complete'));setError('');}catch(e){setError(String(e));}};
 useEffect(()=>{void refresh();},[api]);
 useEffect(()=>{let live=true;setReport(null);setSignals([]);if(evaluation)void api(`evaluations/${evaluation}/report`).then((r:Data)=>{if(live){setReport(r);setIndex(0);}}).catch((e:any)=>{if(live)setError(String(e));});return()=>{live=false};},[evaluation,api]);
 const selected=report?.manifest.runs[index];
 useEffect(()=>{if(!selected)return;const source=report!.manifest.request.sources[selected.source_index];setStart(source.start_s);setEnd(Math.min(source.end_s,source.start_s+120));setSignals([]);},[report,index]);
 const catalog=selected?.signals || {};
 const units=new Set(signals.map(id=>catalog[id]?.unit));
 const valid=(settings.predictors||defaultPredictors).length>0 && !!selected && signals.length>=2 && signals.length<=16 && signals.every(id=>catalog[id]) && units.size===1 && settings.components<=signals.length;
 return <section>
  <h2>R01 · Features del comparador</h2>
  <p>Usa una corrida local congelada y verificada. No abre el video ni cambia el instrumento o la calibración. El horizonte cuenta muestras únicas de features; su duración real queda en las traces.</p>
  <button onClick={()=>void refresh()}>Actualizar comparaciones disponibles</button>
  {error && <p role="alert">{error}</p>}
  <label>Comparación de origen<select value={evaluation} onChange={e=>setEvaluation(e.target.value)}><option value="">Elegir comparación terminada</option>{jobs.map(j=><option key={j.id} value={j.id}>{j.id}</option>)}</select></label>
  {report && <>
   <label>Corrida de origen<select value={index} onChange={e=>setIndex(+e.target.value)}>{report.manifest.runs.map((r:Data,i:number)=><option key={i} value={i}>Fuente {r.source_index+1} · {r.preset_id}</option>)}</select></label>
   <p>Persona: {report.manifest.request.sources[selected.source_index].person_id}. Señales en sus unidades originales; no se mezclan unidades ni se normaliza usando datos futuros.</p>
   <label>Inicio del segmento (s)<input type="number" step=".1" value={start} onChange={e=>setStart(+e.target.value)}/></label>
   <label>Fin del segmento (s)<input type="number" step=".1" value={end} onChange={e=>setEnd(+e.target.value)}/></label>
   <details open><summary>Señales: elegir 2–16 con la misma unidad</summary>{Object.entries(catalog).map(([id,signal]:[string,any])=><label className="check" key={id}><input type="checkbox" checked={signals.includes(id)} onChange={e=>setSignals(e.target.checked?[...signals,id]:signals.filter(k=>k!==id))}/>{id} · {signal.unit} · {signal.observed_count} observaciones</label>)}</details>
  </>}
  <div className="fields">{[
   ['seed','Semilla del control corporal',0,2147483647,1],['components','Componentes corporales',1,12,1],
   ['window_s','Ventana corporal (s)',.3,10,.1],['noise_threshold','Umbral corporal',.0001,2,.001],
   ['ridge','Ridge corporal',.00001,100,.01],['horizon_steps','Horizonte corporal (muestras)',1,30,1],
   ['max_gap_s','Gap máximo corporal (s)',.01,.5,.01],
  ].map(([key,label,min,max,step])=><label key={key}>{label}<input type="number" min={min} max={max} step={step} value={settings[key]} onChange={e=>setSettings({...settings,[key]:+e.target.value})}/></label>)}</div>
  <ForecastControls settings={settings} onChange={setSettings} scope="R01 corporal"/>
  <p>Faltantes y gaps reinician historia y pronósticos. Repeticiones del mismo timestamp por el reloj de control se excluyen. Rotación en el espacio de features no equivale a rotar físicamente el cuerpo; shuffle preserva los límites de los segmentos válidos.</p>
  <button disabled={!valid} onClick={()=>run(async()=>{await api('research/r01/trace',{...settings,evaluation_id:evaluation,run_index:index,signal_ids:signals,start_s:start,end_s:end});await onStarted();})}>Correr R01 con features</button>
  <button onClick={()=>setText(JSON.stringify({settings,signal_ids:signals},null,2))}>Exportar configuración corporal JSON</button>
  <textarea aria-label="Configuración corporal JSON" value={text} onChange={e=>setText(e.target.value)}/>
  <button onClick={()=>run(async()=>{const config=JSON.parse(text);
   if(!config.settings || !Array.isArray(config.signal_ids) || !config.signal_ids.every((id:any)=>typeof id==='string') || Object.entries(config.settings).some(([key,value])=>!(key in defaults) || (key==='predictors'? !Array.isArray(value)||!value.length||!value.every((k:any)=>typeof k==='string'):typeof value!=='number' || !Number.isFinite(value))))throw Error('Configuración corporal inválida');
   setSettings({...defaults,...config.settings});setSignals(config.signal_ids);
  })}>Importar configuración corporal JSON</button>
 </section>;
}
