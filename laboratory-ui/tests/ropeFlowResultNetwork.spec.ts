import {test,expect} from '@playwright/test';
test('known flow ID survives lost result and reload without another start',async({page})=>{
 test.skip(!process.env.LAB_R08_FLOW_RESULT_URL,'isolated fixture required');
 const origin=process.env.LAB_R08_FLOW_RESULT_URL!;
 const initial=await(await page.request.get(`${origin}/api/research/r08/flow`)).json();
 await page.goto(origin);
 const prepare=async()=>{
  await page.getByLabel('Video de biblioteca R08').selectOption('synthetic');
  await page.getByRole('button',{name:'Preparar anotación R08',exact:true}).click();
  await expect(page.getByText(/Imagen decodificada/)).toBeVisible();
 };
 await prepare();const before=await page.getByLabel('Anotación R08 JSON').inputValue();
 await page.getByLabel('Configuración temporal portable R08').fill('{"frames":3,"settings":{}}');
 await page.getByLabel('Seeds temporales R08').fill('[{"x":0.5,"y":0.5}]');
 let starts=0,interrupted=false;
 page.on('request',r=>{if(r.method()==='POST'&&r.url().endsWith('/api/research/r08/flow'))starts++;});
 await page.route(/\/api\/research\/r08\/flow\/[a-f0-9]{32}\/artifacts\/result.json$/,async route=>{
  if(!interrupted){interrupted=true;const response=await route.fetch();expect(response.ok()).toBeTruthy();return route.abort();}
  return route.continue();
 });
 await page.getByRole('button',{name:'Iniciar corrida temporal R08',exact:true}).click();
 await expect(page.getByText(/Corrida temporal R08: connection_lost/)).toBeVisible();
 const id=(await page.getByText(/Corrida temporal R08: connection_lost/).textContent())!.match(/[a-f0-9]{32}/)![0];
 const receipts=await page.evaluate(()=>Object.keys(sessionStorage).filter(k=>k.startsWith('r08-flow-pending-v1:')).map(k=>JSON.parse(sessionStorage.getItem(k)!)));
 expect(receipts).toHaveLength(1);expect(receipts[0].id).toBe(id);
 await page.reload();await prepare();
 await expect(page.getByText(new RegExp(`Corrida temporal R08: connection_lost.*${id}`))).toBeVisible();
 expect(starts).toBe(1);
 await page.getByRole('button',{name:'Retomar consulta temporal R08',exact:true}).click();
 await expect(page.getByText(new RegExp(`Corrida temporal R08: complete.*${id}`))).toBeVisible();
 expect(starts).toBe(1);
 const jobs=await(await page.request.get(`${origin}/api/research/r08/flow`)).json();
 expect(jobs).toHaveLength(initial.length+1);expect(jobs.some((j:any)=>j.id===id)).toBeTruthy();
 expect(await page.evaluate(()=>Object.keys(sessionStorage).filter(k=>k.startsWith('r08-flow-pending-v1:')))).toHaveLength(0);
 await expect(page.getByTestId('rope-flow-overlay')).toHaveCount(1);
 await expect(page.getByLabel('Anotación R08 JSON')).toHaveValue(before);
});
