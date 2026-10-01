import {test,expect} from '@playwright/test';
test('R05 float32 listening view decodes and seeks in Chrome without playing',async({page})=>{
 test.skip(!process.env.LAB_R05_NETWORK_URL,'explicit synthetic pose HTTP fixture required');
 const origin=process.env.LAB_R05_NETWORK_URL!;await page.goto(origin);
 const evaluations=await (await page.request.get(`${origin}/api/evaluations`)).json();
 const response=await page.request.post(`${origin}/api/research/r05`,{data:{
  selection:{evaluation_id:evaluations[0].id,run_index:0,signal_id:'zone.1.speed',start_s:.2,end_s:2},
  resonators:{sample_rate:8000},excitation:{high:.1,low:.02},render:{tail_s:.1}}});
 expect(response.status()).toBe(200);const ident=(await response.json()).id;
 await expect.poll(async()=>{
  const jobs=await (await page.request.get(`${origin}/api/research/r05`)).json();
  return jobs.find((j:any)=>j.id===ident)?.status;
 },{timeout:10000}).toBe('complete');
 const decoded=await page.evaluate(async(url)=>{
  const audio=document.createElement('audio');audio.muted=true;audio.preload='auto';
  try{
   await new Promise<void>((resolve,reject)=>{
    const timer=setTimeout(()=>reject(Error('decoder readiness timeout')),5000);
    audio.oncanplay=()=>{clearTimeout(timer);resolve();};
    audio.onerror=()=>{clearTimeout(timer);reject(Error(audio.error?.message || 'decoder error'));};
    audio.src=url;audio.load();
   });
   const duration=audio.duration;
   await new Promise<void>((resolve,reject)=>{
    const timer=setTimeout(()=>reject(Error('seek timeout')),5000);
    audio.onseeked=()=>{clearTimeout(timer);resolve();};audio.currentTime=.5;
   });
   return {duration,position:audio.currentTime,paused:audio.paused};
  }finally{audio.removeAttribute('src');audio.load();}
 },`${origin}/api/research/r05/${ident}/listen/single?gain=1`);
 expect(decoded.duration).toBeCloseTo(1.9,6);expect(decoded.position).toBeCloseTo(.5,6);
 expect(decoded.paused).toBe(true);
});
