import {useEffect,useState} from 'react';

const initial={schema_version:1,samples:480,hz:60,seeds:[7,19,41]};
function download(value:any,name:string){const u=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}

export function SaiFourierPanel({api}:{api:any}){
 const [settings,setSettings]=useState<any>(initial),[seeds,setSeeds]=useState('[7,19,41]'),[jobs,setJobs]=useState<any[]>([]),[result,setResult]=useState<any>(null),[opened,setOpened]=useState(''),[scenario,setScenario]=useState('coupled_multitone'),[seed,setSeed]=useState(7),[signal,setSignal]=useState('collective.residual'),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const refresh=async()=>setJobs(await api('research/sai-fourier'));
 useEffect(()=>{let live=true;const poll=()=>api('research/sai-fourier').then((r:any[])=>{if(live)setJobs(r);}).catch((e:any)=>{if(live)setError(String(e));});void poll();const timer=setInterval(poll,1000);return()=>{live=false;clearInterval(timer);};},[api]);
 const frozen=()=>({...settings,seeds:JSON.parse(seeds)});
 const start=async()=>{setBusy(true);setError('');try{await api('research/sai-fourier',frozen());await refresh();}catch(e){setError(String(e));}finally{setBusy(false);}};
 const open=async(id:string)=>{setBusy(true);setError('');try{const r=await api(`research/sai-fourier/${id}/artifacts/result.json`);setResult(r);setOpened(id);setSettings(r.settings);setSeeds(JSON.stringify(r.settings.seeds));setSeed(r.settings.seeds[0]);setScenario('coupled_multitone');}catch(e){setError(String(e));}finally{setBusy(false);}};
 const cancel=async(id:string)=>{setBusy(true);setError('');try{await api(`research/sai-fourier/${id}/cancel`,{});await refresh();}catch(e){setError(String(e));}finally{setBusy(false);}};
 const active=jobs.some(j=>['queued','running'].includes(j.status));
 const row=result?.bank.results.find((r:any)=>r.scenario===scenario&&r.seed===seed);
 const descriptor=row?.descriptors[signal];
 return <section aria-label="Controles Fourier Sai"><h3>Sai–Oliva · Controles Fourier offline</h3>
 <p>Banco sintético: original, fases compartidas y fases independientes. Conserva espectros individuales; el control compartido conserva espectros cruzados globales, pero puede modificar I local. No filtra video en vivo ni cambia sonido.</p>
 <label>Muestras Fourier<input type="number" min={64} max={1200} step={1} disabled={busy} value={settings.samples} onChange={e=>setSettings({...settings,samples:Number(e.target.value)})}/></label>
 <label>Frecuencia de muestreo Fourier (Hz)<input type="number" min={.001} max={240} step="any" disabled={busy} value={settings.hz} onChange={e=>setSettings({...settings,hz:Number(e.target.value)})}/></label>
 <label>Semillas Fourier (JSON)<input disabled={busy} value={seeds} onChange={e=>setSeeds(e.target.value)}/></label>
 <p>Duración: {(settings.samples/settings.hz).toPrecision(5)} s. Tonos sintéticos: 3, 7 y 10 ciclos por bloque; variar Hz o muestras cambia sus frecuencias físicas. Escala torso fija .26 y configuración del modelo fija en este banco.</p>
 <button disabled={busy||active} onClick={()=>void start()}>Correr banco Fourier Sai</button>
 <button disabled={busy} onClick={()=>{try{download(frozen(),'sai-fourier-settings.json');}catch(e){setError(String(e));}}}>Exportar configuración Fourier</button>
 <label>Importar configuración Fourier<input type="file" accept="application/json,.json" disabled={busy} onChange={e=>{const f=e.target.files?.[0];e.target.value='';if(!f)return;setBusy(true);setError('');void(async()=>{try{if(f.size>65536)throw Error('Configuración demasiado grande');const r=JSON.parse(await f.text());if(r.schema_version!==1||!Array.isArray(r.seeds)||typeof r.samples!=='number'||typeof r.hz!=='number')throw Error('Configuración Fourier requerida');setSettings(r);setSeeds(JSON.stringify(r.seeds));}catch(e){setError(String(e));}finally{setBusy(false);}})();}}/></label>
 <button disabled={busy} onClick={()=>void refresh().catch(e=>setError(String(e)))}>Actualizar bancos Fourier</button>
 {jobs.map(j=><div key={j.id}>{j.id} · {j.status} {j.error||j.error_type||''}{['queued','running'].includes(j.status)&&<button disabled={busy} onClick={()=>void cancel(j.id)}>Cancelar banco Fourier</button>}{j.status==='complete'&&<><button disabled={busy} onClick={()=>void open(j.id)}>Abrir banco Fourier</button>{['request.json','result.json','manifest.json'].map(n=><a key={n} href={`/api/research/sai-fourier/${j.id}/artifacts/${n}`} download>{n} </a>)}</>}</div>)}
 {error&&<p role="alert">{error}</p>}
 {result&&<><p>Banco recuperado: {opened}. Comparaciones descriptivas; tres semillas no son una distribución nula ni un test de significancia. No demuestra HIT ni eficiencia.</p>
 <label>Escenario Fourier<select aria-label="Escenario Fourier" value={scenario} onChange={e=>setScenario(e.target.value)}>{['coupled_multitone','single_channel','static'].map(s=><option key={s}>{s}</option>)}</select></label>
 <label>Semilla de resultado Fourier<select aria-label="Semilla de resultado Fourier" value={seed} onChange={e=>setSeed(Number(e.target.value))}>{result.settings.seeds.map((s:number)=><option key={s}>{s}</option>)}</select></label>
 <label>Descriptor Fourier<select aria-label="Descriptor Fourier" value={signal} onChange={e=>setSignal(e.target.value)}>{Object.keys(row?.descriptors||{}).map(s=><option key={s}>{s}</option>)}</select></label>
 {descriptor&&<><p>Soporte común de tres condiciones: {descriptor.common_observed}/{descriptor.total}; las medias usan exactamente esa intersección.</p>
 <table aria-label="Descriptores sobre soporte Fourier común"><thead><tr><th>Condición</th><th>Observados propios</th><th>Media común</th><th>Desvío común</th><th>MAE contra original</th></tr></thead><tbody>{Object.entries(descriptor.conditions).map(([name,v]:[string,any])=><tr key={name}><td>{name}</td><td>{v.observed}</td><td>{v.common_mean?.toPrecision(6)??'Sin soporte'}</td><td>{v.common_std?.toPrecision(6)??'Sin soporte'}</td><td>{name==='original'?'Referencia':descriptor.common_mae_from_original[name]?.toPrecision(6)??'Sin soporte'}</td></tr>)}</tbody></table>
 <p>MAE compartido–independiente: {descriptor.common_shared_independent_mae?.toPrecision(6)??'Sin soporte'}. No mide pérdida monotónica de organización.</p></>}
 <table aria-label="Preservación espectral Fourier"><thead><tr><th>Control</th><th>Error relativo máximo de potencia</th><th>Cambio relativo máximo de espectro cruzado</th></tr></thead><tbody>{Object.entries(row?.spectral_checks||{}).map(([name,v]:[string,any])=><tr key={name}><td>{name}</td><td>{v.power_max_relative_error.toExponential(3)}</td><td>{v.cross_spectrum_max_relative_change.toPrecision(6)}</td></tr>)}</tbody></table>
 <p>Errores normalizados por el máximo global; el cambio cruzado puede superar 1. Son espectros de coordenadas, no del audio.</p>
 </>}
 </section>;
}
