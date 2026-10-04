import {test,expect} from '@playwright/test';
test('frozen bodily source uses real paired PCM video and observed pose without retracking',async({page})=>{
 test.skip(!process.env.LAB_R05_BODY_URL,'explicit production UI fixture with read-only frozen body EVAL required');
 test.setTimeout(120000);const origin=process.env.LAB_R05_BODY_URL!;
 const evaluations=await(await page.request.get(`${origin}/api/evaluations`)).json();expect(evaluations).toHaveLength(1);const eid=evaluations[0].id;
 const report=await(await page.request.get(`${origin}/api/evaluations/${eid}/report`)).json();
 const frozen=report.manifest.request.sources[report.manifest.runs[0].source_index];
 const start=Number(process.env.LAB_R05_BODY_START||'10'),end=Number(process.env.LAB_R05_BODY_END||'16');
 expect(start).toBeGreaterThanOrEqual(frozen.start_s);expect(end).toBeLessThanOrEqual(frozen.end_s);
 const errors:string[]=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(origin);await page.getByRole('button',{name:'Investigación',exact:true}).click();
 const request={selection:{evaluation_id:eid,run_index:0,signal_id:'zone.1.speed',start_s:start,end_s:end},resonators:{sample_rate:8000},excitation:{mode:'positive_delta',positive_delta_min:0},render:{tail_s:.5},mapping:{}};
 const started=await page.request.post(`${origin}/api/research/r05`,{data:request});expect(started.ok(),await started.text()).toBeTruthy();const id=(await started.json()).id;
 const explore=page.getByRole('button',{name:`Explorar figura R05 ${id}`,exact:true});await expect(explore).toBeVisible({timeout:60000});await explore.click();
 const source=await(await page.request.get(`${origin}/api/research/r05/${id}/source-info`)).json();expect(source.person_id).toBe(frozen.person_id);expect(source.source_start_s).toBe(start);expect(source.source_end_s).toBe(end);
 const poseResponse=await page.request.get(`${origin}/api/research/r05/${id}/source-pose`);expect(poseResponse.ok()).toBeTruthy();const pose=await poseResponse.json();expect(pose.rows.length).toBeGreaterThan(1);
 const observed=pose.rows.find((r:any)=>r.time_s>start+.1&&r.time_s<end-.5&&r.joints.some((j:any)=>j.state==='observed'));expect(observed).toBeTruthy();const sampleElapsed=observed.time_s+.01-start;
 await page.getByRole('button',{name:'Mostrar video de origen R05',exact:true}).click();await page.getByRole('button',{name:'Cargar pose congelada R05',exact:true}).click();
 const video=page.getByLabel('Video de origen R05',{exact:true});await expect.poll(()=>video.evaluate((v:HTMLVideoElement)=>v.readyState)).toBeGreaterThanOrEqual(2);
 await expect.poll(()=>video.evaluate((v:HTMLVideoElement)=>v.currentTime)).toBeCloseTo(start,1);
 const arm=page.getByRole('combobox',{name:/^Brazo de proyección R05/});
 for(const value of ['excited','mapped']){
  await arm.selectOption(value);await page.getByRole('button',{name:'Cargar audio R05',exact:true}).click();
  const audio=page.getByLabel('Reproductor de vista R05',{exact:true});await expect.poll(()=>audio.evaluate((a:HTMLAudioElement)=>a.readyState)).toBeGreaterThanOrEqual(2);
  await audio.evaluate((a:HTMLAudioElement,t)=>{a.muted=true;a.currentTime=t},sampleElapsed);await expect.poll(()=>video.evaluate((v:HTMLVideoElement)=>v.currentTime)).toBeCloseTo(start+sampleElapsed,1);
  await expect(page.getByText('Ventana congelada:',{exact:false})).toContainText('6 voces');
  const diagnostic=page.getByLabel('Diagnóstico pose R05',{exact:true});await expect(diagnostic).toContainText(/\d+\.\d{3} s/);
  await expect(page.getByLabel('Pose congelada R05',{exact:true})).toBeVisible();
  const poseTime=Number((await diagnostic.innerText()).match(/([0-9]+\.[0-9]{3}) s/)![1]);expect(poseTime).toBeLessThanOrEqual(await video.evaluate((v:HTMLVideoElement)=>v.currentTime)+.001);
  expect(await page.getByLabel('Pose congelada R05',{exact:true}).locator('circle').count()).toBeGreaterThan(0);
  const rendered=await video.evaluate((v:HTMLVideoElement)=>v.getVideoPlaybackQuality().totalVideoFrames);
  await audio.evaluate((a:HTMLAudioElement)=>a.play());await expect.poll(()=>video.evaluate((v:HTMLVideoElement)=>v.getVideoPlaybackQuality().totalVideoFrames)).toBeGreaterThan(rendered+3);
  await audio.evaluate((a:HTMLAudioElement)=>a.pause());await expect.poll(()=>video.evaluate((v:HTMLVideoElement)=>v.paused)).toBe(true);
  const elapsed=await audio.evaluate((a:HTMLAudioElement)=>a.currentTime);await expect.poll(()=>video.evaluate((v:HTMLVideoElement)=>v.currentTime)).toBeCloseTo(start+elapsed,1);
  await audio.evaluate((a:HTMLAudioElement)=>{a.currentTime=.1});await expect.poll(()=>video.evaluate((v:HTMLVideoElement)=>v.currentTime)).toBeCloseTo(start+.1,1);
  await page.getByLabel('Desfase video/audio R05 (s)',{exact:true}).fill('.25');await expect.poll(()=>video.evaluate((v:HTMLVideoElement)=>v.currentTime)).toBeCloseTo(start+.35,1);
  await page.getByLabel('Desfase video/audio R05 (s)',{exact:true}).fill('0');
  await audio.evaluate((a:HTMLAudioElement)=>{a.currentTime=a.duration-.1});await expect.poll(()=>video.evaluate((v:HTMLVideoElement)=>v.currentTime)).toBeCloseTo(end,1);expect(await video.evaluate((v:HTMLVideoElement)=>v.paused)).toBe(true);
 }
 expect(errors).toEqual([]);
 const controls=await(await page.request.get(`${origin}/api/fixture/controls`)).json();expect(controls.mode).toBe('control_targets_only');
 const result=await(await page.request.get(`${origin}/api/research/r05/${id}/artifacts/result.json`)).json();expect(result.metrics.excited_resonators.common_observed.frames).toBe(result.metrics.amplitude_mapping.common_observed.frames);expect(result.metrics.amplitude_mapping.common_observed.frames).toBeGreaterThan(0);
 // Fixture evaluation mutators are disabled; the source artifacts remain in their original directory.
 const blocked=await page.request.post(`${origin}/api/evaluations/${eid}/repeat`,{data:{}});expect(blocked.status()).toBe(422);
});
