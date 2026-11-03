import {test,expect} from '@playwright/test';
import fs from 'node:fs/promises';
import {installLocalNetwork} from '../src/face/localNetwork';
test('worker guard rejects external fetch/XHR and still loads same-origin model metadata',async({page})=>{
 const external:string[]=[];page.on('request',r=>{if(!r.url().startsWith('http://127.0.0.1:')&&!r.url().startsWith('blob:'))external.push(r.url());});
 await page.goto('./?mode=face');
 const result=await page.evaluate(async source=>{
  const origin=location.origin;
  const code=`(${source})(${JSON.stringify(origin)});(async()=>{const result={fetch:'',xhr:'',local:false};try{await fetch('https://example.invalid/face-probe')}catch(e){result.fetch=e.name}try{new XMLHttpRequest().open('POST','https://example.invalid/face-probe')}catch(e){result.xhr=e.name}result.local=(await fetch(${JSON.stringify(origin+'/face-assets/manifest.json')})).ok;postMessage(result)})()`;
  const url=URL.createObjectURL(new Blob([code],{type:'text/javascript'}));
  try{return await new Promise((resolve,reject)=>{const worker=new Worker(url);const timer=setTimeout(()=>{worker.terminate();reject(Error('Probe timed out'));},10000);worker.onmessage=e=>{clearTimeout(timer);worker.terminate();resolve(e.data);};worker.onerror=e=>{clearTimeout(timer);worker.terminate();reject(Error(e.message));};});}
  finally{URL.revokeObjectURL(url);}
 },installLocalNetwork.toString());
 expect(result).toEqual({fetch:'SecurityError',xhr:'SecurityError',local:true});expect(external).toEqual([]);
});
test('actual face worker keeps tracking beyond the SDK diagnostic flush without external traffic',async({page,context})=>{
 test.skip(!process.env.FACE_QA_SCREENS,'Requires the existing private vendor portrait fixture.');test.setTimeout(120000);
 const external:string[]=[],errors:string[]=[];context.on('request',r=>{if(!r.url().startsWith('http://127.0.0.1:')&&!r.url().startsWith('blob:'))external.push(r.url());});page.on('pageerror',e=>errors.push(String(e)));
 await page.route('**/qa-portrait.jpg',async route=>route.fulfill({contentType:'image/jpeg',body:await fs.readFile(process.env.FACE_QA_SCREENS+'/vendor-portrait.jpg')}));
 await page.addInitScript(()=>{
  Object.defineProperty(navigator,'mediaDevices',{value:{getUserMedia:async()=>{const image=await createImageBitmap(await(await fetch('/qa-portrait.jpg')).blob());const canvas=document.createElement('canvas');canvas.width=image.width;canvas.height=image.height;const x=canvas.getContext('2d')!;const timer=setInterval(()=>x.drawImage(image,0,0),100);const stream=canvas.captureStream(10);stream.getTracks()[0].addEventListener('ended',()=>clearInterval(timer));return stream;},enumerateDevices:async()=>[{kind:'videoinput',deviceId:'vendor',label:'Vendor fixture · QA'}]}});
  const Native=window.Worker;(window as any).__faceTimes=[];window.Worker=class extends Native{constructor(...args:any[]){super(args[0],args[1]);this.addEventListener('message',e=>{if(e.data.type==='frame'&&e.data.faces.length===1)(window as any).__faceTimes.push(performance.now());});}} as any;
 });
 await page.goto('./?mode=face');await page.getByRole('button',{name:'Mi cámara',exact:true}).click();await page.getByText('Soy mayor de18 y autorizo usar mi cámara en esta pestaña.',{exact:true}).click();await page.getByRole('button',{name:'Conectar cámara',exact:true}).click();
 await expect(page.getByText('Rostro en seguimiento · medidas proyectadas',{exact:true})).toBeVisible({timeout:55000});
 const start=await page.evaluate(()=>performance.now());
 await page.waitForFunction(start=>((window as any).__faceTimes.at(-1)||0)>start+61000,start,{timeout:70000});
 await expect(page.getByLabel('Puntos y arcos medidos del rostro')).toBeVisible();expect(errors).toEqual([]);expect(external).toEqual([]);
 await fs.writeFile(process.env.FACE_QA_SCREENS+'/long-worker-check.json',JSON.stringify({external,errors,validFrames:await page.evaluate(()=>(window as any).__faceTimes.length),coveredMs:await page.evaluate(start=>performance.now()-start,start)},null,2));
 await page.getByRole('button',{name:'Apagar cámara',exact:true}).click();
});
