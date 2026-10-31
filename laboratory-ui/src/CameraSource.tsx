import {useCallback,useEffect,useRef,useState} from 'react';
type Data=Record<string,any>;
const preference='weaver-lab-camera-id';
const savedChoice=()=>{try{return localStorage.getItem(preference)||'';}catch{return '';}};
const rotationPreference='weaver-lab-camera-rotations';
const rotations=[0,90,180,270];
const savedRotation=(key:string)=>{try{const value=JSON.parse(localStorage.getItem(rotationPreference)||'{}')[key];return rotations.includes(value)?value:0;}catch{return 0;}};
const orientationLabel=(value:number)=>value===90?'Vertical · giro a la derecha':value===270?'Vertical · giro a la izquierda':value===180?'Horizontal · invertida':'Horizontal';

/** Choose hardware connected to the running instrument, without guessing numeric indices. */
export function CameraSource({api,state,perception,locked=false}:{api:any;state:Data;perception:Data|null;locked?:boolean}){
 const [rows,setRows]=useState<Data[]>([]),[selected,setSelected]=useState(savedChoice);
 const [supported,setSupported]=useState(true),[confirmed,setConfirmed]=useState(false),[loading,setLoading]=useState(false);
 const [busy,setBusy]=useState(false),[error,setError]=useState(''),[fetchError,setFetchError]=useState(''),[notice,setNotice]=useState(''),[manual,setManual]=useState(0);
 const live=useRef(false),reading=useRef(false),acting=useRef(false);
 const [rotation,setRotation]=useState(0);
 const refresh=useCallback(async()=>{
  if(reading.current)return;reading.current=true;setLoading(true);
  try{
   const result=await api('cameras');if(!Array.isArray(result?.cameras)||result.scope!=='laboratory_host')throw Error('El laboratorio no pudo consultar las cámaras.');
   if(live.current){setRows(result.cameras);setSupported(result.supported);setConfirmed(true);setFetchError('');}
  }catch{if(live.current){setConfirmed(false);setFetchError('No se pudo actualizar la lista. Pulsá Actualizar cámaras; no cambiamos la cámara activa.');}}
  finally{reading.current=false;if(live.current)setLoading(false);}
 },[api]);
 useEffect(()=>{
  live.current=true;void refresh();const timer=setInterval(()=>{if(!document.hidden)void refresh();},4000);
  const visible=()=>{if(!document.hidden)void refresh();};document.addEventListener('visibilitychange',visible);window.addEventListener('focus',visible);
  return()=>{live.current=false;clearInterval(timer);document.removeEventListener('visibilitychange',visible);window.removeEventListener('focus',visible);};
 },[refresh]);
 const cam=state.source?.kind==='camera'?state.source.camera:null;
 const chosen=rows.find(row=>row.id===selected),active=rows.find(row=>cam?.device_id?row.id===cam.device_id:cam?.index!==undefined&&row.index===cam.index);
 useEffect(()=>{
  if(selected||!confirmed)return;const available=rows.filter(row=>row.available);
  if(active?.id)setSelected(active.id);else if(available.length===1)setSelected(available[0].id);
 },[rows,selected,confirmed,active?.id]);
 const remember=(id:string)=>{setSelected(id);setNotice('');try{localStorage.setItem(preference,id);}catch{setNotice('Esta elección no se pudo guardar; sigue disponible mientras la página esté abierta.');}};
 const running=cam&&['warming','ready'].includes(cam.status)&&!(cam.sample_age_ms>2000);
 const sameCamera=running&&(cam.device_id?cam.device_id===selected:chosen&&cam.index===chosen.index);
 const rotationKey=selected||`index:${manual}`;
 const selectedActive=cam&&(cam.device_id?cam.device_id===selected:!selected&&cam.index===manual);
 useEffect(()=>{
  const applied=selectedActive&&rotations.includes(cam.rotation_degrees)?cam.rotation_degrees:null;
  setRotation(applied??savedRotation(rotationKey));
  if(applied!==null)try{const saved=JSON.parse(localStorage.getItem(rotationPreference)||'{}');localStorage.setItem(rotationPreference,JSON.stringify({...saved,[rotationKey]:applied}));}catch{/* Runtime truth still stays visible. */}
 },[rotationKey,selectedActive,cam?.stream_id]);
 const chooseRotation=(value:number)=>{
  setRotation(value);setNotice('');
  try{const saved=JSON.parse(localStorage.getItem(rotationPreference)||'{}');localStorage.setItem(rotationPreference,JSON.stringify({...saved,[rotationKey]:value}));}
  catch{setNotice('El giro elegido se usará en esta sesión, pero no se pudo guardar en este navegador.');}
 };
 const rotationChanged=!!sameCamera&&rotation!==(cam.rotation_degrees??0);
 const cameraSettings=()=>({...perception,...(selectedActive?cam.perception||{}:{}),camera_rotation_degrees:rotation});
 const act=async(action:()=>Promise<any>)=>{
  if(acting.current||locked)return;acting.current=true;setBusy(true);setError('');setNotice('');
  try{await action();}catch{setError('No se confirmó la conexión. Revisá el estado de la cámara y Actualizar cámaras antes de volver a intentarlo. No reiniciamos automáticamente.');}
  finally{acting.current=false;if(live.current)setBusy(false);}
 };
 return <fieldset aria-label="Conectar cámara">
  <legend>Cámara USB o webcam</legend>
  <p>Elegí una de las cámaras conectadas al equipo que está ejecutando HarmoCap.</p>
  <label>Cámara disponible<select aria-label="Cámara disponible" value={selected} disabled={busy||locked} onChange={e=>remember(e.target.value)}>
   <option value="">Elegí una cámara…</option>
   {selected&&!chosen&&<option value={selected}>Cámara guardada · desconectada o sin consultar</option>}
   {rows.map(row=><option key={row.id} value={row.id} disabled={!row.available}>{row.label} · cámara {row.index}{row.available?'':' · sin permiso'}</option>)}
  </select></label>
  <div role="group" aria-label="Orientación de la cámara" className="camera-orientation">
   <p><b>Orientación de la cámara</b></p>
   <div className="actions">
    <button disabled={busy||locked} aria-pressed={rotation%180===0} onClick={()=>chooseRotation(0)}>Horizontal</button>
    <button disabled={busy||locked} aria-pressed={rotation%180===90} onClick={()=>chooseRotation(rotation%180===90?rotation:90)}>Vertical</button>
    <button disabled={busy||locked} onClick={()=>chooseRotation((rotation+180)%360)}>Dar vuelta</button>
   </div>
   <p>Elegida: {orientationLabel(rotation)}. {sameCamera?`En uso: ${orientationLabel(cam.rotation_degrees??0)}.`:''}</p>
   <p>Para una cámara montada de costado, elegí Vertical. Si quedás cabeza abajo, tocá Dar vuelta. {rotationChanged?'Pulsá Aplicar orientación para usar este giro.':sameCamera?'Esta orientación ya está activa.':'Pulsá Usar esta cámara para conectar con la orientación elegida.'}</p>
  </div>
  <div className="actions">
   <button disabled={loading} onClick={()=>void refresh()}>{loading?'Buscando cámaras…':'Actualizar cámaras'}</button>
   <button disabled={busy||locked||!perception||!confirmed||!chosen?.available||!!sameCamera&&!rotationChanged} onClick={()=>void act(async()=>{remember(selected);await api('sources/camera',{device_id:selected,perception:cameraSettings()});setNotice('Conexión solicitada. Esperá a ver la imagen y el seguimiento.');})}>{rotationChanged?'Aplicar orientación':sameCamera?'Esta cámara está en uso':'Usar esta cámara'}</button>
   <button disabled={busy||locked||!state.source?.kind} onClick={()=>void act(()=>api('sources/close',{}))}>Cerrar fuente / apagar cámara</button>
  </div>
  {confirmed&&supported&&!rows.length&&<p>No se detectaron cámaras. Conectá la cámara USB y pulsá Actualizar cámaras. Si ya está conectada, revisá sus permisos en el sistema.</p>}
  {selected&&!chosen&&confirmed&&<p>La cámara guardada no aparece conectada. No cambiamos a otra cámara: reconectala o elegí otra de la lista.</p>}
  {!supported&&confirmed&&<p>La detección por nombre está disponible en Linux. En este sistema podés usar el índice manual de abajo.</p>}
  {chosen?.reason&&<p>{chosen.reason}</p>}
  {cam&&<p role="status">{cam.status==='warming'?'Preparando la cámara y el seguimiento…':cam.status==='error'?'La cámara no está enviando imágenes. Revisá el cable o si otra aplicación la está usando.':cam.sample_age_ms>2000?'La imagen no se está actualizando. Revisá la conexión antes de volver a conectar.':cam.status==='ready'?'Cámara en vivo'+(active?` · ${active.label}`:''):'Cámara detenida.'}</p>}
  {cam?.status==='ready'&&!(cam.sample_age_ms>2000)&&!state.motion_frame?.persons?.length&&<p>Hay imagen, pero todavía no se detectó un cuerpo. Ponete dentro del encuadre para que aparezcan las líneas.</p>}
  {locked&&<p>Detené la grabación antes de cambiar o apagar la cámara.</p>}
  {notice&&<p role="status">{notice}</p>}{(error||fetchError)&&<p role="alert">{error||fetchError}</p>}
  <details><summary>Si abrís la web desde otra computadora</summary><p>La cámara y el seguimiento funcionan en el equipo que ejecuta el laboratorio. Para usar la webcam de otra computadora, ejecutá HarmoCap en esa computadora. El guardado de copias sí pertenece al navegador donde abriste la web.</p></details>
  <details><summary>Elegir cámara por índice · avanzado</summary>
   <p>Usá esta opción si la detección por nombre no está disponible. El índice puede cambiar al reconectar dispositivos.</p>
   <label>Índice de cámara<input aria-label="Índice de cámara" type="number" min="0" max="32" value={manual} onChange={e=>setManual(e.target.valueAsNumber)}/></label>
   <button disabled={busy||locked||!perception||!Number.isInteger(manual)||manual<0||manual>32} onClick={()=>void act(()=>api('sources/camera',{index:manual,perception:{...perception,camera_rotation_degrees:rotation}}))}>Usar índice manual</button>
  </details>
 </fieldset>;
}
