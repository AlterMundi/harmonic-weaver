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
 const baselineResponse=await page.request.get(`${origin}/api/research/r09/multiview/runs`);const baseline=(await baselineResponse.json()).filter((r:any)=>r.status==='complete').length;
 await mount();
 const panel=page.getByRole('region',{name:'Reconstrucción multivista R09',exact:true});
 const saved=page.getByRole('region',{name:'Cálculos multivista guardados R09',exact:true});
 await panel.getByRole('button',{name:'Cargar control sintético multivista R09'}).click();
 await expect(panel.getByRole('textbox',{name:'Pares y calibración JSON R09'})).toHaveValue(/"calibration_kind": "synthetic"/);
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

 await expect(panel.getByText('Multivista R09: 5 puntos inferidos; 0 faltantes.',{exact:false})).toBeVisible();
 expect(JSON.parse(await panel.getByRole('textbox',{name:'Pares y calibración JSON R09'}).inputValue()).left_camera).toEqual(original.left_camera);
 const download=page.waitForEvent('download');await saved.locator(`a[href$="/${acceptedId}/artifacts/result.json"]`).click();
 const result=JSON.parse(await readFile((await(await download).path())!,'utf8'));expect(result.stream.frames[0].points[0].state).toBe('inferred');
 await saved.getByRole('button',{name:`Verificar recálculo multivista ${acceptedId}`,exact:true}).click();
 await expect(saved.getByText('Recálculo verificado',{exact:false})).toBeVisible();
 // An accepted but lost derived-stream response recovers by the same run ID and key.
 const selections:any[]=[];let loseConversion=true;let conversionId='';
 const conversionRoute='**/api/research/r09/multiview-conversions';
 await page.route(conversionRoute,async route=>{selections.push(route.request().postDataJSON());if(loseConversion){loseConversion=false;const r=await route.fetch();expect(r.ok()).toBeTruthy();conversionId=(await r.json()).id;await route.abort('failed');return}await route.continue()});
 const originButton=saved.getByRole('button',{name:`Guardar stream con procedencia multivista ${acceptedId}`,exact:true});
 await originButton.click();await expect(saved.getByRole('alert')).toBeVisible();
 await originButton.click();await expect(saved.getByRole('status').filter({hasText:'Stream multivista guardado con procedencia'})).toContainText(conversionId);
 expect(selections).toHaveLength(2);expect(selections[1]).toEqual(selections[0]);
 const conversionResponse=await page.request.get(`${origin}/api/research/r09/conversions/${conversionId}/artifacts/result.json`);const conversionResult=await conversionResponse.json();
 expect(conversionResult.multiview_origin.run_id).toBe(acceptedId);expect(conversionResult.multiview_origin.verification).toBe('local_artifact_integrity');expect(conversionResult.stream).toEqual(result.stream);
 const compare=page.getByRole('region',{name:'Comparación espacial R09',exact:true});
 await compare.getByRole('combobox',{name:'Origen de comparación R09'}).selectOption('saved');
 await compare.getByRole('button',{name:'Actualizar conversiones para comparar R09'}).click();
 await compare.getByRole('combobox',{name:'Referencia guardado R09'}).selectOption(conversionId);
 await compare.getByRole('combobox',{name:'Candidato guardado R09'}).selectOption(conversionId);
 await compare.getByRole('textbox',{name:'Etiquetas de comparación R09'}).fill(JSON.stringify(original.labels));
 await compare.getByRole('checkbox',{name:'Admitir puntos inferidos R09'}).check();
 await compare.getByRole('button',{name:'Guardar comparación espacial R09'}).click();
 await expect(compare.getByText('Soporte espacial: 5/5 puntos elegibles. Unidad: metres.',{exact:true})).toBeVisible();
 await expect(compare.getByText('Error medio sobre soporte: 0; máximo: 0.',{exact:true})).toBeVisible();
 await page.unroute(conversionRoute);
 // Hold a real accepted artifact response, then edit the worksheet before delivery.
 let release!:()=>void;const gate=new Promise<void>(resolve=>release=resolve);
 let received!:()=>void;const responseReady=new Promise<void>(resolve=>received=resolve);
 const artifactUrl=`**/api/research/r09/multiview/runs/${acceptedId}/artifacts/result.json`;
 await page.route(artifactUrl,async route=>{const response=await route.fetch();received();await gate;await route.fulfill({response})});
 await saved.getByRole('button',{name:`Abrir cálculo multivista ${acceptedId}`,exact:true}).click();await responseReady;
 const changed={...original,source_id:'edited-during-open'};
 await panel.getByRole('textbox',{name:'Pares y calibración JSON R09'}).fill(JSON.stringify(changed));release();
 await expect(saved.getByRole('alert')).toContainText('Apertura descartada');
 expect(JSON.parse(await panel.getByRole('textbox',{name:'Pares y calibración JSON R09'}).inputValue()).source_id).toBe('edited-during-open');
 await page.unroute(artifactUrl);
 await saved.getByRole('button',{name:`Abrir cálculo multivista ${acceptedId}`,exact:true}).click();
 await expect(panel.getByRole('textbox',{name:'Pares y calibración JSON R09'})).not.toHaveValue(/edited-during-open/);
 await saved.getByRole('button',{name:`Repetir cálculo multivista ${acceptedId}`,exact:true}).click();
 await expect(saved.getByRole('button',{name:/^Abrir cálculo multivista /})).toHaveCount(baseline+2);
 expect(bodies).toHaveLength(3);expect(bodies[2].idempotency_key).not.toBe(bodies[0].idempotency_key);
 await mount();await expect(saved.getByRole('button',{name:/^Abrir cálculo multivista /})).toHaveCount(baseline+2);expect(bodies).toHaveLength(3);
 // Recover the monitor of an actual bounded calculation started by a previous page.
 const large={...original,labels:['a','b','c'],frames:Array.from({length:14400},(_,i)=>({
  ...original.frames[0],index:i,left_time_s:i*.01,right_time_s:i*.01,
  left:['a','b','c'].map(label=>({...original.frames[0].left[0],label})),
  right:['a','b','c'].map(label=>({...original.frames[0].right[0],label}))
 }))};
 const started=await page.request.post(`${origin}/api/research/r09/multiview/runs`,{data:large});expect(started.ok()).toBeTruthy();const ongoing=(await started.json()).id;
 await mount();await saved.getByRole('button',{name:`Seguir cálculo multivista ${ongoing}`,exact:true}).click();
 await saved.getByRole('button',{name:'Cancelar cálculo multivista R09',exact:true}).click();
 await expect(saved.getByRole('status').filter({hasText:ongoing})).toContainText('cancelled');
 await page.evaluate(()=>new Promise<void>((resolve,reject)=>{
  const request=indexedDB.open('weaver-r09-multiview',1);
  request.onsuccess=()=>{const db=request.result;const tx=db.transaction('pending','readwrite');tx.objectStore('pending').put({body:{idempotency_key:'invalid'}},'start');tx.oncomplete=()=>{db.close();resolve()};tx.onerror=()=>reject(tx.error)};
  request.onerror=()=>reject(request.error);
 }));
 await mount();await expect(saved.getByRole('alert')).toContainText('Intento multivista local inválido');
 await expect(saved.getByRole('button',{name:'Recuperar inicio multivista R09'})).toBeDisabled();
 await saved.getByRole('button',{name:'Descartar intento multivista pendiente'}).click();
 await expect(saved.getByRole('button',{name:'Guardar y reconstruir multivista R09',exact:true})).toBeEnabled();expect(bodies).toHaveLength(3);


});
