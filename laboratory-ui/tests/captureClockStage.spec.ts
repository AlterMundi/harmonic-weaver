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
