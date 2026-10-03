import {useEffect,useRef,useState} from 'react';
type Data=Record<string,any>;
export function EvaluationProfiles({api,getDraft,onApply}:Data){
 const [rows,setRows]=useState<Data[]>([]),[id,setId]=useState(''),[name,setName]=useState('Procesamiento de comparación');
 const [text,setText]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState(''),[status,setStatus]=useState('');
 const mounted=useRef(false);
 const currentDraft=useRef('');currentDraft.current=JSON.stringify(getDraft());
 useEffect(()=>{mounted.current=true;void api('evaluation-profiles').then((value:Data[])=>{if(mounted.current)setRows(value)}).catch((e:unknown)=>{if(mounted.current)setError(String(e))});return()=>{mounted.current=false}},[api]);
 const act=async(work:()=>Promise<void>)=>{setBusy(true);setError('');setStatus('');try{await work()}catch(e){if(mounted.current)setError(String(e))}finally{if(mounted.current)setBusy(false)}};
 const draft=()=>({schema_version:1,...(id?{id}:{}),name,...getDraft()});
 const display=(p:Data)=>{setId(p.id);setName(p.name);setText(JSON.stringify(p,null,2))};
 const apply=(p:Data)=>{if(!mounted.current)return;onApply(p);display(p);setStatus('Ajustes cargados; selecciones intactas, sin iniciar ni modificar corridas.')};
 const load=async(work:()=>Promise<Data>)=>{const before=currentDraft.current;const profile=await work();if(!mounted.current)return;if(before!==currentDraft.current)throw Error('Los ajustes cambiaron durante la carga; volvé a aplicar el perfil si querés reemplazarlos.');apply(profile)};
 return <section aria-label="Perfiles de procesamiento de comparación">
  <h3>Guardar ajustes de procesamiento</h3>
  <label>Perfil de procesamiento<select aria-label="Perfil de procesamiento" value={id} disabled={busy} onChange={e=>setId(e.target.value)}><option value="">Nuevo perfil</option>{id&&!rows.some(p=>p.id===id)&&<option value={id}>{name} (sin guardar)</option>}{rows.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
  <label>Nombre del perfil de procesamiento<input value={name} disabled={busy} onChange={e=>setName(e.target.value)}/></label>
  <button disabled={busy} onClick={()=>void act(async()=>{const p=await api('evaluation-profiles',draft());if(!mounted.current)return;display(p);setRows(await api('evaluation-profiles'));setStatus('Perfil guardado localmente.')})}>Guardar perfil de comparación</button>
  <button disabled={busy||!rows.some(p=>p.id===id)} onClick={()=>void act(()=>load(()=>api(`evaluation-profiles/${id}`)))}>Cargar perfil de comparación</button>
  <button disabled={busy} onClick={()=>void act(async()=>{const p=await api('evaluation-profiles/validate',draft());if(mounted.current){display(p);setStatus('JSON preparado.')}})}>Preparar JSON de comparación</button>
  <label>Perfil de comparación JSON<textarea aria-label="Perfil de comparación JSON" disabled={busy} value={text} onChange={e=>setText(e.target.value)}/></label>
  <button disabled={busy||!text} onClick={()=>void act(()=>load(()=>api('evaluation-profiles/validate',JSON.parse(text))))}>Aplicar JSON de comparación</button>
  <button disabled={busy||!text} onClick={()=>void act(async()=>{const p=await api('evaluation-profiles/validate',JSON.parse(text));if(!mounted.current)return;const url=URL.createObjectURL(new Blob([JSON.stringify(p,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='evaluation-profile.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)})}>Descargar perfil de comparación</button>
  <p>Sólo frecuencia de control, historia previa, presupuesto por tanda y render PCM. Sin presets, fuentes, personas, calibración ni identidad de motor/entorno. Aplicar prepara futuras corridas; no cambia una corrida congelada ni el instrumento.</p>
  {error&&<p role="alert">{error}</p>}{status&&<p role="status">{status}</p>}
 </section>;
}
