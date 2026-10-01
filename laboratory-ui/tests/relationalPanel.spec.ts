import {test,expect} from '@playwright/test';
test('R04 edits freeze settings, portable configuration and missing trace stays undefined',async({page})=>{
 test.skip(!process.env.LAB_COMPONENT_TEST_URL,'isolated Vite required');
 const origin=process.env.LAB_COMPONENT_TEST_URL!;
 await page.route(`${origin}/r04-test`,r=>r.fulfill({contentType:'text/html',body:'<div id="root"></div>'}));
 await page.goto(`${origin}/r04-test`);
 await page.addScriptTag({type:'module',content:`
 import React from '/node_modules/.vite/deps/react.js';
 import ReactDOM from '/node_modules/.vite/deps/react-dom_client.js';
 import {RelationalPanel} from '/src/RelationalPanel.tsx';
 window.calls=[];
 const api=async(path,body)=>{
 if(body){window.calls.push({path,body});return {id:'job'};}
 if(path==='evaluations')return [];
 if(path==='research/r04')return [{id:'job',status:'complete'}];
 return {traces:{'shared/original':[{time_s:0,parent_velocity:[1,0],child_velocity:[1,0],relative:{state:'missing',reason:'warming relationship'}}]},limits:['Synthetic only']};
 };
 ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(RelationalPanel,{api,run:fn=>fn().catch(()=>{})}));
 `});
 const start=page.getByRole('button',{name:'Correr banco R04'});
 await expect(start).toBeEnabled();
 await page.getByLabel('Muestras R04').fill('9');await expect(start).toBeDisabled();
 await page.getByLabel('Muestras R04').fill('30');
 await page.getByLabel('Referencia relacional R04').selectOption('instantaneous');
 await page.getByLabel('Rotación uniforme R04 (grados)').fill('90');
 expect(await page.evaluate(()=>(window as any).calls)).toEqual([]);
 await start.click();
 await expect.poll(()=>page.evaluate(()=>(window as any).calls.length)).toBe(1);
 expect(await page.evaluate(()=>(window as any).calls[0])).toMatchObject({path:'research/r04',body:{samples:30,rotation_deg:90,relation_reference:'instantaneous'}});
 await page.getByRole('button',{name:'Exportar configuración R04'}).click();
 const config=JSON.parse(await page.getByLabel('Configuración R04 JSON').inputValue());
 expect(config.rotation_deg).toBe(90);expect(Object.keys(config)).toHaveLength(10);
 await page.getByLabel('Rotación uniforme R04 (grados)').fill('73');
 await page.getByRole('button',{name:'Importar configuración R04'}).click();
 await expect(page.getByLabel('Rotación uniforme R04 (grados)')).toHaveValue('90');
 expect(await page.evaluate(()=>(window as any).calls.length)).toBe(1);
 await page.getByRole('button',{name:'Ver resultado R04 job'}).click();
 await expect(page.getByText('indefinido',{exact:true})).toHaveCount(3);
 await expect(page.getByText('Synthetic only',{exact:true})).toBeVisible();
});
