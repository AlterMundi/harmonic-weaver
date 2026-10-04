import {test,expect} from '@playwright/test';
test('R12 real API controls, missing support, immutable save retry and portable settings',async({page})=>{
 test.skip(!process.env.LAB_COMPONENT_TEST_URL,'requires isolated local API/Vite proxy');
 const origin=process.env.LAB_COMPONENT_TEST_URL!;
 await page.route(`${origin}/r12-test`,r=>r.fulfill({contentType:'text/html',body:'<div id="test-root"></div>'}));
 const mount=async()=>{
  await page.goto(`${origin}/r12-test`);
  await page.addScriptTag({type:'module',content:`
   import React from '/node_modules/.vite/deps/react.js';
   import ReactDOM from '/node_modules/.vite/deps/react-dom_client.js';
   import {PhysiologyPanel} from '/src/PhysiologyPanel.tsx';
   const api=async(path,body)=>{const r=await fetch('/api/'+path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const value=await r.json();if(!r.ok)throw Error(JSON.stringify(value));return value};
   ReactDOM.createRoot(document.getElementById('test-root')).render(React.createElement(PhysiologyPanel,{api}));
  `});
 };
 await mount();
 await page.getByRole('button',{name:'Analizar mediciones R12',exact:true}).click();
 const table=page.getByRole('table',{name:'Resultados R12 control'});
 await expect(table).toBeVisible();
 await expect(table.getByRole('row').nth(1)).toContainText('85');
 await expect(table.getByRole('row').nth(2)).toContainText('10');
 await page.getByLabel('Gap máximo entre muestras (s)',{exact:true}).fill('.5');
 await page.getByRole('button',{name:'Analizar mediciones R12',exact:true}).click();
 await expect(table.getByRole('row').nth(1)).toContainText('Sin soporte');
 await expect(table.getByRole('row').nth(2)).toContainText('No calculado');
 await page.getByLabel('Gap máximo entre muestras (s)',{exact:true}).fill('2');
 const download=page.waitForEvent('download');
 await page.getByRole('button',{name:'Guardar configuración portable R12'}).click();
 expect((await download).suggestedFilename()).toBe('r12-analysis-settings.json');
 await page.getByRole('button',{name:'Analizar mediciones R12',exact:true}).click();
 await expect(table.getByRole('row').nth(1)).toContainText('85');
 let sent:string|null=null;
 await page.route('**/api/research/r12/measurements',async route=>{
  if(route.request().method()==='POST' && sent===null){sent=route.request().postData();const response=await route.fetch();expect(response.ok()).toBe(true);await route.abort('failed');return}
  if(route.request().method()==='POST')expect(route.request().postData()).toBe(sent);
  await route.continue();
 });
 await page.getByRole('button',{name:'Guardar corrida R12',exact:true}).click();
 await expect(page.getByRole('button',{name:'Recuperar envío R12'})).toBeVisible();
 await mount();
 await expect(page.getByRole('button',{name:'Recuperar envío R12'})).toBeVisible();
 await page.getByRole('button',{name:'Recuperar envío R12'}).click();
 await expect(page.getByRole('button',{name:'Recuperar envío R12'})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Abrir corrida R12'})).toHaveCount(1);
 await page.getByRole('button',{name:'Abrir corrida R12'}).click();
 await expect(table.getByRole('row').nth(1)).toContainText('85');
 const manifest=page.locator('a[href^="/api/research/r12/measurements/"]').filter({hasText:'manifest.json'});
 const response=await page.request.get(origin+(await manifest.getAttribute('href') || ''));expect(response.ok()).toBe(true);
 expect((await response.json()).line).toBe('R12');
 await expect(page.getByRole('alert')).toHaveCount(0);
});
