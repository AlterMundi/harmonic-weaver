import {createRoot} from 'react-dom/client';
import {MembranePanel} from '../../src/MembranePanel';
import {MembraneTransferPanel} from '../../src/MembraneTransferPanel';
import {MembraneControlsPanel} from '../../src/MembraneControlsPanel';
async function api(path:string,body?:unknown){
 const response=await fetch(`/api/${path}`,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 const value=await response.json();if(!response.ok)throw Error(JSON.stringify(value));return value;
}
createRoot(document.getElementById('root')!).render(<><MembranePanel api={api}/><MembraneTransferPanel api={api}/><MembraneControlsPanel api={api}/></>);
