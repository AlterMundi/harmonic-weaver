import {test,expect} from '@playwright/test';
import {readFile} from 'node:fs/promises';
test('lost accepted multiview start recovers once across reload; explicit open, verify and repeat',async({page})=>{
 test.skip(!process.env.LAB_COMPONENT_TEST_URL,'isolated API/Vite required');
 const origin=process.env.LAB_COMPONENT_TEST_URL!;
 await page.route(`${origin}/multiview-runs-test`,route=>route.fulfill({contentType:'text/html',body:'<div id="test-root"></div>'}));
 const mount=async()=>{
  await page.goto(`${origin}/multiview-runs-test`);
  await page.addScriptTag({type:'module',content:`import React from '/node_modules/.vite/deps/react.js';import ReactDOM from '/node_modules/.vite/deps/react-dom_client.js';import {SpatialPanel} from '/src/SpatialPanel.tsx';
 const api=async(path,body)=>{const r=await fetch('/api/'+path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const value=await r.json();if(!r.ok){const e=Error(JSON.stringify(value));e.status=r.status;throw e}return value};ReactDOM.createRoot(document.getElementById('test-root')).render(React.createElement(SpatialPanel,{api}));`});
 };
 await mount();
 const panel=page.getByRole('region',{name:'Reconstrucción multivista R09',exact:true});
 const saved=page.getByRole('region',{name:'Cálculos multivista guardados R09',exact:true});
 await panel.getByRole('button',{name:'Cargar control sintético multivista R09'}).click();
 const original=JSON.parse(await panel.getByRole('textbox',{name:'Pares y calibración JSON R09'}).inputValue());
 const bodies:any[]=[];let lost=true;let acceptedId='';
 await page.route('**/api/research/r09/multiview/runs',async route=>{
  if(route.request().method()!=='POST'){await route.continue();return}
  bodies.push(route.request().postDataJSON());
  if(lost){lost=false;const response=await route.fetch();expect(response.ok()).toBeTruthy();acceptedId=(await response.json()).id;await route.abort('failed');return}
  await route.continue();
 });
 await saved.getByRole('button',{name:'Guardar y reconstruir multivista R09',exact:true}).click();
 await expect(saved.getByRole('button',{name:'Recuperar inicio multivista R09'})).toBeVisible();
 expect(bodies).toHaveLength(1);
 await mount();
 await expect(saved.getByRole('button',{name:'Recuperar inicio multivista R09'})).toBeVisible();expect(bodies).toHaveLength(1);
 await saved.getByRole('button',{name:'Recuperar inicio multivista R09'}).click();
 await expect(saved.getByRole('button',{name:`Abrir cálculo multivista ${acceptedId}`,exact:true})).toBeVisible();
 expect(bodies).toHaveLength(2);expect(bodies[1]).toEqual(bodies[0]);
 await saved.getByRole('button',{name:`Abrir cálculo multivista ${acceptedId}`,exact:true}).click();
 expect(JSON.parse(await panel.getByRole('textbox',{name:'Pares y calibración JSON R09'}).inputValue()).left_camera).toEqual(original.left_camera);
 await expect(panel.getByText('Multivista R09: 5 puntos inferidos; 0 faltantes.',{exact:false})).toBeVisible();
 const download=page.waitForEvent('download');await saved.getByRole('link',{name:'result.json',exact:true}).first().click();
 const result=JSON.parse(await readFile((await(await download).path())!,'utf8'));expect(result.stream.frames[0].points[0].state).toBe('inferred');
 await saved.getByRole('button',{name:`Verificar recálculo multivista ${acceptedId}`,exact:true}).click();
 await expect(saved.getByText('Recálculo verificado',{exact:false})).toBeVisible();
 await saved.getByRole('button',{name:`Repetir cálculo multivista ${acceptedId}`,exact:true}).click();
 await expect(saved.getByRole('button',{name:/^Abrir cálculo multivista /})).toHaveCount(2);
 expect(bodies).toHaveLength(3);expect(bodies[2].idempotency_key).not.toBe(bodies[0].idempotency_key);
 await mount();await expect(saved.getByRole('button',{name:/^Abrir cálculo multivista /})).toHaveCount(2);expect(bodies).toHaveLength(3);
});
