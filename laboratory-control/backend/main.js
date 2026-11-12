'use strict';
const http=require('node:http'),fs=require('node:fs'),path=require('node:path'),{spawn}=require('node:child_process'),crypto=require('node:crypto');
const root=__dirname,state=process.env.STATE_DIR;
const assets=fs.existsSync(path.join(root,'index.html'))?root:path.dirname(root);
const csrf=crypto.randomBytes(24).toString('hex');
const pending=new Map();
function config(){const x=JSON.parse(fs.readFileSync(path.join(state,'control.json'),'utf8'));if(!Array.isArray(x.hosts)||x.hosts.length>8)throw Error('Invalid receiving configuration');return x;}
function host(id){return config().hosts.find(x=>x.id===id);}
function invoke(h,request){return new Promise((resolve,reject)=>{
 const args=['-T','-i',path.join(state,h.key),'-o','BatchMode=yes','-o','ConnectTimeout=5','-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile='+path.join(state,h.knownHosts),h.user+'@'+h.address,'lab-control-v1'];
 const child=spawn('/usr/bin/ssh',args,{stdio:['pipe','pipe','pipe']});let out='',err='';
 const timer=setTimeout(()=>{child.kill('SIGTERM');reject(Error('No se pudo confirmar la respuesta del equipo. No se repitió la acción.'));},16000);
 child.stdout.on('data',b=>{out+=b;if(out.length>131072){child.kill();reject(Error('Respuesta inválida del equipo'));}});
 child.stderr.on('data',b=>{err=(err+b).slice(-1024);});
 child.on('error',e=>{clearTimeout(timer);reject(e)});
 child.on('close',code=>{clearTimeout(timer);try{const r=JSON.parse(out);if(!r.ok)throw Error(r.error);resolve(r.data);}catch(e){reject(Error(code?'No se puede conectar con este equipo.':e.message));}});
 child.stdin.end(JSON.stringify(request));
 });}
function json(res,code,data){res.writeHead(code,{'Content-Type':'application/json','Cache-Control':'no-store','X-Content-Type-Options':'nosniff'});res.end(JSON.stringify(data));}
function rawBody(req){return new Promise((resolve,reject)=>{let s='';req.on('data',b=>{s+=b;if(s.length>16384){reject(Error('Solicitud demasiado grande'));req.destroy();}});req.on('end',()=>{try{resolve(JSON.parse(s||'{}'))}catch{reject(Error('Solicitud inválida'))}});});}
const server=http.createServer(async(req,res)=>{
 const u=new URL(req.url,'http://local');
 if(u.pathname==='/health'){res.end('{"ok":true}');return;}
 try{
  if(req.method==='GET'&&u.pathname==='/api/status'){
   const hosts=await Promise.all(config().hosts.map(async h=>{try{return {id:h.id,label:h.label,online:true,...await invoke(h,{op:'status'})};}catch(e){return {id:h.id,label:h.label,online:false,message:e.message,services:[]}}}));
   return json(res,200,{hosts,csrf});
  }
  if(req.method==='POST'&&['/api/start','/api/configure'].includes(u.pathname)){
   if(req.headers['x-lab-csrf']!==csrf)return json(res,403,{error:'Actualizá el panel antes de continuar.'});
   const body=await rawBody(req),h=host(body.host);if(!h)return json(res,404,{error:'Equipo no configurado para este panel.'});
   if(pending.has(h.id))return json(res,409,{error:'Este equipo está respondiendo a otra solicitud.'});
   const request=u.pathname==='/api/start'?{op:'start',service:body.service,id:body.id}:{op:'configure',profile:body.profile};
   const action=invoke(h,request);pending.set(h.id,action);
   try{return json(res,202,{id:h.id,...await action});}finally{pending.delete(h.id)}
  }
  const names={'/':'index.html','/index.html':'index.html','/app.js':'app.js'};
  const file=names[u.pathname];if(req.method!=='GET'||!file)return json(res,404,{error:'No encontrado'});
  res.writeHead(200,{'Content-Type':file.endsWith('.js')?'application/javascript; charset=utf-8':'text/html; charset=utf-8','Cache-Control':'no-store','Content-Security-Policy':"default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'self'"});res.end(fs.readFileSync(path.join(assets,file)));
 }catch(e){json(res,503,{error:e.message||'No se pudo completar la acción.'});}
});
server.listen(Number(process.env.PORT),process.env.HOST);
