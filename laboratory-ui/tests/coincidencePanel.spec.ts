import {test,expect} from '@playwright/test';
test('explicit coverage and group freeze, configuration portability, result display',async({page})=>{
 test.skip(!process.env.LAB_COMPONENT_TEST_URL,'isolated Vite required');
 const origin=process.env.LAB_COMPONENT_TEST_URL!;
 await page.route(`${origin}/r03-test`,r=>r.fulfill({contentType:'text/html',body:'<div id="root"></div>'}));
 await page.goto(`${origin}/r03-test`);
 await page.addScriptTag({type:'module',content:`
 import React from '/node_modules/.vite/deps/react.js';
 import ReactDOM from '/node_modules/.vite/deps/react-dom_client.js';
 import {CoincidencePanel} from '/src/CoincidencePanel.tsx';
 window.calls=[];
 const api=async(path,body)=>{
 if(body){window.calls.push({path,body});return {id:'job'};}
 if(path==='evaluations')return [{id:'evaluation',status:'complete'}];
 if(path==='marks/snapshot')return {through_sequence:7,marks:[{event:{session_id:'session',payload:{annotation_origin:'human_button',source_id:'source',person_id:'right',annotation_category:'deployment',observed_epoch:2,transport_epoch:2}}}]};
 if(path.endsWith('/report'))return {manifest:{runs:[{source_index:0,preset_id:'preset',signals:{speed:{unit:'T/s'}}}],request:{sources:[{person_id:'right',start_s:0,end_s:60}]}}};
 if(path==='research/r03')return [{id:'job',status:'complete'}];
 if(path.endsWith('result.json'))return {comparison:{support_duration_s:20,matches:[{}],precision:1,recall:1}};
 throw Error(path);
 };
 ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(CoincidencePanel,{api,run:fn=>fn().catch(()=>{})}));
 `});
 const start=page.getByRole('button',{name:'Correr contraste R03'});
 await expect(start).toBeDisabled();
 await page.getByRole('combobox',{name:/^Comparación R03/}).selectOption('evaluation');
 await page.getByRole('combobox',{name:/^Señal R03/}).selectOption('speed');
 await page.getByLabel('Grupo de marcas R03').selectOption({index:1});
 await expect(start).toBeDisabled(); // no inferred observation support
 await page.getByLabel('Intervalos realmente observados R03 (JSON)').fill('[[2,1]]');
 await expect(start).toBeDisabled();
 await page.getByLabel('Intervalos realmente observados R03 (JSON)').fill('[[0,20],[30,60]]');
 await expect(start).toBeEnabled();
 await page.getByLabel('Tolerancia (s) R03').fill('11');
 await expect(start).toBeDisabled();
 await page.getByLabel('Tolerancia (s) R03').fill('.2');
 await start.click();
 await expect.poll(()=>page.evaluate(()=>(window as any).calls.length)).toBe(1);
 const call=await page.evaluate(()=>(window as any).calls[0]);
 expect(call.path).toBe('research/r03');
 expect(call.body).toMatchObject({source_id:'source',person_id:'right',session_id:'session',observed_epoch:2,through_sequence:7,mark_support:[[0,20],[30,60]],candidate:{signal_id:'speed',start_s:0,end_s:60}});
 await page.getByRole('button',{name:'Exportar configuración R03'}).click();
 const config=JSON.parse(await page.getByLabel('Configuración R03 JSON').inputValue());
 expect(Object.keys(config).sort()).toEqual(['settings','signal_id']);
 await page.getByRole('button',{name:'Actualizar fuentes y corte de marcas R03'}).click();
 await expect(page.getByLabel('Grupo de marcas R03')).toHaveValue('');
 await expect(start).toBeDisabled();
 await page.getByRole('button',{name:'Ver resultado R03 job'}).click();
 await expect(page.getByText('Soporte común: 20 s', {exact:false}).first()).toBeVisible();
 expect(await page.evaluate(()=>(window as any).calls.length)).toBe(1);
});
