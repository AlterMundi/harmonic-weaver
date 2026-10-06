import {test,expect} from '@playwright/test';

for(const oldFails of [false,true])test('late preset inventory '+(oldFails?'failure':'snapshot')+' cannot hide a newly saved preset',async({page})=>{
 test.skip(!process.env.LAB_INVENTORY_ORDER_URL,'isolated production laboratory required');
 const origin=process.env.LAB_INVENTORY_ORDER_URL!,url=`${origin}/api/presets`;
 const name='Inventory ordering control '+Date.now();let first=true,reached=false;let release!:()=>void;const held=new Promise<void>(resolve=>release=resolve);
 await page.route(url,async route=>{
  if(route.request().method()==='GET'&&first){first=false;const response=await route.fetch();expect(response.ok()).toBe(true);reached=true;await held;
   if(oldFails)await route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'old-inventory-fault-control'})});else await route.fulfill({response});
  }else await route.continue();
 });
 const errors:string[]=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(origin);await expect.poll(()=>reached).toBe(true);
 await page.getByRole('button',{name:'Presets',exact:true}).click();await page.getByLabel('Nombre',{exact:true}).fill(name);
 const accepted=page.waitForResponse(r=>r.url()===url&&r.request().method()==='POST');await page.getByRole('button',{name:'Guardar preset',exact:true}).click();const response=await accepted;expect(response.ok()).toBe(true);
 const saved=page.getByRole('button',{name,exact:true});await expect(saved).toBeVisible();
 const late=page.waitForResponse(r=>r.url()===url&&r.request().method()==='GET');release();await(await late).finished();await page.evaluate(()=>new Promise<void>(resolve=>requestAnimationFrame(()=>requestAnimationFrame(()=>resolve()))));
 await expect(saved).toBeVisible();await expect(page.getByText(/old-inventory-fault-control/)).toHaveCount(0);
 const records=await(await page.request.get(url)).json();expect(records.filter((r:any)=>r.name===name)).toHaveLength(1);expect(errors).toEqual([]);
});
