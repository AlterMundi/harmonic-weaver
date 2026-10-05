import {test,expect} from '@playwright/test';

test('Stage derivative clock and gap persist through save and reload',async({page})=>{
  test.skip(!process.env.LAB_CAPTURE_UI_URL,'isolated synthetic Stage fixture required');
  const url=process.env.LAB_CAPTURE_UI_URL!;
  const errors:string[]=[];page.on('pageerror',e=>errors.push(String(e)));
  await page.goto(url);
  const card=page.locator('[data-route-id="capture-derivative"]');
  await card.getByRole('button',{name:'Edit chain'}).click();
  const clock=page.getByRole('combobox',{name:/^Derivative clock/});
  await expect(clock).toHaveValue('engine');
  await clock.selectOption('source_capture');
  await page.getByLabel('Maximum capture gap (ms)').fill('350');
  await page.getByRole('button',{name:'Save chain'}).click();
  const saved=async()=>{
    const r=await page.request.get(url+'/fixture/state');return r.json();
  };
  await expect.poll(async()=> (await saved()).scenes[0].routes[0].transforms[0].clock).toBe('source_capture');
  expect((await saved()).scenes[0].routes[0].transforms[0].max_gap_ms).toBe(350);
  await page.reload();
  await card.getByRole('button',{name:'Edit chain'}).click();
  await expect(clock).toHaveValue('source_capture');
  await expect(page.getByLabel('Maximum capture gap (ms)')).toHaveValue('350');
  await clock.selectOption('engine');
  await expect(page.getByLabel('Maximum engine delta (ms)')).toHaveValue('1000');
  await page.getByRole('button',{name:'Save chain'}).click();
  await expect.poll(async()=> (await saved()).scenes[0].routes[0].transforms[0].clock).toBe('engine');
  expect(errors).toEqual([]);
});

test('Stage smoothing capture clock and gap survive save and reload',async({page})=>{
 test.skip(!process.env.LAB_CAPTURE_UI_URL,'isolated synthetic Stage fixture required');
 const url=process.env.LAB_CAPTURE_UI_URL!;
 const errors:string[]=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(url);
 const card=page.locator('[data-route-id="capture-smoothing"]');
 await card.getByRole('button',{name:'Edit chain'}).click();
 const clock=page.getByRole('combobox',{name:/^Smoothing clock/});
 await expect(clock).toHaveValue('engine');
 await clock.selectOption('source_capture');
 await page.getByLabel('Maximum capture gap (ms)').fill('400');
 await page.getByRole('button',{name:'Save chain'}).click();
 const saved=async()=> (await page.request.get(url+'/fixture/state')).json();
 await expect.poll(async()=> (await saved()).scenes[0].routes.find((r:any)=>r.route_id==='capture-smoothing').transforms[0].clock).toBe('source_capture');
 await page.reload();
 await card.getByRole('button',{name:'Edit chain'}).click();
 await expect(clock).toHaveValue('source_capture');
 await expect(page.getByLabel('Maximum capture gap (ms)')).toHaveValue('400');
 await clock.selectOption('engine');
 await expect(page.getByLabel('Maximum capture gap (ms)')).not.toBeVisible();
 await page.getByRole('button',{name:'Save chain'}).click();
 await expect.poll(async()=> (await saved()).scenes[0].routes.find((r:any)=>r.route_id==='capture-smoothing').transforms[0].clock).toBe('engine');
 expect(errors).toEqual([]);
});

for(const kind of ['phase','slew'])test(`Stage ${kind} capture clock and rate controls persist`,async({page})=>{
 test.skip(!process.env.LAB_CAPTURE_UI_URL,'isolated synthetic Stage fixture required');
 const url=process.env.LAB_CAPTURE_UI_URL!;
 const errors:string[]=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(url);
 const card=page.locator(`[data-route-id="capture-${kind}"]`);
 await card.getByRole('button',{name:'Edit chain'}).click();
 const clock=page.getByRole('combobox',{name:kind==='phase'?/^Phase clock/:/^Slew clock/});
 await expect(clock).toHaveValue('engine');await clock.selectOption('source_capture');
 await page.getByLabel('Maximum capture gap (ms)').fill('300');
 if(kind==='phase'){
  await expect(page.getByLabel('Limit phase rate')).not.toBeChecked();
  await page.getByLabel('Limit phase rate').check();
  await page.getByLabel('Maximum phase rate (deg/s)').fill('120');
 }else await page.getByLabel('Maximum slew rate (/s)').fill('3.5');
 await page.getByRole('button',{name:'Save chain'}).click();
 const saved=async()=> (await page.request.get(url+'/fixture/state')).json();
 await expect.poll(async()=> (await saved()).scenes[0].routes.find((r:any)=>r.route_id===`capture-${kind}`).transforms[0].clock).toBe('source_capture');
 await page.reload();await card.getByRole('button',{name:'Edit chain'}).click();
 await expect(clock).toHaveValue('source_capture');
 await expect(page.getByLabel('Maximum capture gap (ms)')).toHaveValue('300');
 if(kind==='phase'){
  await expect(page.getByLabel('Maximum phase rate (deg/s)')).toHaveValue('120');
  await page.getByLabel('Limit phase rate').uncheck();
  await expect(page.getByLabel('Maximum phase rate (deg/s)')).not.toBeVisible();
 }else await expect(page.getByLabel('Maximum slew rate (/s)')).toHaveValue('3.5');
 await clock.selectOption('engine');await expect(page.getByLabel('Maximum engine delta (ms)')).toHaveValue('100');
 await page.getByRole('button',{name:'Save chain'}).click();
 await expect.poll(async()=> (await saved()).scenes[0].routes.find((r:any)=>r.route_id===`capture-${kind}`).transforms[0].clock).toBe('engine');
 if(kind==='phase')expect((await saved()).scenes[0].routes.find((r:any)=>r.route_id==='capture-phase').transforms[0]).not.toHaveProperty('max_rate');
 expect(errors).toEqual([]);
});

for(const [kind,title] of [['beat','Beat'],['peak','Peak'],['dwell','Dwell']])test(`Stage ${kind} event clock and controls persist`,async({page})=>{
 test.skip(!process.env.LAB_CAPTURE_UI_URL,'isolated synthetic Stage fixture required');
 const url=process.env.LAB_CAPTURE_UI_URL!;
 const errors:string[]=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(url);
 const card=page.locator(`[data-route-id="capture-${kind}"]`);
 await card.getByRole('button',{name:'Edit chain'}).click();
 const clock=page.getByRole('combobox',{name:new RegExp(`^${title} clock`)});
 await expect(clock).toHaveValue('engine');await clock.selectOption('source_capture');
 await page.getByLabel('Maximum capture gap (ms)').fill('300');
 if(kind==='beat'){
  await expect(page.getByLabel('Fixed envelope decay')).not.toBeChecked();
  await page.getByLabel('Fixed envelope decay').check();
  await page.getByLabel('Envelope decay (ms)').fill('350');
  await page.getByLabel('Beat threshold').fill('0.4');
 }else if(kind==='peak')await page.getByLabel('Peak refractory (ms)').fill('120');
 else await page.getByLabel('Minimum dwell commit interval (ms)').fill('150');
 await page.getByRole('button',{name:'Save chain'}).click();
 const saved=async()=> (await page.request.get(url+'/fixture/state')).json();
 await expect.poll(async()=> (await saved()).scenes[0].routes.find((r:any)=>r.route_id===`capture-${kind}`).transforms[0].clock).toBe('source_capture');
 await page.reload();await card.getByRole('button',{name:'Edit chain'}).click();
 await expect(clock).toHaveValue('source_capture');
 await expect(page.getByLabel('Maximum capture gap (ms)')).toHaveValue('300');
 if(kind==='beat'){
  await expect(page.getByLabel('Envelope decay (ms)')).toHaveValue('350');
  await expect(page.getByLabel('Beat threshold')).toHaveValue('0.4');
  await page.getByLabel('Fixed envelope decay').uncheck();
  await expect(page.getByLabel('Decay / beat interval')).toHaveValue('0.3');
 }else if(kind==='peak')await expect(page.getByLabel('Peak refractory (ms)')).toHaveValue('120');
 else await expect(page.getByLabel('Minimum dwell commit interval (ms)')).toHaveValue('150');
 await clock.selectOption('engine');await expect(page.getByLabel('Maximum capture gap (ms)')).not.toBeVisible();
 await page.getByRole('button',{name:'Save chain'}).click();
 await expect.poll(async()=> (await saved()).scenes[0].routes.find((r:any)=>r.route_id===`capture-${kind}`).transforms[0].clock).toBe('engine');
 if(kind==='beat')expect((await saved()).scenes[0].routes.find((r:any)=>r.route_id==='capture-beat').transforms[0]).not.toHaveProperty('tau_ms');
 expect(errors).toEqual([]);
});
