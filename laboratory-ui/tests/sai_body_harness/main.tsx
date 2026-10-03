import React from 'react';import {createRoot} from 'react-dom/client';import {SaiBodyFourierPanel} from '../../src/SaiBodyFourierPanel';
async function api(path:string,body?:unknown){const r=await fetch('/api/'+path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const v=await r.json();if(!r.ok)throw Error(JSON.stringify(v));return v;}
createRoot(document.getElementById('root')!).render(<SaiBodyFourierPanel api={api}/>);
