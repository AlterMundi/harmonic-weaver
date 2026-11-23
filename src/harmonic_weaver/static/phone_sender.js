// Latest-only persistent sensor transport. No HTTP acknowledgement per sample.
const $=id=>document.getElementById(id),query=new URLSearchParams(location.search);
if(['A','B'].includes(query.get('device')))$('device').value=query.get('device');
let socket=null,timer=null,wake=null,active=false,starting=false,generation=0,stream='',sequence=0;
let zeroYaw=null,zeroPitch=null,lastMotion=-Infinity,lastOrientation=-Infinity;
let yaw=0,pitch=0,roll=0,ax=0,ay=0,az=0,role='A';
const wrap=v=>((v+540)%360)-180;
function orient(event){if(![event.alpha,event.beta,event.gamma].every(Number.isFinite)){lastOrientation=-Infinity;return;}zeroYaw??=event.alpha;zeroPitch??=event.beta;yaw=wrap(event.alpha-zeroYaw);pitch=event.beta-zeroPitch;roll=event.gamma;lastOrientation=performance.now();}
function motion(event){const a=event.acceleration;if(!a||![a.x,a.y,a.z].every(Number.isFinite)){lastMotion=-Infinity;return;}({x:ax,y:ay,z:az}=a);lastMotion=performance.now();}
function reference(){zeroYaw=zeroPitch=null;lastOrientation=-Infinity;$('status').textContent='Tomando referencia en la próxima lectura…';}
function stop(message='Envío detenido'){
 generation++;starting=false;const old=socket;socket=null;active=false;clearInterval(timer);timer=null;
 window.removeEventListener('deviceorientation',orient);window.removeEventListener('devicemotion',motion);
 if(old){if(old.readyState===WebSocket.OPEN)old.send(JSON.stringify({device:role,stream,stop:true}));old.close();}
 if(wake){void wake.release().catch(()=>{});wake=null;}
 $('start').disabled=false;
 $('stop').disabled=true;$('reference').disabled=true;$('device').disabled=false;$('status').textContent=message;$('readings').textContent='Sin lecturas';
}
function send(){
 if(!active||socket?.readyState!==WebSocket.OPEN)return;
 const now=performance.now();if(now-lastMotion>750||now-lastOrientation>750){$('status').textContent='Esperando movimiento y orientación recientes…';return;}
 if(socket.bufferedAmount>2048){$('status').textContent='Conexión demorada · descartando lecturas anteriores';return;}
 socket.send(JSON.stringify({device:role,stream,seq:sequence++,yaw,pitch,roll,ax,ay,az}));
 $('status').textContent='Enviando a Weaver';$('readings').textContent='Giro: '+yaw.toFixed(1)+'°\nInclinación: '+pitch.toFixed(1)+'°\nAceleración: '+Math.hypot(ax,ay,az).toFixed(2)+' m/s²';
 $('phone-needle').style.transform='rotate('+yaw+'deg)';$('phone-halo').style.transform='scale('+(1+Math.min(Math.hypot(ax,ay,az)/3,1)*.2)+')';
}
$('start').onclick=async()=>{
 if(active||starting)return;starting=true;const attempt=++generation;$('start').disabled=true;
 try{
  if(!isSecureContext)throw Error('Abrí el enlace HTTPS del receptor local.');
  if(!window.DeviceMotionEvent||!window.DeviceOrientationEvent)throw Error('Este navegador no ofrece movimiento y orientación.');
  const requests=[DeviceMotionEvent,DeviceOrientationEvent].filter(type=>typeof type.requestPermission==='function').map(type=>type.requestPermission());
  if((await Promise.all(requests)).some(value=>value!=='granted'))throw Error('Falta autorizar los sensores.');
  if(attempt!==generation||document.visibilityState==='hidden')return;
  role=$('device').value;stream=crypto.randomUUID();sequence=0;reference();lastMotion=-Infinity;
  const url=new URL('./imu',location.href);url.protocol=location.protocol==='https:'?'wss:':'ws:';
  const current=new WebSocket(url);socket=current;
  await new Promise((resolve,reject)=>{const deadline=setTimeout(()=>reject(Error('No se pudo conectar con el receptor.')),4000);current.onopen=()=>{clearTimeout(deadline);resolve();};current.onerror=()=>{clearTimeout(deadline);reject(Error('No se pudo conectar con el receptor.'));};});
  if(socket!==current||attempt!==generation)throw Error('Conexión detenida.');
  active=true;current.onclose=event=>{if(socket===current)stop(event.reason||'Conexión cerrada. Tocá Iniciar para volver.');};current.onerror=()=>{if(socket===current)stop('Conexión interrumpida. Tocá Iniciar para volver.');};
  window.addEventListener('deviceorientation',orient);window.addEventListener('devicemotion',motion);
  $('stop').disabled=false;$('reference').disabled=false;$('device').disabled=true;timer=setInterval(send,40);$('status').textContent='Esperando las primeras lecturas…';
  try{const lease=await navigator.wakeLock.request('screen');if(!active||attempt!==generation){await lease.release();}else{wake=lease;wake.addEventListener('release',()=>{$('wake-warning').hidden=false;});}}catch{if(attempt===generation)$('wake-warning').hidden=false;}
 }catch(error){if(attempt===generation)stop(error.message);}finally{if(attempt===generation){starting=false;$('start').disabled=active;}}
};
$('stop').onclick=()=>stop();$('reference').onclick=reference;
window.addEventListener('pagehide',()=>stop());document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')stop('Envío detenido al salir de la página.');});
