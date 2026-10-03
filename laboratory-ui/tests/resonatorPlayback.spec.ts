import {test,expect} from '@playwright/test';
for(const paired of [false,true])test(`R05 ${paired?'paired':'single'} muted playback follows past samples across pause, seek and loop`,async({page})=>{
 test.skip(!process.env.LAB_R05_NETWORK_URL,'explicit synthetic pose HTTP fixture required');
 const origin=process.env.LAB_R05_NETWORK_URL!;await page.goto(origin);
 const evaluations=await (await page.request.get(`${origin}/api/evaluations`)).json();
 const request:any={selection:{evaluation_id:evaluations[0].id,run_index:0,signal_id:'zone.1.speed',start_s:.2,end_s:2},
  resonators:{sample_rate:8000},excitation:{high:.1,low:.02},render:{tail_s:.1}};
 if(paired)request.mapping={};
 const started=await page.request.post(`${origin}/api/research/r05`,{data:request});
 expect(started.status()).toBe(200);const ident=(await started.json()).id;
 const explore=page.getByRole('button',{name:`Explorar figura R05 ${ident}`,exact:true});
 await expect(explore).toBeVisible({timeout:10000});await explore.click();
 if(paired)await page.getByRole('combobox',{name:/^Brazo de proyección R05/}).selectOption('mapped');
 await page.getByRole('button',{name:'Cargar audio R05',exact:true}).click();
 const audio=page.getByLabel('Reproductor de vista R05',{exact:true});
 await expect(audio).toBeVisible();
 await expect.poll(()=>audio.evaluate((el:HTMLAudioElement)=>el.readyState)).toBeGreaterThanOrEqual(2);
 expect(await audio.evaluate((el:HTMLAudioElement)=>el.paused)).toBe(true);
 await audio.evaluate((el:HTMLAudioElement)=>{el.muted=true;el.currentTime=.5;});
 const sample=page.getByLabel('Muestra inicial de proyección R05',{exact:true});
 await expect(sample).toHaveValue('3488');
 await expect(page.getByText('Ventana congelada:',{exact:false})).toContainText('6 voces');
 const windows:any[]=[];let pending=0;
 page.on('request',r=>{if(r.url()===`${origin}/api/research/r05/${ident}/projection`)pending++;});
 page.on('requestfailed',r=>{if(r.url()===`${origin}/api/research/r05/${ident}/projection`)pending--;});
 page.on('response',async r=>{if(r.url()===`${origin}/api/research/r05/${ident}/projection`){try{windows.push(await r.json());}finally{pending--;}}});
 await audio.evaluate((el:HTMLAudioElement)=>el.play());
 await expect.poll(()=>windows.length).toBeGreaterThanOrEqual(2);
 await audio.evaluate((el:HTMLAudioElement)=>el.pause());
 await expect.poll(()=>pending).toBe(0);
 const position=await audio.evaluate((el:HTMLAudioElement)=>el.currentTime);
 for(const window of windows){
  expect(window.voices).toBe(6);
  expect((window.sample_indices.at(-1)+1)/window.sample_rate).toBeLessThanOrEqual(position+.001);
 }
 const before=windows.length;await page.waitForTimeout(250);expect(windows).toHaveLength(before);
 // Hold a real server response, seek again while paused, then release old data.
 let release!:()=>void,ready!:()=>void;const gate=new Promise<void>(r=>release=r),held=new Promise<void>(r=>ready=r);
 let intercepted=false;const url=`${origin}/api/research/r05/${ident}/projection`;
 await page.route(url,async route=>{if(intercepted){await route.continue();return;}intercepted=true;const response=await route.fetch();ready();await gate;await route.fulfill({response});});
 try{
  await audio.evaluate((el:HTMLAudioElement)=>{el.currentTime=.9;});await held;
  await audio.evaluate((el:HTMLAudioElement)=>{el.currentTime=.1;});
  await expect.poll(()=>audio.evaluate((el:HTMLAudioElement)=>el.seeking)).toBe(false);
  await expect(page.getByText('Ventana congelada:',{exact:false})).toHaveCount(0);
  release();await expect(sample).toHaveValue('288');
 }finally{release();await page.unroute(url);}
 await page.getByRole('checkbox',{name:'Loop de audio R05',exact:true}).check();
 await audio.evaluate((el:HTMLAudioElement)=>{el.currentTime=1.85;});
 await expect.poll(()=>audio.evaluate((el:HTMLAudioElement)=>el.seeking)).toBe(false);
 await audio.evaluate((el:HTMLAudioElement)=>el.play());
 await expect.poll(()=>audio.evaluate((el:HTMLAudioElement)=>el.currentTime)).toBeLessThan(.4);
 await expect.poll(async()=>Number(await sample.inputValue())).toBeLessThan(3200);
 await audio.evaluate((el:HTMLAudioElement)=>el.pause());
 await expect(page.getByRole('alert').filter({hasText:/Error|decode|invalid/})).toHaveCount(0);
});
