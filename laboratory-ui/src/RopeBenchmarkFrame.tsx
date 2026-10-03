import {useEffect,useState,type ReactNode} from 'react';

type Props={api:any,source:string,sha256:string,index:number,width:number,height:number,children:ReactNode};
// Parent keys this component by reference, run and source. A new context starts hidden.
export function RopeBenchmarkFrame({api,source,sha256,index,width,height,children}:Props){
 const [shown,setShown]=useState(false),[image,setImage]=useState(''),[ready,setReady]=useState(false),[error,setError]=useState('');
 useEffect(()=>{
  let active=true,id='';setImage('');setReady(false);setError('');
  if(shown)void(async()=>{
   try{
    let status=await api('research/r08/reads',{media_id:source,frame_index:index,sha256});id=status.id;
    if(!active){await api(`research/r08/reads/${id}/cancel`,{});return;}
    while(active&&status.status==='running'){
     await new Promise(resolve=>setTimeout(resolve,100));if(!active)return;
     status=await api(`research/r08/reads/${id}`);
    }
    if(!active)return;
    if(status.status==='complete')setImage(`/api/research/r08/reads/${id}/result`);
    else if(status.status!=='cancelled')setError(status.error||'Falló la lectura del frame original');
   }catch(e){if(active)setError(String(e));}
  })();
  return()=>{active=false;if(id)void api(`research/r08/reads/${id}/cancel`,{}).catch(()=>{});};
 },[api,source,sha256,index,shown]);
 return <>
 <button disabled={!source} onClick={()=>setShown(!shown)}>{shown?'Ocultar frame original R08':'Mostrar frame original R08'}</button>
 {shown&&!ready&&!error&&<p role="status">Leyendo frame original R08 {index}; no usa seek aproximado del navegador.</p>}
 {error&&<p role="alert">Frame original no disponible: {error}. El esquema sigue disponible.</p>}
 <svg aria-label="Semillas y extremos en frame inicial R08" viewBox={`0 0 ${width} ${height}`} style={{width:'100%',maxWidth:480,background:'#20232a'}}>
 {shown&&image&&!error&&<image aria-label="Frame original de la corrida R08" href={image} width={width} height={height} onLoad={()=>setReady(true)} onError={()=>{setReady(false);setError('No se pudo mostrar el PNG decodificado');}}/>}
 {children}
 </svg>
 {shown&&ready&&!error&&<p>Frame original R08 {index} verificado por hash y decodificado por índice. Semillas y etiquetas superpuestas en ese mismo frame; no selecciona correspondencias.</p>}
 </>;
}
