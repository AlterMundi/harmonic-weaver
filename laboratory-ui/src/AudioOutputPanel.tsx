import {useState} from 'react';
type Data=Record<string,any>;
export function AudioOutputPanel({api,playing}:Data){
 const [settings,setSettings]=useState<Data|null>(null),[device,setDevice]=useState(''),[rate,setRate]=useState(48000),[buffer,setBuffer]=useState(1024),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const load=(value:Data)=>{setSettings(value);setDevice(value.device==null?'':String(value.device));setRate(value.requested_sample_rate);setBuffer(value.block_size);};
 const act=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');try{await fn();}catch(e){setError(String(e));}finally{setBusy(false);}};
 const current=settings?.devices?.find((d:Data)=>String(d.id)===String(settings.device)||d.name===settings.device)?.name??settings?.device??'predeterminada';
 const known=settings?.devices?.some((d:Data)=>String(d.id)===device);
 return <details><summary>Salida y buffer de audio</summary>
 <button disabled={busy} onClick={()=>void act(async()=>load(await api('audio/output')))}>Consultar salidas de Shaper</button>
 {error&&<p role="alert">{error}</p>}
 {settings&&<><p>Salida actual: {current} · efectiva {settings.sample_rate} Hz / {settings.block_size} muestras.</p>
 <fieldset disabled={busy}><label>Salida Shaper<select aria-label="Salida Shaper" value={device} onChange={e=>setDevice(e.target.value)}><option value="">Predeterminada del backend</option>{device&&!known&&<option value={device}>{device}</option>}{settings.devices.map((d:Data)=><option key={d.id} value={String(d.id)}>{d.name} · {d.hostapi}</option>)}</select></label>
 <label>Frecuencia pedida (Hz)<input aria-label="Frecuencia pedida (Hz)" type="number" min={8000} max={192000} step={1} value={rate} onChange={e=>setRate(+e.target.value)}/></label>
 <label>Buffer Shaper<select aria-label="Buffer Shaper" value={buffer} onChange={e=>setBuffer(+e.target.value)}>{[128,256,512,1024,2048].map(v=><option key={v} value={v}>{v} muestras</option>)}</select></label>
 <button disabled={playing} onClick={()=>void act(async()=>load(await api('audio/output',{expected_revision:settings.revision,device:device===''?null:/^\d+$/.test(device)?+device:device,sample_rate:rate,block_size:buffer})))}>Aplicar salida y buffer</button></fieldset>
 {playing&&<p>Pausá la fuente para cambiar la salida.</p>}
 <p>Aplicar reabre sólo el stream de audio; requiere liberar voces y detener capturas. JACK usa la frecuencia de su servidor: pedir 96 kHz no cambia PipeWire globalmente. Estos ajustes son de la sesión; el próximo arranque usa los flags del comando.</p></>}
 </details>;
}
