import {ExperiencePanel} from '../../src/ExperiencePanel';
import {SpatialPanel} from '../../src/SpatialPanel';
import {createRoot} from 'react-dom/client';
import {RopePanel} from '../../src/RopePanel';
async function api(path:string,body?:unknown){const response=await fetch(`/api/${path}`,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const value=await response.json();if(!response.ok)throw Object.assign(Error(JSON.stringify(value)),{status:response.status});return value;}
createRoot(document.getElementById('root')!).render(<><RopePanel api={api}/><SpatialPanel api={api}/><ExperiencePanel api={api}/></>);
