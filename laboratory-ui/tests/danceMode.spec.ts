import {test,expect} from '@playwright/test';
import {setupRecording} from './recordingFixture';

async function setupDance(page:any,{portrait=false,fallback=false,missingAPI=false}={}){
 if(fallback||missingAPI)await page.addInitScript(({missingAPI}:any)=>{Object.defineProperty(HTMLElement.prototype,'requestFullscreen',{configurable:true,value:missingAPI?undefined:function(){return Promise.reject(Error('Synthetic fullscreen refusal'));}});},{missingAPI});
 const fx=await setupRecording(page),width=portrait?720:1280,height=portrait?1280:720,aspect=width/height,c=aspect/2;
 const points:any={0:[c,.12],5:[c-.10,.26],6:[c+.10,.26],7:[c-.16,.43],8:[c+.16,.43],9:[c-.18,.60],10:[c+.18,.60],11:[c-.07,.53],12:[c+.07,.53],13:[c-.08,.73],14:[c+.08,.73],15:[c-.09,.92],16:[c+.09,.92]};
 fx.state.motion_frame={width,height,persons:[{person_id:'one',joints:Object.entries(points).map(([i,p])=>({index:Number(i),position:p,state:'observed',confidence:1}))}]};
 fx.state.shaper={telemetry_valid:true};fx.state.voice_frame={sample_index:1,audio_health:{engine_id:'synthetic-audio'},voices:[{frequency_hz:40.4,gain:.25,phase_rad:0,harmonic_n:1},{frequency_hz:80.8,gain:.2,phase_rad:1,harmonic_n:2}]};
 const body=`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}"><defs><linearGradient id="g" x2="0" y2="1"><stop stop-color="#183449"/><stop offset="1" stop-color="#091722"/></linearGradient></defs><rect width="100%" height="100%" fill="url(#g)"/><circle cx="${c*height}" cy="${.15*height}" r="${.055*height}" fill="#326075"/><path d="M ${(c-.1)*height} ${.26*height} L ${(c+.1)*height} ${.26*height} L ${(c+.07)*height} ${.53*height} L ${(c-.07)*height} ${.53*height}Z" fill="#234957"/></svg>`;
 await page.route('**/api/camera/preview?**',(r:any)=>r.fulfill({contentType:'image/svg+xml',body}));
 await expect.poll(()=>page.getByAltText('Cámara en vivo').evaluate((el:any)=>el.naturalWidth)).toBe(width);
 return fx;
}
const enter=(page:any)=>page.getByRole('button',{name:'Bailar en pantalla completa',exact:true});
const exit=(page:any)=>page.getByRole('button',{name:'Salir del modo baile',exact:true});
async function checkLayout(page:any){
 const boxes=await page.evaluate(()=>{
  const box=(s:string)=>{const b=document.querySelector(s)!.getBoundingClientRect();return {x:b.x,y:b.y,width:b.width,height:b.height,right:b.right,bottom:b.bottom};};
  return {stage:box('.stage'),source:box('.source-view'),video:box('.video-wrap'),figure:box('.figure-view'),canvas:box('.figure-view canvas'),width:innerWidth,height:innerHeight};
 });
 expect(boxes.stage.x).toBeCloseTo(0,1);expect(boxes.stage.y).toBeCloseTo(0,1);expect(boxes.stage.width).toBeCloseTo(boxes.width,1);expect(boxes.stage.height).toBeCloseTo(boxes.height,1);
 expect(boxes.video.width).toBeCloseTo(boxes.width,1);expect(boxes.video.height).toBeCloseTo(boxes.height,1);expect(boxes.figure.right).toBeLessThanOrEqual(boxes.width-8);expect(boxes.figure.bottom).toBeLessThanOrEqual(boxes.height-8);expect(boxes.figure.x).toBeGreaterThan(boxes.width/2);expect(boxes.figure.y).toBeGreaterThan(boxes.height/2);expect(boxes.figure.width).toBeLessThan(boxes.width*.4);expect(boxes.canvas.width).toBeGreaterThan(100);expect(boxes.canvas.height).toBeGreaterThan(100);
 await expect(page.getByRole('region',{name:'Opciones del instrumento',exact:true})).not.toBeVisible();await expect(page.getByRole('region',{name:'Volumen del instrumento'})).not.toBeVisible();await expect(page.locator('.source-view .stage-label')).not.toBeVisible();await expect(page.locator('.source-view .transport')).not.toBeVisible();await expect(exit(page)).toBeVisible();
}

test('native fullscreen keeps the mounted source, skeleton, single figure and active recording',async({page})=>{
 const fx=await setupDance(page);await page.getByRole('button',{name:'Performance',exact:true}).click();fx.inventory.current={id:'human-take',status:'recording'};
 const source=await page.getByAltText('Cámara en vivo').elementHandle(),canvas=await page.locator('.figure-view canvas').elementHandle(),preset=JSON.stringify(fx.state.preset);
 await enter(page).click();await expect.poll(()=>page.evaluate(()=>document.fullscreenElement===document.querySelector('.stage'))).toBe(true);await checkLayout(page);
 expect(await page.getByAltText('Cámara en vivo').evaluate((el:any,old:any)=>el===old,source)).toBe(true);expect(await page.locator('.figure-view canvas').evaluate((el:any,old:any)=>el===old,canvas)).toBe(true);expect(await page.locator('.figure-view canvas').count()).toBe(1);await expect(page.locator('.skeleton')).toBeVisible();
 expect(fx.calls).toEqual([]);expect(fx.inventory.current.status).toBe('recording');expect(JSON.stringify(fx.state.preset)).toBe(preset);
 if(process.env.TUTORIAL_QA_DIR)await page.screenshot({path:process.env.TUTORIAL_QA_DIR+'/dance-landscape.png'});
 await exit(page).click();await expect.poll(()=>page.evaluate(()=>document.fullscreenElement)).toBe(null);await expect(enter(page)).toBeFocused();await expect(page.getByRole('button',{name:'Performance',exact:true})).toHaveAttribute('aria-pressed','true');expect(fx.calls).toEqual([]);expect(fx.errors).toEqual([]);
});

test('native Escape returns to the ordinary set without source or sound writes',async({page})=>{
 const fx=await setupDance(page);await enter(page).click();await expect(page.locator('main')).toHaveClass(/dance-mode/);await page.keyboard.press('Escape');await expect(page.locator('main')).not.toHaveClass(/dance-mode/);await expect(enter(page)).toBeFocused();expect(fx.calls).toEqual([]);expect(fx.errors).toEqual([]);
});

test('rejected fullscreen uses the full-tab view and Escape exits',async({page})=>{
 const fx=await setupDance(page,{fallback:true});await enter(page).click();await expect(page.getByRole('status')).toContainText('Modo baile en esta pestaña');await checkLayout(page);expect(await page.evaluate(()=>document.fullscreenElement)).toBe(null);await page.keyboard.press('Escape');await expect(enter(page)).toBeVisible();await expect(enter(page)).toBeFocused();expect(fx.calls).toEqual([]);
});

test('missing fullscreen API still supports portrait dancing and returns preset visibility settings',async({page})=>{
 const fx=await setupDance(page,{portrait:true,missingAPI:true});fx.state.preset.visual.show_skeleton=false;await expect(page.locator('.skeleton')).not.toBeVisible();const before=JSON.stringify(fx.state.preset);await enter(page).click();await checkLayout(page);await expect(page.locator('.skeleton')).toBeVisible();await expect(page.locator('.skeleton')).toHaveAttribute('viewBox','0 0 0.5625 1');expect(await page.getByAltText('Cámara en vivo').evaluate((el:any)=>getComputedStyle(el).objectFit)).toBe('contain');
 if(process.env.TUTORIAL_QA_DIR)await page.screenshot({path:process.env.TUTORIAL_QA_DIR+'/dance-portrait.png'});
 await exit(page).click();await expect(page.locator('.skeleton')).not.toBeVisible();expect(JSON.stringify(fx.state.preset)).toBe(before);expect(fx.calls).toEqual([]);
});

test('portrait dance view fits a narrow screen and exposes an accessible exit',async({page})=>{
 await page.setViewportSize({width:390,height:844});const fx=await setupDance(page,{portrait:true,fallback:true});await enter(page).click();await checkLayout(page);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);expect(await exit(page).evaluate((el:any)=>parseFloat(getComputedStyle(el).fontSize))).toBeGreaterThanOrEqual(16);expect((await exit(page).boundingBox())!.height).toBeGreaterThanOrEqual(44);
 if(process.env.TUTORIAL_QA_DIR)await page.screenshot({path:process.env.TUTORIAL_QA_DIR+'/dance-narrow.png'});
 await exit(page).click();await expect(enter(page)).toBeVisible();expect(fx.errors).toEqual([]);
});

test('source loss remains visible inside the dance view without an automatic retry',async({page})=>{
 const fx=await setupDance(page,{fallback:true});await enter(page).click();fx.state.source.camera.status='error';await expect(page.getByRole('status')).toContainText('La cámara se detuvo');await expect(exit(page)).toBeVisible();expect(fx.calls).toEqual([]);await exit(page).click();
});

test('dance is available only after choosing a source',async({page})=>{
 await setupRecording(page,{camera:false});await expect(enter(page)).toBeDisabled();expect(await page.evaluate(()=>document.fullscreenElement)).toBe(null);
});

test('the existing harmonic canvas repaints at portrait corner size',async({page})=>{
 const fx=await setupDance(page,{portrait:true,missingAPI:true});const voices=JSON.stringify(fx.state.voice_frame.voices);await enter(page).click();const canvas=page.locator('.figure-view canvas');
 await expect.poll(()=>canvas.evaluate((el:any)=>{const gl=el.getContext('webgl');if(!gl||gl.isContextLost())return 0;const data=new Uint8Array(el.width*el.height*4);gl.readPixels(0,0,el.width,el.height,gl.RGBA,gl.UNSIGNED_BYTE,data);let bright=0;for(let i=0;i<data.length;i+=4)if(data[i+1]>70||data[i+2]>70)bright++;return bright;})).toBeGreaterThan(50);
 await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));
 if(process.env.TUTORIAL_QA_DIR)await page.screenshot({path:process.env.TUTORIAL_QA_DIR+'/dance-portrait-rendered.png'});
 await exit(page).click();await expect.poll(()=>canvas.evaluate((el:any)=>el.width)).toBeGreaterThan(400);expect(JSON.stringify(fx.state.voice_frame.voices)).toBe(voices);expect(fx.calls).toEqual([]);
});
