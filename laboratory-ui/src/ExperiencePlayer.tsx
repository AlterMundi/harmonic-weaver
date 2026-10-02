import {useEffect,useRef,useState} from 'react';
import {VideoFollower} from './videoFollower';
type Clock={position:number,playing:boolean,epoch:number,anchor:number,started:number};
export function ExperiencePlayer({api,protocolId,trials}:{api:any,protocolId:string,trials:any[]}){
 const [trial,setTrial]=useState(trials[0]?.trial_id||''),[info,setInfo]=useState<any>(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[status,setStatus]=useState('Sin preparar'),[elapsed,setElapsed]=useState(0),[playing,setPlaying]=useState(false),[ready,setReady]=useState(0);
 const video=useRef<HTMLVideoElement>(null),audio=useRef<HTMLAudioElement>(null),clock=useRef<Clock>({position:0,playing:false,epoch:0,anchor:0,started:0}),generation=useRef(0);
 const stop=(reason:string)=>{const c=clock.current;c.playing=false;c.anchor=c.position;video.current?.pause();audio.current?.pause();setPlaying(false);setStatus(reason);};
 useEffect(()=>()=>{generation.current++;clock.current.playing=false;video.current?.pause();audio.current?.pause();},[]);
 useEffect(()=>{
  if(!info)return;let frame=0;const v=video.current,a=audio.current,c=clock.current;let exhausted=false,lastSupport=false;
  const support=()=>{const s=info.audio_support_elapsed_s;return !!s&&c.position>=s[0]&&c.position<s[1]&&!exhausted;};
  const targetVideo=()=>({position:info.clock.video_source_origin_s+c.position,playing:c.playing&&!!v&&v.readyState>=2,epoch:c.epoch});
  const targetAudio=()=>({position:Math.max(0,Math.min(info.source.pcm_frames/info.source.sample_rate,c.position+info.clock.audio_elapsed_offset_s)),playing:c.playing&&support()&&!!a&&a.readyState>=2,epoch:c.epoch});
  const fail=(message:string)=>{stop('Error de reproducción');setError(message);};
  const vf=v?new VideoFollower(v,targetVideo,fail):null,af=a?new VideoFollower(a,targetAudio,fail):null;
  const waiting=()=>{if(c.playing)stop('Pausado por buffering; reanudar explícitamente');};
  const ended=()=>{if(!c.playing)return;if(c.position>=info.duration_s-.05){c.position=info.duration_s;setElapsed(c.position);stop('Fin del transporte nominal');}else if(a?.ended&&info.audio_support_elapsed_s&&Math.abs(c.position-info.audio_support_elapsed_s[1])<.1){exhausted=true;}else stop('Medio terminó antes del reloj nominal');};
  v?.addEventListener('waiting',waiting);a?.addEventListener('waiting',waiting);v?.addEventListener('ended',ended);a?.addEventListener('ended',ended);
  let previousEpoch=c.epoch;
  const tick=()=>{if(c.epoch!==previousEpoch){exhausted=false;previousEpoch=c.epoch;}if(c.playing){c.position=Math.min(info.duration_s,c.anchor+(performance.now()-c.started)/1000);setElapsed(c.position);if(c.position>=info.duration_s)stop('Fin del transporte nominal');}const active=support();if(active!==lastSupport){c.epoch++;previousEpoch=c.epoch;lastSupport=active;}vf?.sync();af?.sync();frame=requestAnimationFrame(tick);};tick();
  return()=>{cancelAnimationFrame(frame);vf?.dispose();af?.dispose();v?.pause();a?.pause();v?.removeEventListener('waiting',waiting);a?.removeEventListener('waiting',waiting);v?.removeEventListener('ended',ended);a?.removeEventListener('ended',ended);};
 },[info]);
 const base=`/api/research/r10/protocols/${protocolId}/trials/${trial}`;
 const prepare=async()=>{stop('Preparando');setInfo(null);setError('');setBusy(true);const token=++generation.current;try{const value=await api(`research/r10/protocols/${protocolId}/trials/${trial}/media-info`);if(token!==generation.current)return;clock.current={position:0,playing:false,epoch:clock.current.epoch+1,anchor:0,started:0};setElapsed(0);setInfo(value);setStatus('Preparado, sin reproducir');}catch(e){if(token===generation.current){setError(String(e));setStatus('No preparado');}}finally{if(token===generation.current)setBusy(false);}};
 const canPlay=!!info&&(!info.trial.video_enabled||!!video.current&&video.current.readyState>=2)&&(!info.trial.audio_enabled||!!audio.current&&audio.current.readyState>=2);void ready;
 return <section aria-label="Player de ensayo R10"><h3>Reproducción por condición</h3><p>Transporte nominal de un ensayo. No registra exposición ni acredita escucha, participación o sincronización física. No pasa al siguiente automáticamente.</p>
 <label>Ensayo para reproducir R10<select disabled={busy} value={trial} onChange={e=>{generation.current++;stop('Ensayo cambiado');setTrial(e.target.value);setInfo(null);setError('');}}>{trials.map(t=><option key={t.trial_id} value={t.trial_id}>{t.trial_id} · {t.condition}</option>)}</select></label>
 <button disabled={busy||!trial} onClick={()=>void prepare()}>Preparar reproducción R10</button>
 {error&&<p role="alert">{error}</p>}<p role="status">{status}</p>
 {info&&<><p>Condición preparada: {info.trial.condition} · video {info.trial.video_enabled?'habilitado':'deshabilitado'} · audio {info.trial.audio_enabled?'habilitado':'deshabilitado'}.</p>
 {info.trial.video_enabled&&<video ref={video} src={base+'/video'} muted preload="auto" playsInline aria-label="Video del ensayo R10" onCanPlay={()=>setReady(r=>r+1)} onError={()=>{stop('Error de video');setError('No se pudo decodificar el video del ensayo');}} style={{maxWidth:480}}/>}
 {info.trial.audio_enabled&&<audio ref={audio} src={base+'/audio'} preload="auto" aria-label="Audio del ensayo R10" onCanPlay={()=>setReady(r=>r+1)} onError={()=>{stop('Error de audio');setError('No se pudo decodificar el audio del ensayo');}}/>}
 <button disabled={!canPlay||playing} onClick={()=>{const c=clock.current;if(c.position>=info.duration_s){c.position=0;setElapsed(0);c.epoch++;}c.anchor=c.position;c.started=performance.now();c.playing=true;setPlaying(true);setError('');setStatus('Reproduciendo transporte nominal');}}>Reproducir ensayo R10</button>
 <button disabled={!playing} onClick={()=>stop('Pausado')}>Pausar ensayo R10</button>
 <label>Tiempo nominal del ensayo R10<input type="range" min={0} max={info.duration_s} step={.001} value={elapsed} onChange={e=>{stop('Seek en pausa');const c=clock.current;c.position=Number(e.target.value);c.anchor=c.position;c.epoch++;setElapsed(c.position);}}/></label>
 <p>Tiempo nominal: {elapsed.toFixed(3)} / {info.duration_s.toFixed(3)} s. Audio disponible: {info.audio_support_elapsed_s?info.audio_support_elapsed_s.join('–')+' s':'sin soporte'}. Positivo adelanta audio respecto al video.</p>
 </>}
 </section>;
}
