import {test,expect} from '@playwright/test';
test('lost flow start response retries exact frozen request without duplicate work',async({page})=>{
 test.skip(!process.env.LAB_R08_FLOW_START_URL,'fresh isolated fixture required');
 const origin=process.env.LAB_R08_FLOW_START_URL!;await page.goto(origin);
 await page.getByLabel('Video de biblioteca R08').selectOption('synthetic');
 await page.getByRole('button',{name:'Preparar anotación R08',exact:true}).click();
 await expect(page.getByText(/Imagen decodificada/)).toBeVisible();
 const before=await page.getByLabel('Anotación R08 JSON').inputValue();
 await page.getByLabel('Configuración temporal portable R08').fill('{"frames":3,"settings":{}}');
 await page.getByLabel('Seeds temporales R08').fill('[{"x":0.5,"y":0.5}]');
 const bodies:any[]=[];let originalId='';
 await page.route(/\/api\/research\/r08\/flow$/,async route=>{
  if(route.request().method()!=='POST')return route.continue();
  bodies.push(route.request().postDataJSON());
  if(bodies.length===1){
   const response=await route.fetch();expect(response.ok()).toBeTruthy();originalId=(await response.json()).id;
   return route.abort(); // Server accepted; browser never receives its response.
  }
  return route.continue();
 });
 await page.getByRole('button',{name:'Iniciar corrida temporal R08',exact:true}).click();
 await expect(page.getByText('Corrida temporal R08: start_unknown',{exact:true})).toBeVisible();
 await expect(page.getByRole('button',{name:'Iniciar corrida temporal R08',exact:true})).toBeDisabled();
 await expect(page.getByLabel('Configuración temporal portable R08')).toBeDisabled();
 await page.getByRole('button',{name:'Reintentar mismo inicio temporal R08',exact:true}).click();
 await expect(page.getByText(new RegExp(`Corrida temporal R08: complete.*${originalId}`))).toBeVisible();
 expect(bodies).toHaveLength(2);expect(bodies[1]).toEqual(bodies[0]);
 expect(bodies[0].idempotency_key).toMatch(/^[a-f0-9]{32}$/);
 const jobs=await(await page.request.get(`${origin}/api/research/r08/flow`)).json();
 expect(jobs).toHaveLength(1);expect(jobs[0].id).toBe(originalId);
 await expect(page.getByLabel('Anotación R08 JSON')).toHaveValue(before);
 await page.getByLabel('Seeds temporales R08').fill('[]');
 await page.getByRole('button',{name:'Iniciar corrida temporal R08',exact:true}).click();
 await expect(page.getByText('Corrida temporal R08: failed',{exact:true})).toBeVisible();
 await expect(page.getByLabel('Seeds temporales R08')).toBeEnabled();
});
