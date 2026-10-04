import {test,expect} from '@playwright/test';
import {join} from 'node:path';

for(const bitrate of [64,192,320])test(`Chrome decodes synthetic AAC preview ${bitrate} without output devices`,async({page})=>{
 test.skip(!process.env.LAB_CAPTURE_PREVIEW_TIMING_ROOT,'explicit synthetic rendered stimulus required');
 const path=join(process.env.LAB_CAPTURE_PREVIEW_TIMING_ROOT!,`bitrate-${bitrate}-offset-0-repeat-0`,'preview.mp4');
 const origin='http://127.0.0.1:18968';
 await page.route(`${origin}/control`,r=>r.fulfill({contentType:'text/html',body:'<video muted preload="auto" src="/timing-preview.mp4"></video><canvas width="160" height="120"></canvas>'}));
 await page.route(`${origin}/timing-preview.mp4`,r=>r.fulfill({path,contentType:'video/mp4'}));
 await page.goto(`${origin}/control`);
 const result=await page.evaluate(async()=>{
  const context=new OfflineAudioContext(2,48000,48000);
  const buffer=await context.decodeAudioData(await(await fetch('/timing-preview.mp4')).arrayBuffer());
  const first=Math.round(.45*buffer.sampleRate),last=Math.round(.55*buffer.sampleRate);
  let total=0,weighted=0,peak=0,peakIndex=0;
  for(let i=0;i<buffer.length;i++){
   let energy=0;for(let c=0;c<buffer.numberOfChannels;c++)energy+=buffer.getChannelData(c)[i]**2;
   if(energy>peak){peak=energy;peakIndex=i;}
   if(i>=first&&i<last){total+=energy;weighted+=i/buffer.sampleRate*energy;}
  }
  const video=document.querySelector('video')!;video.pause();
  if(video.readyState<2)await new Promise<void>((resolve,reject)=>{video.addEventListener('loadeddata',()=>resolve(),{once:true});video.addEventListener('error',()=>reject(Error('Video decode failed')),{once:true});});
  const canvas=document.querySelector('canvas')!,drawing=canvas.getContext('2d')!;
  const presented=await new Promise<{dark:boolean;flashTime:number|null}>((resolve,reject)=>{
   let dark=false,flashTime:number|null=null;
   const timeout=setTimeout(()=>{video.pause();reject(Error('No presented stimulus frames'));},3000);
   const frame=(_now:number,metadata:VideoFrameCallbackMetadata)=>{
    drawing.drawImage(video,0,0,160,120);const pixels=drawing.getImageData(0,0,160,120).data;
    let sum=0;for(let i=0;i<pixels.length;i+=4)sum+=pixels[i]+pixels[i+1]+pixels[i+2];const mean=sum/(160*120*3);
    if(mean<20)dark=true;if(mean>200&&flashTime===null)flashTime=metadata.mediaTime;
    if(metadata.mediaTime>=.65){clearTimeout(timeout);video.pause();resolve({dark,flashTime});}
    else video.requestVideoFrameCallback(frame);
   };
   video.requestVideoFrameCallback(frame);void video.play().catch(reject);
  });
  return {centroid:weighted/total,peak:peakIndex/buffer.sampleRate,sampleRate:buffer.sampleRate,
          ...presented,muted:video.muted,paused:video.paused};
 });
 expect(result.sampleRate).toBe(48000);expect(Math.abs(result.centroid-(24000+15.5)/48000)).toBeLessThan(.002);expect(Math.abs(result.peak-.5)).toBeLessThan(.002);
 expect(result.dark).toBe(true);expect(result.flashTime).not.toBeNull();expect(result.flashTime!).toBeCloseTo(.5,3);expect(result.muted&&result.paused).toBe(true);
});
