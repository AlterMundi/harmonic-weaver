import {useEffect,useRef,useState} from 'react';
type Data=Record<string,any>;
const defaults={arm:'single',points:512,stride:1,weights:null,phase_offsets_rad:null,scale_x:1,scale_y:1};
export function ModelProjectionPanel({job,api,run}:Data){
 const [settings,setSettings]=useState<Data>({...defaults,arm:job.kind==='mechanism_comparison'?'excited':'single'}),[sample,setSample]=useState(0),[arrays,setArrays]=useState<Data>({}),[text,setText]=useState(''),[result,setResult]=useState<Data|null>(null),[busy,setBusy]=useState(false);
 const canvas=useRef<HTMLCanvasElement>(null),generation=useRef(0);
 const settingsValue=()=>{const value={...settings};for(const [key,text] of Object.entries(arrays))value[key]=JSON.parse(text as string);return value;};
 const paired=job.kind==='mechanism_comparison';
 const refresh=()=>run(async()=>{const current=++generation.current;setBusy(true);try{const value=await api(`research/r05/${job.id}/projection`,{...settingsValue(),start_sample:sample});if(current===generation.current)setResult(value);}finally{if(current===generation.current)setBusy(false);}});
 useEffect(()=>()=>{generation.current++;},[]);
 useEffect(()=>{const el=canvas.current,ctx=el?.getContext('2d');if(!el || !ctx)return;ctx.fillStyle='#041020';ctx.fillRect(0,0,el.width,el.height);if(!result)return;ctx.strokeStyle='#74e6d2';ctx.lineWidth=1;ctx.beginPath();result.points.forEach(([x,y]:number[],i:number)=>{const px=el.width/2+x*el.width/2,py=el.height/2-y*el.height/2;if(i===0)ctx.moveTo(px,py);else ctx.lineTo(px,py);});ctx.stroke();},[result]);
 return <section><h3>Proyección del estado R05 · {job.id}</h3><p>Suma de todas las voces guardadas. X real, Y audible con pesos/fases explícitos; figura teórica del modelo, no cymatic físico ni fase corporal.</p>
  <label>Brazo de proyección R05<select value={settings.arm} onChange={e=>{generation.current++;setBusy(false);setResult(null);setSettings({...settings,arm:e.target.value});}}>{(paired?['excited','mapped']:['single']).map(a=><option key={a}>{a}</option>)}</select></label>
  <label>Muestra inicial de proyección R05<input type="number" min={0} step={1} value={sample} onChange={e=>setSample(+e.target.value)}/></label>
  {['points','stride','scale_x','scale_y'].map(key=><label key={key}>{key} proyección R05<input type="number" step={key.startsWith('scale')?'any':1} value={settings[key]} onChange={e=>setSettings({...settings,[key]:+e.target.value})}/></label>)}
  {['weights','phase_offsets_rad'].map(key=><label key={key}>{key} proyección R05<textarea value={arrays[key] ?? JSON.stringify(settings[key])} onChange={e=>setArrays({...arrays,[key]:e.target.value})}/></label>)}
  <p>null usa todas las voces con peso1/fase0; listas deben tener una entrada por voz. Escala explícita sin normalización; valores fuera del canvas se recortan. Stride es decimación visual sin antialias.</p>
  <button disabled={busy} onClick={refresh}>Leer ventana de proyección R05</button>
  <button onClick={()=>run(async()=>setText(JSON.stringify(await api('research/r05/projection/configuration',{schema_version:1,settings:settingsValue()}),null,2)))}>Exportar proyección R05</button>
  <textarea aria-label="Preset de proyección R05 JSON" value={text} onChange={e=>setText(e.target.value)}/>
  <button onClick={()=>run(async()=>{const value=await api('research/r05/projection/configuration',JSON.parse(text));if(! (paired?['excited','mapped']:['single']).includes(value.settings.arm))throw Error('Brazo de preset incompatible con esta corrida');generation.current++;setBusy(false);setResult(null);setSettings(value.settings);setArrays({});})}>Importar proyección R05</button>
  <p>Preset no incluye corrida, persona, calibración ni muestra inicial. Importar no calcula ni reproduce audio. Inspección manual; seguimiento de reproducción todavía pendiente.</p>
  <canvas ref={canvas} width={600} height={400} aria-label="Figura de todas las voces R05" style={{width:'100%',maxWidth:600}}/>
  {result && <p>Ventana congelada: {result.voices} voces · muestras {result.sample_indices[0]}–{result.sample_indices.at(-1)} · {result.sample_rate} Hz · {result.tail.some((v:boolean)=>v)?'incluye cola del instrumento':'tramo de fuente'} · {result.verification_mode}</p>}
 </section>;
}
