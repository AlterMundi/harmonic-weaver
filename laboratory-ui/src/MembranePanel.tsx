import {useEffect,useState,useRef} from 'react';
type Data=Record<string,any>;
export function MembranePanel({api}:Data){
 const [frame,setFrame]=useState(-1);
 const [resultId,setResultId]=useState(''),[follow,setFollow]=useState(false);
 const audio=useRef<HTMLAudioElement|null>(null);
 const [settings,setSettings]=useState<Data|null>(null),[sources,setSources]=useState<Data[]>([]),[source,setSource]=useState(''),[jobs,setJobs]=useState<Data[]>([]),[result,setResult]=useState<Data|null>(null),[text,setText]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false),[scale,setScale]=useState(10000);
 useEffect(()=>{setFrame(-1);},[result]);
 useEffect(()=>{let live=true;void api('research/r07/configuration',{}).then((v:Data)=>{if(live)setSettings(v.settings);}).catch((e:any)=>{if(live)setError(String(e));});const poll=async()=>{try{const [a,b]=await Promise.all([api('research/r05'),api('research/r07')]);if(live){setSources(a.filter((j:Data)=>j.status==='complete'));setJobs(b);}}catch(e){if(live)setError(String(e));}};void poll();const timer=setInterval(poll,1000);return()=>{live=false;clearInterval(timer);};},[api]);
 const act=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');try{await fn();}catch(e){setError(String(e));}finally{setBusy(false);}};
 const config=()=>({schema_version:1,settings});
 const active=busy||jobs.some(j=>j.worker_active||['queued','running'].includes(j.status));
 useEffect(()=>{if(!follow||!result?.trajectory)return;let raf=0;const sync=()=>{const time=audio.current?.currentTime??0;let index=-2;for(let i=0;i<result.trajectory.length;i++){if(result.trajectory[i].last_output_time_s<=time)index=i;else break;}setFrame(index);raf=requestAnimationFrame(sync);};sync();return()=>cancelAnimationFrame(raf);},[follow,result]);
 const selected=frame===-2?null:frame>=0?result?.trajectory?.[frame]:result?.window;
 const grid=selected?.rms as number[][]|undefined;
 return <section><h2>R07 · Membrana virtual</h2><p>Mezcla PCM verificada → membrana de bordes fijos. RMS de desplazamiento sin calibración física; no simula arena ni agua. No cambia el instrumento live.</p>
 {error&&<p role="alert">{error}</p>}
 <label>Fuente R05 para R07<select value={source} onChange={e=>setSource(e.target.value)}><option value="">Elegir corrida completa</option>{sources.map(j=><option key={j.id} value={j.id}>{j.id}</option>)}</select></label>
 {settings&&<><label>Brazo R07<select value={settings.arm} onChange={e=>setSettings({...settings,arm:e.target.value})}>{['single','excited','mapped'].map(k=><option key={k}>{k}</option>)}</select></label>
 {Object.entries(settings).filter(([k,v])=>typeof v==='number').map(([k,v])=><label key={k}>{k}<input aria-label={`R07 ${k}`} type="number" value={v as number} onChange={e=>setSettings({...settings,[k]:+e.target.value})}/></label>)}
 {Object.entries(settings.membrane).map(([k,v])=><label key={k}>{k}<input aria-label={`R07 ${k}`} type="number" step="any" value={v as number} onChange={e=>setSettings({...settings,membrane:{...settings.membrane,[k]:+e.target.value}})}/></label>)}
 <label><input type="checkbox" checked={!!settings.trajectory} onChange={e=>{const value={...settings};if(e.target.checked)value.trajectory={window_samples:Math.round(settings.membrane.sample_rate*.1),hop_samples:Math.round(settings.membrane.sample_rate*.1)};else delete value.trajectory;setSettings(value);}}/>Secuencia causal R07</label>
 {settings.trajectory&&['window_samples','hop_samples'].map(k=><label key={k}>{k}<input aria-label={`R07 ${k}`} type="number" value={settings.trajectory[k]} onChange={e=>setSettings({...settings,trajectory:{...settings.trajectory,[k]:+e.target.value}})}/></label>)}
 <button disabled={active||!source} onClick={()=>void act(async()=>{const value=await api('research/r07/configuration',config());await api('research/r07',{source_run_id:source,settings:value.settings});})}>Calcular membrana R07</button>
 <button disabled={busy} onClick={()=>void act(async()=>{setText(JSON.stringify(await api('research/r07/configuration',config()),null,2));})}>Exportar configuración R07</button></>}
 <label>Preset portable R07<textarea value={text} onChange={e=>setText(e.target.value)}/></label><button disabled={busy} onClick={()=>void act(async()=>{const value=await api('research/r07/configuration',JSON.parse(text));setSettings(value.settings);})}>Importar configuración R07</button>
 {jobs.map(j=><div key={j.id}>{j.id} · {j.status}{['queued','running'].includes(j.status)&&<button onClick={()=>void act(async()=>{await api(`research/r07/${j.id}/cancel`,{});})}>Cancelar R07</button>}{j.status==='complete'&&<><button onClick={()=>void act(async()=>{setFollow(false);setResultId(j.id);setResult(await api(`research/r07/${j.id}/artifacts/result.json`));})}>Ver figura R07</button>{['request.json','result.json','manifest.json'].map(n=><a key={n} href={`/api/research/r07/${j.id}/artifacts/${n}`} download>{n} </a>)}</>}</div>)}
 {result&&<audio key={resultId} ref={audio} controls aria-label="Audio de la figura R07" src={`/api/research/r07/${resultId}/listen`} onError={()=>setError('No se pudo cargar el audio vinculado a esta figura')}/>}
 {result?.trajectory&&<label><input type="checkbox" checked={follow} onChange={e=>setFollow(e.target.checked)}/>Seguir audio R07</label>}
 {frame===-2&&<p>Todavía no ocurrió el primer frame de esta secuencia.</p>}
 {result?.trajectory&&<label>Frame R07<select disabled={follow} value={frame} onChange={e=>setFrame(+e.target.value)}><option value={-2}>Sin frame pasado</option><option value={-1}>RMS global de la ventana</option>{result.trajectory.map((f:Data,i:number)=><option key={i} value={i}>{i+1} · t={f.last_output_time_s}s</option>)}</select></label>}
 {grid&&<><p>Figura congelada · {result?.request.arm} · muestras {selected.start_sample}–{selected.stop_sample_exclusive} (fin exclusivo){selected.warmup?' · calentamiento':''}. Editar controles no altera esta figura.</p><label>Escala visual R07<input type="number" min={0} step="any" value={scale} onChange={e=>setScale(Math.max(0,+e.target.value))}/></label>
 <svg viewBox={`0 0 ${grid[0].length} ${grid.length}`} width="360" height="360" aria-label="Campo RMS R07">{grid.flatMap((row,y)=>row.map((v,x)=><rect key={`${x}.${y}`} x={x} y={y} width={1} height={1} fill={`rgb(${Math.min(255,v*scale*255)},0,${255-Math.min(255,v*scale*255)})`}><title>{`x=${x/(row.length-1)}, y=${y/(grid.length-1)}, RMS=${v}`}</title></rect>))}</svg><p>Escala de color explícita: azul=0, rojo≥{scale?1/scale:'∞'}; valores crudos en cada celda y artifact.</p><details><summary>Configuración y límites de la figura</summary><pre>{JSON.stringify(result,null,2)}</pre></details></>}
 </section>;
}
