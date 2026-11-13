'use strict';
const $=s=>document.getElementById(s);let data=null,chosen='',csrf='',pending=false,editing=false;
const labels={router:'Weaver · ruteos',guitar:'Guitarra',audio:'Spatializer',body:'Weaver · HarMoCAP · Shaper'};
function selected(){return data?.hosts.find(x=>x.id===chosen);}
function notice(s){$('notice').textContent=s;}
function render(){
 const h=selected();$('services').replaceChildren();$('start-all').disabled=pending||!h?.online||!h.services.some(s=>s.enabled&&s.installed);
 if(!h)return;
 if(!h.online)notice('No podemos conectar con '+h.label+'. Verificá que esté encendido y conectado.');
 for(const s of h.services){
  const card=document.createElement('article');card.className='card';
  const title=document.createElement('h2');title.textContent=s.label;card.append(title);
  const state=document.createElement('div');state.className='status'+(s.status==='ready'?' ready':'');
  const starting=h.job&&['queued','starting'].includes(h.job.phase)&&h.job.services.includes(s.id);
  state.textContent=s.status==='ready'?'En marcha':starting?'Iniciando…':!s.installed?'Sin instalar':!s.enabled?'No seleccionado':'Detenido';card.append(state);
  const info=document.createElement('p');info.textContent=({router:'Ruteos entre fuentes e instrumentos. No requiere guitarra, cámara ni salida de audio.',guitar:'Control del mecanismo y ajustes guardados.',audio:'Entrada de guitarra, bandas y espacio sonoro.',body:'Captura corporal, ruteos y síntesis. La cámara se activa desde su interfaz.'})[s.id];card.append(info);
  const result=h.job?.results?.[s.id];if(result?.status==='failed'){const error=document.createElement('p');error.textContent=result.message;card.append(error);}
  const controls=document.createElement('div');controls.className='controls';const start=document.createElement('button');start.textContent='Iniciar';start.disabled=pending||starting||s.status==='ready'||!s.enabled||!s.installed;start.onclick=()=>begin(s.id);controls.append(start);
  const open=document.createElement('a');open.textContent='Abrir interfaz';open.target='_blank';open.rel='noopener';
  if(s.status==='ready'&&s.url)open.href=s.url;else{open.className='disabled';open.setAttribute('aria-disabled','true');}controls.append(open);card.append(controls);$('services').append(card);
 }
 if(!editing&&h.online){
  $('enabled').replaceChildren();for(const id of Object.keys(labels)){const l=document.createElement('label'),c=document.createElement('input');c.type='checkbox';c.dataset.service=id;c.checked=h.profile.services?.[id]??h.services.find(x=>x.id===id)?.enabled??false;l.append(c,' '+labels[id]);$('enabled').append(l);}
  const e=h.profile.environment||{};$('backend').value=e.HARMONIC_LAB_AUDIO_BACKEND||'auto';$('device').value=e.HARMONIC_SHAPER_DEVICE||'';$('input-device').value=e.BEACON_INPUT_DEVICE||e.BEACON_INPUT_PORT||'';$('output-device').value=e.BEACON_OUTPUT_DEVICE||[e.BEACON_OUTPUT_LEFT,e.BEACON_OUTPUT_RIGHT].filter(Boolean).join(' | ');
 }
}
async function refresh(){try{const r=await fetch('api/status');if(!r.ok)throw Error('No se pudo consultar el laboratorio.');data=await r.json();csrf=data.csrf;const old=chosen;chosen=data.hosts.some(h=>h.id===chosen)?chosen:data.hosts[0]?.id||'';$('host').replaceChildren(...data.hosts.map(h=>new Option(h.label,h.id)));$('host').value=chosen;if(!old&&chosen)notice('');render();}catch(e){notice(e.message);$('start-all').disabled=true;}}
async function post(url,body){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json','X-Lab-CSRF':csrf},body:JSON.stringify(body)});const result=await r.json();if(!r.ok)throw Error(result.error);return result;}
async function begin(service){pending=true;render();notice('Solicitando inicio…');try{await post('api/start',{host:chosen,service,id:crypto.randomUUID()});notice('Inicio solicitado. El estado se actualizará cuando cada interfaz esté lista.');await refresh();}catch(e){notice(e.message+' No se repitió la acción.');}finally{pending=false;render();}}
$('start-all').onclick=()=>begin('all');$('refresh').onclick=refresh;$('host').onchange=()=>{chosen=$('host').value;editing=false;notice('');render();};$('profile').oninput=()=>{editing=true;};
$('profile').onsubmit=async e=>{e.preventDefault();const h=selected();if(!h)return;const profile=structuredClone(h.profile),env=profile.environment||{};profile.services=Object.fromEntries([...document.querySelectorAll('[data-service]')].map(x=>[x.dataset.service,x.checked]));env.HARMONIC_LAB_AUDIO_BACKEND=$('backend').value;env.HARMONIC_SHAPER_DEVICE=$('device').value;
 const input=$('input-device').value,output=$('output-device').value;
 if(h.profile.environment?.BEACON_INPUT_DEVICE!==undefined){env.BEACON_INPUT_DEVICE=input;env.BEACON_OUTPUT_DEVICE=output;}
 else{if(input)env.BEACON_INPUT_PORT=input;const pair=output.split(' | ');if(output&&pair.length!==2){notice('La salida JACK necesita dos puertos separados por |.');return;}if(output){env.BEACON_OUTPUT_LEFT=pair[0];env.BEACON_OUTPUT_RIGHT=pair[1];}}
 profile.environment=env;try{await post('api/configure',{host:chosen,profile});editing=false;notice('Configuración guardada para los próximos inicios.');await refresh();}catch(e){notice(e.message);}};
refresh();setInterval(()=>{if(!pending&&!document.hidden)refresh();},4000);
