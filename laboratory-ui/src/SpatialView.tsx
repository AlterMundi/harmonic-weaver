import {useEffect,useState} from 'react';
type Data=Record<string,any>;
export function SpatialView({stream}:{stream:Data}){
 const [axes,setAxes]=useState('0,1');
 const [scale,setScale]=useState(100),[x,setX]=useState(0),[y,setY]=useState(0);
 const [playing,setPlaying]=useState(false),[loop,setLoop]=useState(false),[speed,setSpeed]=useState(1),[gap,setGap]=useState(.1);
 const first=stream.frames[0].source_time_s,last=stream.frames.at(-1).source_time_s;
 const [time,setTime]=useState(first);
 useEffect(()=>{if(!playing)return;let handle=0,previous:number|null=null;const tick=(now:number)=>{if(previous!==null){const delta=(now-previous)*.001*speed;setTime((t:number)=>{let next=t+delta;if(next>=last){if(loop&&last>first)next=first+(next-first)%(last-first);else{next=last;setPlaying(false);}}return next;});}previous=now;handle=requestAnimationFrame(tick);};handle=requestAnimationFrame(tick);return()=>cancelAnimationFrame(handle);},[playing,speed,loop,first,last]);
 let effective=0;for(let i=1;i<stream.frames.length&&stream.frames[i].source_time_s<=time;i++)effective=i;
 const frame=stream.frames[effective];
 const stale=time-frame.source_time_s>gap;

 const [a,b]=axes.split(',').map(Number);
 const supported=(stale?[]:frame.points).filter((p:Data)=>p.position&&p.state!=='missing');
 const projected=supported.map((p:Data)=>({...p,px:200+(p.position[a]-x)*scale,py:150+(p.position[b]-y)*scale}));
 const clipped=projected.filter((p:Data)=>p.px<0||p.px>400||p.py<0||p.py>300).length;
 return <section aria-label="Inspector espacial R09"><h3>Plano de observaciones R09</h3>
 <p>{stream.dimensions}D · {stream.coordinate_frame} · {stream.units}. Proyección de coordenadas; no reconstrucción física verificada.</p>
 <label>Frame espacial R09<input type="range" min={0} max={stream.frames.length-1} step={1} value={effective} onChange={e=>{const i=Number(e.target.value);setTime(stream.frames[i].source_time_s);setPlaying(false);}}/></label>
 <button disabled={last<=first} onClick={()=>{if(time>=last)setTime(first);setPlaying(!playing);}}>{playing?'Pausar observaciones R09':'Reproducir observaciones R09'}</button>
 <label>Loop espacial R09<input type="checkbox" checked={loop} onChange={e=>setLoop(e.target.checked)}/></label>
 <label>Velocidad espacial R09<input type="number" min={.1} max={10} step={.1} value={speed} onChange={e=>setSpeed(Math.max(.1,Math.min(10,Number(e.target.value)||1)))}/></label>
 <label>Gap máximo visible R09<input type="number" min={.001} max={10} step={.01} value={gap} onChange={e=>setGap(Math.max(.001,Math.min(10,Number(e.target.value)||.1)))}/></label>
 <label>Tiempo de reproducción R09<input type="range" min={first} max={last} step={.001} value={time} onChange={e=>{setTime(Number(e.target.value));setPlaying(false);}}/></label>
 <p>Reloj fuente de reproducción: {time.toFixed(3)} s · {stale?'gap: sin puntos vigentes':'observación vigente'}.</p>
 <p>Índice original {frame.index} · tiempo fuente {frame.source_time_s} s · faltantes {frame.points.length-supported.length} · fuera del encuadre {clipped}.</p>
 <label>Proyección R09<select value={axes} onChange={e=>setAxes(e.target.value)}><option value="0,1">XY</option>{stream.dimensions===3&&<><option value="0,2">XZ</option><option value="1,2">YZ</option></>}</select></label>
 <label>Escala de vista R09<input type="number" min={1} max={10000} value={scale} onChange={e=>setScale(Math.max(1,Math.min(10000,Number(e.target.value)||1)))}/></label>
 <label>Centro horizontal R09<input type="number" value={x} onChange={e=>setX(Number(e.target.value)||0)}/></label>
 <label>Centro vertical R09<input type="number" value={y} onChange={e=>setY(Number(e.target.value)||0)}/></label>
 <svg aria-label="Puntos proyectados R09" viewBox="0 0 400 300" style={{width:'100%',maxWidth:500,background:'#20232a'}}>
 {projected.filter((p:Data)=>Number.isFinite(p.px)&&Number.isFinite(p.py)&&p.px>=0&&p.px<=400&&p.py>=0&&p.py<=300).map((p:Data)=><g key={p.label} data-state={p.state}><circle cx={p.px} cy={p.py} r={4} fill={p.state==='observed'?'#66ccff':p.state==='held'?'#ffcc66':'none'} stroke={p.state==='inferred'?'#ee88ff':'none'}/><text x={p.px+5} y={p.py} fill="white" fontSize={10}>{p.label}</text></g>)}
 </svg><p>Azul observado · amarillo sostenido · contorno violeta inferido. Los faltantes no se dibujan ni se unen.</p>
 </section>;
}
