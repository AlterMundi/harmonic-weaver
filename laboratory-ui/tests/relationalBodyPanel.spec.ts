import {test,expect} from '@playwright/test';
test('R04 frozen body selects endpoints and rejects absent calibration without API calls',async({page})=>{
 test.skip(!process.env.LAB_COMPONENT_TEST_URL,'isolated Vite required');
 const origin=process.env.LAB_COMPONENT_TEST_URL!;
 await page.route(`${origin}/r04-body-test`,r=>r.fulfill({contentType:'text/html',body:'<div id="root"></div>'}));
 await page.goto(`${origin}/r04-body-test`);
 await page.addScriptTag({type:'module',content:`
 import React from '/node_modules/.vite/deps/react.js';
 import ReactDOM from '/node_modules/.vite/deps/react-dom_client.js';
 import {RelationalBodyPanel} from '/src/RelationalBodyPanel.tsx';
 window.calls=[];
 const api=async(path,body)=>{if(body){window.calls.push({path,body});return {};}
 if(path==='evaluations')return [{id:'good',status:'complete'},{id:'bad',status:'complete'}];
 return {manifest:{runs:[{source_index:0,preset_id:'preset'}],request:{sources:[{person_id:'right',start_s:2,end_s:62,torso_scale:path.includes('/good/')?.2:null,calibration_provenance:path.includes('/good/')?'explicit':null}]}}};};
 ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(RelationalBodyPanel,{api,run:fn=>fn().catch(()=>{}),settings:{history_s:.5},settingsValid:true,active:false,onStarted:async()=>{}}));
 `});
 const start=page.getByRole('button',{name:'Correr R04 con pose congelada'});
 await expect(start).toBeDisabled();
 await page.getByRole('combobox',{name:/^Comparación corporal R04/}).selectOption('good');
 await expect(start).toBeEnabled();
 await expect(page.getByLabel('Inicio corporal R04 (s)')).toHaveValue('2');
 await page.getByRole('combobox',{name:/^Extremo proximal R04/}).selectOption('9');
 await expect(start).toBeDisabled();
 await page.getByRole('combobox',{name:/^Extremo proximal R04/}).selectOption('7');
 await page.getByLabel('Fin corporal R04 (s)').fill('63');await expect(start).toBeDisabled();
 await page.getByLabel('Fin corporal R04 (s)').fill('12');
 expect(await page.evaluate(()=>(window as any).calls)).toEqual([]);
 await start.click();await expect.poll(()=>page.evaluate(()=>(window as any).calls.length)).toBe(1);
 expect(await page.evaluate(()=>(window as any).calls[0])).toEqual({path:'research/r04/trace',body:{settings:{history_s:.5},selection:{evaluation_id:'good',run_index:0,parent_joint:7,child_joint:9,start_s:2,end_s:12}}});
 await page.getByRole('combobox',{name:/^Comparación corporal R04/}).selectOption('bad');
 await expect(start).toBeDisabled();await expect(page.getByRole('alert')).toContainText('no tiene escala');
});
