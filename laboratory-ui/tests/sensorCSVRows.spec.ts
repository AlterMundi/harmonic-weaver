import {test,expect} from '@playwright/test';
import {readFile} from 'node:fs/promises';
for(const scope of ['R11','R12'])test(`${scope} row indices preserve timestamps, missing values and original archive`,async({page})=>{
 test.skip(!process.env.LAB_COMPONENT_TEST_URL,'isolated API/Vite proxy required');
 const url=process.env.LAB_COMPONENT_TEST_URL!,neuro=scope==='R11',component=neuro?'NeuroPanel':'PhysiologyPanel';
 await page.route(`${url}/csv-rows-test`,route=>route.fulfill({contentType:'text/html',body:'<div id="test-root"></div>'}));await page.goto(`${url}/csv-rows-test`);
 await page.addScriptTag({type:'module',content:`
 import React from '/node_modules/.vite/deps/react.js';import ReactDOM from '/node_modules/.vite/deps/react-dom_client.js';import {${component}} from '/src/${component}.tsx';
 const api=async(path,body)=>{const r=await fetch('/api/'+path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const value=await r.json();if(!r.ok)throw Error(JSON.stringify(value));return value};
 ReactDOM.createRoot(document.getElementById('test-root')).render(React.createElement(${component},{api}));`});
 if(!neuro)await page.getByText('Importar tabla CSV R12',{exact:true}).click();
 const json=page.getByRole('textbox',{name:neuro?'Mapeo de columnas CSV R11 (JSON)':'Mapeo CSV R12 JSON',exact:true});
 await json.fill(JSON.stringify({delimiter:',',index_column:'index',time_column:'time_ms',time_units:'milliseconds',channel_columns:neuro?{ch1:'channel'}:{hr:'hr',p:'power'},missing_tokens:[''],missing_cause:'declared_csv_missing'}));
 await expect(page.getByRole('combobox',{name:`Índice CSV ${scope}`,exact:true})).toHaveValue('column');
 await page.getByRole('combobox',{name:`Índice CSV ${scope}`,exact:true}).selectOption('row_ordinal');
 await expect(page.getByText('Índices generados por fila, sin descartar registros.',{exact:false})).toBeVisible();
 await page.getByRole('combobox',{name:`Formato temporal CSV ${scope}`,exact:true}).selectOption('iso8601');await page.getByRole('textbox',{name:`Origen ISO CSV ${scope}`,exact:true}).fill('2026-10-03T12:00:00Z');
 expect(JSON.parse(await json.inputValue()).schema_version).toBe(3);
 if(neuro){
  await page.getByRole('combobox',{name:`Formato temporal CSV ${scope}`,exact:true}).selectOption('milliseconds');expect(JSON.parse(await json.inputValue()).time_origin).toBeUndefined();
  await page.getByLabel('Metadatos de observación CSV R11 (JSON)').fill(JSON.stringify({source_id:'synthetic-row-csv',subject_slot:'declared-slot',provider:'synthetic',hardware_description:'No hardware',nominal_sample_rate_hz:250,clock:{source_clock:'synthetic',common_clock:'declared',offset_s:0,rate:1,uncertainty_s:.01,method:'declared_assumption'},channels:[{id:'ch1',kind:'eeg',units:'adc_counts',reference:'declared-reference'}]}));
 }
 const raw=neuro?'time_ms,channel\r\n0,1\r\n100,\r\n':'time_ms,hr,power\r\n2026-10-03T12:00:00Z,60,2\r\n2026-10-03T12:00:01Z,,2\r\n2026-10-03T12:00:03Z,80,2\r\n';
 await page.getByLabel(neuro?'Archivo CSV UTF-8 R11':'Archivo CSV R12',{exact:true}).setInputFiles({name:'synthetic.csv',mimeType:'text/csv',buffer:Buffer.from(raw)});
 const inspected=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes(neuro?'/api/research/r11/import-csv':'/api/research/r12/csv/inspect'));
 await page.getByRole('button',{name:neuro?'Convertir CSV R11':'Inspeccionar CSV R12',exact:true}).click();
 const response=await inspected;expect(response.ok()).toBe(true);const result=await response.json(),samples=neuro?result.stream.samples:result.request.samples;
 expect(samples.map((r:any)=>r.index)).toEqual(neuro?[0,1]:[0,1,2]);expect(samples.map((r:any)=>r.source_time_s)).toEqual(neuro?[0,.1]:[0,1,3]);expect(samples[1].values[neuro?'ch1':'hr']).toBeNull();expect(result.import_provenance.index_generation.device_counter_observed).toBe(false);
 const saveRoute=neuro?'/api/research/r11/csv-imports':'/api/research/r12/csv/imports';const accepted=page.waitForResponse(r=>r.url().endsWith(saveRoute)&&r.request().method()==='POST');
 await page.getByRole('button',{name:neuro?'Guardar importación CSV R11':'Guardar original y conversión CSV R12',exact:true}).click();
 const savedResponse=await accepted;expect(savedResponse.ok()).toBe(true);const saved=await savedResponse.json();const original=await page.request.get(`${url}${saveRoute}/${saved.id}/artifacts/source.csv`);expect((await original.body()).equals(Buffer.from(raw))).toBe(true);
 const downloadPromise=page.waitForEvent('download');await page.getByRole('button',{name:`Exportar mapeo CSV ${scope}`,exact:true}).click();
 const downloaded=await downloadPromise,portable=JSON.parse(await readFile((await downloaded.path())!,'utf8'));
 expect(portable.schema_version).toBe(3);expect(portable.index_mode).toBe('row_ordinal');expect(portable.index_column).toBeNull();expect(portable.time_origin).toBeUndefined();
 await page.getByRole('combobox',{name:`Índice CSV ${scope}`,exact:true}).selectOption('column');await expect(page.getByRole('textbox',{name:`Columna de índice CSV ${scope}`,exact:true})).toHaveValue('index');const restored=JSON.parse(await json.inputValue());expect(restored.index_mode).toBeUndefined();expect(restored.schema_version).toBe(neuro?undefined:2);
});
