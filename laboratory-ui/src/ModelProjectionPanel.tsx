import {useEffect,useRef,useState} from 'react';
import {pastWindow} from './projectionClock';
type Data=Record<string,any>;
const defaults={arm:'single',points:512,stride:1,weights:null,phase_offsets_rad:null,scale_x:1,scale_y:1};
const playbackDefaults={follow_audio:true,refresh_hz:10,preview_gain:1,loop_audio:false};
export function ModelProjectionPanel({job,api,run}:Data){
 const [settings,setSettings]=useState<Data>({...defaults,arm:job.kind==='mechanism_comparison'?'excited':'single'}),[sample,setSample]=useState(0),[arrays,setArrays]=useState<Data>({}),[text,setText]=useState(''),[result,setResult]=useState<Data|null>(null),[busy,setBusy]=useState(false);
 const canvas=useRef<HTMLCanvasElement>(null),generation=useRef(0);
 const audio=useRef<HTMLAudioElement>(null),inFlight=useRef(false),pendingFollow=useRef(false),lastWindow=useRef(-1);
 const [playback,setPlayback]=useState<Data>(playbackDefaults),[audioSrc,setAudioSrc]=useState(''),[metadata,setMetadata]=useState<Data|null>(null),[playing,setPlaying]=useState(false),[playerError,setPlayerError]=useState('');
 const settingsValue=()=>{const value={...settings};for(const [key,text] of Object.entries(arrays))value[key]=JSON.parse(text as string);return value;};
 const paired=job.kind==='mechanism_comparison';
 const invalidate=()=>{generation.current++;lastWindow.current=-1;setBusy(false);setResult(null);};
 const stopAudio=()=>{pendingFollow.current=false;audio.current?.pause();setAudioSrc('');setMetadata(null);setPlaying(false);invalidate();};
 const latest=useRef<Data>({});latest.current={settings,arrays,playback,metadata};
 const followWindow=async()=>{
  const el=audio.current,{settings,arrays,playback,metadata}=latest.current;
  if(!el || el.seeking || !metadata || !playback.follow_audio)return;
  if(inFlight.current){pendingFollow.current=true;return;}
  pendingFollow.current=false;
  let window:any,parameters:Data;
  try{parameters={...settings};for(const [key,text] of Object.entries(arrays))parameters[key]=JSON.parse(text as string);window=pastWindow(el.currentTime,metadata.sample_rate,metadata.total_frames,parameters.points,parameters.stride);}catch(e){setPlayerError(String(e));audio.current?.pause();return;}
  if(!window || window.start_sample===lastWindow.current)return;
  const version=generation.current;inFlight.current=true;lastWindow.current=window.start_sample;
  try{const value=await api(`research/r05/${job.id}/projection`,{...parameters,...window});if(version===generation.current){setResult(value);setSample(window.start_sample);setPlayerError('');}}
  catch(e){if(version===generation.current){setPlayerError(String(e));setResult(null);audio.current?.pause();}}
  finally{inFlight.current=false;if(pendingFollow.current)void followWindow();}
 };
 useEffect(()=>{invalidate();},[settings,arrays,playback.follow_audio]);
 useEffect(()=>{let frame=0,last=-Infinity;const tick=(now:number)=>{if(audio.current && !audio.current.paused && now-last>=1000/latest.current.playback.refresh_hz){last=now;void followWindow();}frame=requestAnimationFrame(tick);};if(audioSrc)frame=requestAnimationFrame(tick);return()=>cancelAnimationFrame(frame);},[audioSrc]);
 useEffect(()=>()=>{audio.current?.pause();},[]);
 const refresh=()=>run(async()=>{const current=++generation.current;setBusy(true);try{const value=await api(`research/r05/${job.id}/projection`,{...settingsValue(),start_sample:sample});if(current===generation.current)setResult(value);}finally{if(current===generation.current)setBusy(false);}});
 useEffect(()=>()=>{generation.current++;},[]);
 useEffect(()=>{const el=canvas.current,ctx=el?.getContext('2d');if(!el || !ctx)return;ctx.fillStyle='#041020';ctx.fillRect(0,0,el.width,el.height);if(!result)return;ctx.strokeStyle='#74e6d2';ctx.lineWidth=1;ctx.beginPath();result.points.forEach(([x,y]:number[],i:number)=>{const px=el.width/2+x*el.width/2,py=el.height/2-y*el.height/2;if(i===0)ctx.moveTo(px,py);else ctx.lineTo(px,py);});ctx.stroke();},[result]);
 return <section><h3>Proyección del estado R05 · {job.id}</h3><p>Suma de todas las voces guardadas. X real, Y audible con pesos/fases explícitos; figura teórica del modelo, no cymatic físico ni fase corporal.</p>
  <label>Brazo de proyección R05<select value={settings.arm} onChange={e=>{stopAudio();setSettings({...settings,arm:e.target.value});}}>{(paired?['excited','mapped']:['single']).map(a=><option key={a}>{a}</option>)}</select></label>
  <label>Muestra inicial de proyección R05<input type="number" min={0} step={1} value={sample} onChange={e=>setSample(+e.target.value)}/></label>
  {['points','stride','scale_x','scale_y'].map(key=><label key={key}>{key} proyección R05<input type="number" step={key.startsWith('scale')?'any':1} value={settings[key]} onChange={e=>setSettings({...settings,[key]:+e.target.value})}/></label>)}
  {['weights','phase_offsets_rad'].map(key=><label key={key}>{key} proyección R05<textarea value={arrays[key] ?? JSON.stringify(settings[key])} onChange={e=>setArrays({...arrays,[key]:e.target.value})}/></label>)}
  <p>null usa todas las voces con peso1/fase0; listas deben tener una entrada por voz. Escala explícita sin normalización; valores fuera del canvas se recortan. Stride es decimación visual sin antialias.</p>
  <label><input type="checkbox" checked={playback.follow_audio} onChange={e=>setPlayback({...playback,follow_audio:e.target.checked})}/>Seguir reloj de audio R05</label>
  <label>Actualizaciones de figura R05 (Hz)<input type="number" min={1} max={30} value={playback.refresh_hz} onChange={e=>setPlayback({...playback,refresh_hz:+e.target.value})}/></label>
  <label>Ganancia de vista audio R05<input type="number" min={0} max={10} step=".1" value={playback.preview_gain} onChange={e=>{stopAudio();setPlayback({...playback,preview_gain:+e.target.value});}}/></label>
  <label><input type="checkbox" checked={playback.loop_audio} onChange={e=>setPlayback({...playback,loop_audio:e.target.checked})}/>Loop de audio R05</label>
  <button onClick={()=>run(async()=>{const version=++generation.current;const validated=await api('research/r05/projection/configuration',{schema_version:1,settings:settingsValue(),playback});const meta=await api(`research/r05/${job.id}/projection`,{...validated.settings,start_sample:0,points:2});if(version!==generation.current)return;stopAudio();setMetadata(meta);setAudioSrc(`/api/research/r05/${job.id}/listen/${validated.settings.arm}?gain=${validated.playback.preview_gain}`);setPlayerError('');})}>Cargar audio R05</button>
  {audioSrc && <audio ref={audio} aria-label="Reproductor de vista R05" controls preload="metadata" src={audioSrc} loop={playback.loop_audio} onPlay={()=>{invalidate();setPlaying(true);}} onPause={()=>setPlaying(false)} onSeeking={invalidate} onSeeked={()=>void followWindow()} onEnded={()=>{setPlaying(false);void followWindow();}} onError={()=>setPlayerError(audio.current?.error?.message || 'No se pudo decodificar audio R05')}/>}
  {playerError && <p role="alert">{playerError}</p>}
  <p>Escucha float32 derivada del WAV DOUBLE: ganancia explícita, sin normalización/limitador. Ventana de figura sólo sobre muestras ya reproducidas. Frecuencia de actualización solicitada, no latencia física medida.</p>
  <button disabled={busy || playing && playback.follow_audio} onClick={refresh}>Leer ventana de proyección R05</button>
  <button onClick={()=>run(async()=>setText(JSON.stringify(await api('research/r05/projection/configuration',{schema_version:1,settings:settingsValue(),playback}),null,2)))}>Exportar proyección R05</button>
  <textarea aria-label="Preset de proyección R05 JSON" value={text} onChange={e=>setText(e.target.value)}/>
  <button onClick={()=>run(async()=>{const value=await api('research/r05/projection/configuration',JSON.parse(text));if(! (paired?['excited','mapped']:['single']).includes(value.settings.arm))throw Error('Brazo de preset incompatible con esta corrida');stopAudio();setSettings(value.settings);setArrays({});setPlayback(value.playback || playbackDefaults);})}>Importar proyección R05</button>
  <p>Preset no incluye corrida, persona, calibración ni muestra inicial. Importar detiene la escucha y no reproduce automáticamente.</p>
  <canvas ref={canvas} width={600} height={400} aria-label="Figura de todas las voces R05" style={{width:'100%',maxWidth:600}}/>
  {result && <p>Ventana congelada: {result.voices} voces · muestras {result.sample_indices[0]}–{result.sample_indices.at(-1)} · {result.sample_rate} Hz · {result.tail.some((v:boolean)=>v)?'incluye cola del instrumento':'tramo de fuente'} · {result.verification_mode}</p>}
 </section>;
}
