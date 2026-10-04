import {useEffect,useState,useRef} from 'react';
type Data=Record<string,any>;
export function CaptureProfiles({api,getDraft,onApply,disabled}:Data){
 const [rows,setRows]=useState<Data[]>([]),[ident,setIdent]=useState(''),[name,setName]=useState('Captura y exportación');
 const blockedRef=useRef(disabled);blockedRef.current=disabled;
 const [text,setText]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState(''),[status,setStatus]=useState('');
 useEffect(()=>{let live=true;void api('capture-profiles').then((value:Data[])=>{if(live)setRows(value)}).catch((e:unknown)=>{if(live)setError(String(e))});return()=>{live=false}},[api]);
 const act=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');setStatus('');try{await fn()}catch(e){setError(String(e))}finally{setBusy(false)}};
 const draft=()=>({schema_version:1,...(ident?{id:ident}:{}),name,...getDraft()});
 const display=(p:Data)=>{setIdent(p.id);setName(p.name);setText(JSON.stringify(p,null,2));};
 const apply=(p:Data)=>{if(blockedRef.current)throw Error('Esperá a que termine la captura o exportación para cargar controles.');onApply(p);display(p);setStatus('Configuración cargada en los controles; no inició captura ni exportación.');};
 const blocked=disabled||busy;
 return <div aria-label="Configuraciones de captura">
  <h3>Configuraciones de captura y exportación</h3>
  <label>Configuración guardada<select aria-label="Configuración guardada" value={ident} disabled={blocked} onChange={e=>setIdent(e.target.value)}><option value="">Nueva configuración</option>{ident&&!rows.some(p=>p.id===ident)&&<option value={ident}>{name} (sin guardar)</option>}{rows.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
  <label>Nombre de configuración de captura<input value={name} disabled={blocked} onChange={e=>setName(e.target.value)}/></label>
  <button disabled={blocked} onClick={()=>void act(async()=>{const p=await api('capture-profiles',draft());display(p);setRows(await api('capture-profiles'));setStatus('Configuración guardada.');})}>Guardar configuración de captura</button>
  <button disabled={blocked||!rows.some(p=>p.id===ident)} onClick={()=>void act(async()=>apply(await api(`capture-profiles/${ident}`)))}>Cargar configuración de captura</button>
  <button disabled={blocked} onClick={()=>void act(async()=>{const p=await api('capture-profiles/validate',draft());display(p);setStatus('JSON preparado para copiar o descargar.');})}>Preparar JSON de captura</button>
  <label>Configuración de captura JSON<textarea aria-label="Configuración de captura JSON" value={text} disabled={blocked} onChange={e=>setText(e.target.value)}/></label>
  <button disabled={blocked||!text} onClick={()=>void act(async()=>apply(await api('capture-profiles/validate',JSON.parse(text))))}>Aplicar JSON de captura</button>
  <button disabled={blocked||!text} onClick={()=>void act(async()=>{const p=await api('capture-profiles/validate',JSON.parse(text));const url=URL.createObjectURL(new Blob([JSON.stringify(p,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='capture-profile.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);})}>Descargar configuración de captura</button>
  <small>Guarda sólo ajustes: sin fuente, persona ni calibración. Cargar no activa la grabación de cámara; Iniciar captura sigue siendo una acción explícita. No cambia el instrumento.</small>
  {error&&<p role="alert">{error}</p>}{status&&<p role="status">{status}</p>}
 </div>;
}
