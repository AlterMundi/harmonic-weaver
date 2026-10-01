import React from 'react';
import {createRoot} from 'react-dom/client';
import {ResonatorPanel} from '../../src/ResonatorPanel';
async function api(path:string,body?:unknown){
 const response=await fetch(`/api/${path}`,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 const value=await response.json();if(!response.ok)throw Error(JSON.stringify(value));return value;
}
function Harness(){const [error,setError]=React.useState('');return <><p role="alert">{error}</p><ResonatorPanel api={api} run={(fn:()=>Promise<void>)=>fn().catch(e=>setError(String(e)))}/></>;}
createRoot(document.getElementById('root')!).render(<Harness/>);
