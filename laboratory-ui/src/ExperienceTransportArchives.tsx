import {useEffect,useRef,useState} from 'react';
import {listTransportArchives,saveTransportArchive,readTransportArchive,deleteTransportArchive,type TransportArchive} from './transportArchives';
import {transportDraftKey,transportDraftChanged} from './ExperienceTransportsPanel';
export function ExperienceTransportArchives({draft}:{draft:string|null}){
 const mounted=useRef(true);useEffect(()=>{mounted.current=true;return()=>{mounted.current=false}},[]);
 const [rows,setRows]=useState<TransportArchive[]>([]),[busy,setBusy]=useState(false),[error,setError]=useState(''),[saved,setSaved]=useState('');
 const refresh=async()=>setRows(await listTransportArchives());
 useEffect(()=>{let active=true;void listTransportArchives().then(r=>{if(active)setRows(r)}).catch(e=>{if(active)setError(String(e))});return()=>{active=false}},[]);
 const act=async(fn:()=>Promise<void>)=>{setBusy(true);setError('');try{await fn()}catch(e){setError(String(e))}finally{setBusy(false)}};
 const download=async(id:string)=>{const row=await readTransportArchive(id);const url=URL.createObjectURL(new Blob([row.raw],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=`r10-transport-${id}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
 return <section aria-label="Archivo local de transportes R10"><h4>Borradores conservados en el navegador</h4><p>Guardado opcional en IndexedDB de este navegador/origen. Conserva el JSON exacto, sin video/audio. No abre player ni envía al servidor. Preparar otro ensayo no borra estos archivos. Borrar datos del sitio o cambiar origen/navegador puede impedir recuperarlos; exportar conserva una copia independiente.</p>
 <button disabled={busy||draft===null} onClick={()=>void act(async()=>{const row=await saveTransportArchive(draft!);setSaved(row.id);await refresh()})}>Conservar borrador en navegador R10</button>
 <button disabled={busy} onClick={()=>void act(refresh)}>Actualizar archivo local R10</button>
 {saved&&<p role="status">Borrador conservado en navegador: {saved}</p>}{error&&<p role="alert">{error}</p>}
 {rows.map(row=><div key={row.id}>{row.id} · {row.created_at}
 <button disabled={busy} onClick={()=>void act(async()=>{const before=sessionStorage.getItem(transportDraftKey);const frozen=await readTransportArchive(row.id);if(!mounted.current)return;if(sessionStorage.getItem(transportDraftKey)!==before)throw Error('Borrador actual cambió durante la lectura; restauración descartada');sessionStorage.setItem(transportDraftKey,frozen.raw);window.dispatchEvent(new Event(transportDraftChanged))})}>Restaurar borrador local {row.id}</button>
 <button disabled={busy} onClick={()=>void act(async()=>download(row.id))}>Exportar borrador local {row.id}</button>
 <button disabled={busy} onClick={()=>void act(async()=>{await deleteTransportArchive(row.id);await refresh()})}>Borrar archivo local {row.id}</button>
 </div>)}<p>Restaurar reemplaza sólo el borrador de esta pestaña; no cambia un envío pendiente ni revierte el registro en memoria de un player activo. Guardar en servidor sigue siendo otra acción explícita. Fecha local y checksum no acreditan exposición humana.</p></section>;
}
