import {useState} from 'react';
type Data=Record<string,any>;
export function SpatialView({stream}:{stream:Data}){
 const [index,setIndex]=useState(0),[axes,setAxes]=useState('0,1');
 const [scale,setScale]=useState(100),[x,setX]=useState(0),[y,setY]=useState(0);
 const frame=stream.frames[Math.min(index,stream.frames.length-1)];
 const [a,b]=axes.split(',').map(Number);
 const supported=frame.points.filter((p:Data)=>p.position&&p.state!=='missing');
 const projected=supported.map((p:Data)=>({...p,px:200+(p.position[a]-x)*scale,py:150+(p.position[b]-y)*scale}));
 const clipped=projected.filter((p:Data)=>p.px<0||p.px>400||p.py<0||p.py>300).length;
 return <section aria-label="Inspector espacial R09"><h3>Plano de observaciones R09</h3>
 <p>{stream.dimensions}D · {stream.coordinate_frame} · {stream.units}. Proyección de coordenadas; no reconstrucción física verificada.</p>
 <label>Frame espacial R09<input type="range" min={0} max={stream.frames.length-1} step={1} value={Math.min(index,stream.frames.length-1)} onChange={e=>setIndex(Number(e.target.value))}/></label>
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
