import {test,expect} from '@playwright/test';
test('body bench selects frozen same-unit features and sends explicit origin settings',async({page})=>{
 test.skip(!process.env.LAB_COMPONENT_TEST_URL,'requires isolated Vite');const origin=process.env.LAB_COMPONENT_TEST_URL!;
 const errors:string[]=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.route(`${origin}/body-test`,r=>r.fulfill({contentType:'text/html',body:'<div id="root"></div>'}));
 await page.goto(`${origin}/body-test`);
 await page.addScriptTag({type:'module',content:`
 import React from '/node_modules/.vite/deps/react.js';import ReactDOM from '/node_modules/.vite/deps/react-dom_client.js';
 import {BodyResearchPanel} from '/src/BodyResearchPanel.tsx';
 const api=async(path,body)=>{if(body){window.request=body;return {id:'new'};}if(path==='evaluations')return [{id:'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',status:'complete'}];return {manifest:{request:{sources:[{start_s:1,end_s:4,person_id:'right-slot'}]},runs:[{source_index:0,preset_id:'local',signals:{'zone.1.speed':{unit:'T/s',observed_count:80},'zone.2.speed':{unit:'T/s',observed_count:80},'zone.1.acceleration':{unit:'T/s2',observed_count:80}}}]}};};
 ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(BodyResearchPanel,{api,run:fn=>fn(),onStarted:async()=>{window.started=true}}));
 `});
 await page.getByLabel('Comparación de origen').selectOption('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa');
 await expect(page.getByText('Persona: right-slot.',{exact:false})).toBeVisible();
 await page.getByRole('checkbox',{name:'zone.1.speed',exact:false}).check();
 await page.getByRole('checkbox',{name:'zone.1.acceleration',exact:false}).check();
 await expect(page.getByRole('button',{name:'Correr R01 con features'})).toBeDisabled();
 await page.getByRole('checkbox',{name:'zone.1.acceleration',exact:false}).uncheck();
 await page.getByRole('checkbox',{name:'zone.2.speed',exact:false}).check();
 await page.getByLabel('Horizonte corporal (muestras)').fill('6');
 await page.getByRole('button',{name:'Exportar configuración corporal JSON'}).click();
 const config=JSON.parse(await page.getByLabel('Configuración corporal JSON').inputValue());
 expect(config.settings.horizon_steps).toBe(6);expect(config.evaluation_id).toBeUndefined();
 await page.getByRole('button',{name:'Correr R01 con features'}).click();
 await expect.poll(()=>page.evaluate(()=>(window as any).request)).toEqual({evaluation_id:'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',run_index:0,signal_ids:['zone.1.speed','zone.2.speed'],start_s:1,end_s:4,seed:0,components:2,window_s:2,noise_threshold:.02,ridge:.1,horizon_steps:6,max_gap_s:.1});
 expect(errors).toEqual([]);
});
