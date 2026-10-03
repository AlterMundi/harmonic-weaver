import {PhysiologyPanel} from './PhysiologyPanel';
import {NeuroPanel} from './NeuroPanel';
import {ExperiencePanel} from './ExperiencePanel';
import {SpatialPanel} from './SpatialPanel';
import {RopePanel} from './RopePanel';
import {useEffect,useState} from 'react';
import {RelationalPanel} from './RelationalPanel';
import {ActivationPanel} from './ActivationPanel';
import {MembranePanel} from './MembranePanel';
import {MembraneTransferPanel} from './MembraneTransferPanel';
import {MembraneControlsPanel} from './MembraneControlsPanel';
import {ResonatorPanel} from './ResonatorPanel';
import {CoincidencePanel} from './CoincidencePanel';
import {BodyResearchPanel} from './BodyResearchPanel';
type Data=Record<string,any>;
const defaults={seed:0,samples:360,control_hz:30,dimensions:8,signal_rank:3,components:3,window_s:2,noise_std:.01,noise_threshold:.02,ridge:.1,horizon_steps:1,scenario:'fixed_span',rotation_deg_s:30,temporal_memory:.95};
export function ResearchPanel({api,run}:Data){
 const [settings,setSettings]=useState<Data>(defaults),[jobs,setJobs]=useState<Data[]>([]);
 const [text,setText]=useState(''),[paired,setPaired]=useState(true);
 useEffect(()=>{let live=true;const poll=()=>api('research/r01').then((j:Data[])=>{if(live)setJobs(j)}).catch(()=>{});
 void poll();const timer=setInterval(poll,1000);return()=>{live=false;clearInterval(timer)};},[api]);
 const active=jobs.some(j=>j.status==='running');
 return <>
  <h2>R01 · Geometría y predicción</h2>
  <p>Banco sintético independiente del instrumento. Compara subespacios del pasado, predicción a horizonte configurable y controles; no produce evidencia corporal ni prueba HIT.</p>
  <label>Dinámica sintética<select value={settings.scenario} onChange={e=>setSettings({...settings,scenario:e.target.value})}>
   <option value="fixed_span">Subespacio fijo con oscilaciones</option><option value="rotating_span">Subespacio que rota</option><option value="stochastic_span">Subespacio fijo estocástico</option>
  </select></label>
  <div className="fields">{[
   ['seed','Semilla',0,2147483647,1],['samples','Muestras',60,1200,1],['control_hz','Frecuencia (Hz)',10,120,1],
   ['dimensions','Dimensiones',2,16,1],['signal_rank','Rango de la señal',1,8,1],['components','Componentes estimados',1,12,1],
   ['window_s','Ventana del pasado (s)',.3,10,.1],['noise_std','Ruido sintético (desvío)',0,1,.001],
   ['noise_threshold','Umbral del estimador',.0001,2,.001],['ridge','Regularización ridge',.00001,100,.01],
   ['horizon_steps','Horizonte de predicción (pasos)',1,30,1],
   ['rotation_deg_s','Rotación del subespacio (grados/s)',0,360,1],['temporal_memory','Memoria estocástica',0,.999,.01],
  ].map(([key,label,min,max,step])=><label key={key}>{label}<input type="number" value={settings[key]} min={min} max={max} step={step}
    onChange={e=>setSettings({...settings,[key]:+e.target.value})}/></label>)}</div>
  <button disabled={active} onClick={()=>run(async()=>{await api('research/r01',settings);setJobs(await api('research/r01'));})}>Correr banco R01</button>
  <p>Horizonte: {((settings.horizon_steps ?? 1)/settings.control_hz).toFixed(3)} s. Cada predicción queda congelada con datos disponibles en su origen; el residuo geométrico se calcula en el instante objetivo y usa otra ventana.</p>
  <button onClick={()=>setText(JSON.stringify(settings,null,2))}>Exportar configuración JSON</button>
  <textarea aria-label="Configuración R01 JSON" value={text} onChange={e=>setText(e.target.value)}/>
  <button onClick={()=>run(async()=>setSettings(JSON.parse(text)))}>Importar configuración JSON</button>
  <p>Original, rotación global y orden temporal mezclado usan las mismas muestras. El residuo de reconstrucción y el error de predicción son observables distintos. Compará métodos dentro del soporte común de cada control.</p>
  <label><input type="checkbox" checked={paired} onChange={e=>setPaired(e.target.checked)}/>Comparar controles sobre instantes comunes</label>
  <RelationalPanel api={api} run={run}/>
  <ResonatorPanel api={api} run={run}/>
  <ActivationPanel api={api} run={run}/>
  <MembranePanel api={api}/>
  <MembraneTransferPanel api={api}/>
  <MembraneControlsPanel api={api}/>
  <RopePanel api={api}/>
  <SpatialPanel api={api}/>
  <ExperiencePanel api={api}/>
  <NeuroPanel api={api}/>
  <PhysiologyPanel api={api}/>
  <CoincidencePanel api={api} run={run}/>
  <BodyResearchPanel api={api} run={run} onStarted={async()=>setJobs(await api('research/r01'))}/>
  {jobs.map(j=><section key={j.id}><p>{j.status} · {j.error || ''} · {j.directory}</p>
   {j.input_kind==='evaluation_features' && <p>Features: {j.signal_ids.join(', ')} · unidad {j.unit} · {j.contiguous_segments} segmentos válidos · {j.invalid_observations} faltantes · {j.duplicate_control_holds_excluded} repeticiones excluidas</p>}
   {j.status==='running' && <button onClick={()=>run(async()=>{await api(`research/r01/${j.id}/cancel`,{});setJobs(await api('research/r01'));})}>Cancelar corrida R01</button>}
   <a href={`/api/research/r01/${j.id}/artifacts/manifest.json`} download>Manifest R01</a>
   {j.status==='complete' && <div>
    <a href={`/api/research/r01/${j.id}/artifacts/request.json`} download>Configuración de corrida</a>
    {Object.keys(j.artifact_hashes || {}).map(name=><span key={name}>{' · '}<a href={`/api/research/r01/${j.id}/artifacts/${name}`} download>{name}</a></span>)}
   </div>}
   {j.paired && <p>Soporte pareado: {j.paired.common_samples} instantes. Empareja posiciones del reloj; el shuffle cambia el vector observado.</p>}
   {j.results && <table><thead><tr><th>Control</th><th>Muestras comunes</th><th>Persistencia MSE</th><th>Ridge completo MSE</th><th>Ridge subespacio MSE</th><th>Residuo reconstrucción</th></tr></thead>
    <tbody>{Object.entries(paired && j.paired ? j.paired.results : j.results).map(([name,value]:[string,any])=><tr key={name}><td>{name}</td><td>{value.common_samples}</td>
    {['persistence','full_ridge','subspace_ridge'].map(k=><td key={k}>{value.mean_prediction_mse[k]?.toPrecision(5) ?? 'Sin soporte'}</td>)}
    <td>{value.mean_reconstruction_residual?.toPrecision(5) ?? 'Sin soporte'}</td></tr>)}</tbody></table>}
  </section>)}
 </>;
}
