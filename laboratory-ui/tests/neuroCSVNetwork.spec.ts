import {test,expect} from '@playwright/test';

test('explicit CSV import preserves raw digest and archives converted observations',async({page})=>{
 test.skip(!process.env.LAB_R11_CSV_URL&&!process.env.LAB_COMPONENT_TEST_URL,'isolated API/production UI required');
 const component=process.env.LAB_COMPONENT_TEST_URL;
 const url=component||process.env.LAB_R11_CSV_URL!;
 const mount=async()=>{
  if(!component){await page.goto(url);await page.getByRole('button',{name:'Investigación',exact:true}).click();return}
  await page.route(`${url}/r11-csv-test`,r=>r.fulfill({contentType:'text/html',body:'<div id="test-root"></div>'}));
  await page.goto(`${url}/r11-csv-test`);
  await page.addScriptTag({type:'module',content:`
   import React from '/node_modules/.vite/deps/react.js';import ReactDOM from '/node_modules/.vite/deps/react-dom_client.js';
   import {NeuroPanel} from '/src/NeuroPanel.tsx';
   const api=async(path,body)=>{const r=await fetch('/api/'+path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const value=await r.json();if(!r.ok)throw Error(JSON.stringify(value));return value};
   ReactDOM.createRoot(document.getElementById('test-root')).render(React.createElement(NeuroPanel,{api}));
  `});
 };
 await mount();
 const panel=page.getByRole('region',{name:'Importación CSV R11',exact:true});
 const raw='\ufeffindex,time_ms,channel\r\n0,0,0\r\n2,8,NA\r\n';
 const metadata={source_id:'synthetic-csv',subject_slot:'declared-slot',provider:'synthetic',hardware_description:'No hardware: CSV fixture',nominal_sample_rate_hz:250,clock:{source_clock:'synthetic',common_clock:'declared',offset_s:0,rate:1,uncertainty_s:.01,method:'declared_assumption'},channels:[{id:'ch1',kind:'eeg',units:'adc_counts',reference:'declared-reference'}]};
 const mapping={delimiter:',',skip_rows:0,index_column:'index',time_column:'time_ms',time_units:'milliseconds',channel_columns:{ch1:'channel'},missing_tokens:['NA'],missing_cause:'declared_export_gap'};
 await panel.getByLabel('Archivo CSV UTF-8 R11').setInputFiles({name:'synthetic.csv',mimeType:'text/csv',buffer:Buffer.from(raw)});
 await expect(panel.getByLabel('Texto CSV R11')).toHaveValue(raw.replace(/\r\n/g,'\n'));
 await panel.getByLabel('Metadatos de observación CSV R11 (JSON)').fill(JSON.stringify(metadata));
 await panel.getByLabel('Mapeo de columnas CSV R11 (JSON)').fill(JSON.stringify(mapping));
 await expect(panel.getByLabel('Formato temporal CSV R11')).toHaveValue('milliseconds');
 await panel.getByLabel('Formato temporal CSV R11').selectOption('iso8601');
 await panel.getByLabel('Origen ISO CSV R11').fill('2026-10-03T12:00:00Z');
 await panel.getByLabel('Formato temporal CSV R11').selectOption('milliseconds');
 expect(JSON.parse(await panel.getByLabel('Mapeo de columnas CSV R11 (JSON)').inputValue())).toEqual(mapping);
 await panel.getByRole('button',{name:'Convertir CSV R11'}).click();
 await expect(panel).toContainText('CSV convertido: 2 muestras · 1 saltos');
 const exported=page.waitForEvent('download');await panel.getByRole('button',{name:'Exportar conversión y procedencia CSV R11'}).click();
 const stream=await(await exported).createReadStream();let text='';for await(const chunk of stream!)text+=chunk.toString();const converted=JSON.parse(text);
 const digest=await page.evaluate(async raw=>{const h=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(raw));return Array.from(new Uint8Array(h)).map(v=>v.toString(16).padStart(2,'0')).join('');},raw);
 expect(converted.stream.raw_source_sha256).toBe(digest);
 expect(converted.import_provenance.mapping).toEqual(mapping);
 expect(converted.stream.samples[1].source_time_s).toBe(.008);
 expect(converted.stream.samples[0].values.ch1).toBe(0);
 expect(converted.stream.samples[1].values.ch1).toBeNull();
 await page.route('**/api/research/r11/csv-imports',async route=>{
  if(route.request().method()!=='POST'){await route.continue();return;}
  await route.fetch();await route.fulfill({status:503,contentType:'application/json',body:'{"detail":"simulated lost publication response"}'});
 });
 await panel.getByRole('button',{name:'Guardar importación CSV R11',exact:true}).click();
 await expect(panel.getByRole('alert')).toContainText('Si se perdió la respuesta');
 await page.unroute('**/api/research/r11/csv-imports');
 await panel.getByRole('button',{name:'Actualizar importaciones CSV R11',exact:true}).click();
 await expect(panel.getByRole('button',{name:'Abrir importación CSV R11',exact:true})).toHaveCount(1);
 await panel.getByRole('button',{name:'Guardar importación CSV R11',exact:true}).click();
 await expect(panel.getByRole('button',{name:'Abrir importación CSV R11',exact:true})).toHaveCount(1);
 await mount();
 await panel.getByRole('button',{name:'Abrir importación CSV R11',exact:true}).click();
 await expect(panel).toContainText('CSV convertido: 2 muestras · 1 saltos');
 const savedMetadata=JSON.parse(await panel.getByLabel('Metadatos de observación CSV R11 (JSON)').inputValue());
 expect(savedMetadata.source_id).toBe(metadata.source_id);
 const originalDownload=page.waitForEvent('download');await panel.getByRole('link',{name:'source.csv',exact:true}).click();
 const originalStream=await(await originalDownload).createReadStream();const chunks:Buffer[]=[];
 for await(const chunk of originalStream!)chunks.push(Buffer.from(chunk));
 expect(Buffer.concat(chunks).equals(Buffer.from(raw))).toBeTruthy();
 await panel.getByRole('button',{name:'Recalcular importación CSV R11',exact:true}).click();
 await expect(panel).toContainText('Verificación CSV: recomputed');
 await panel.getByRole('button',{name:'Usar observaciones CSV en R11'}).click();
 const native=page.getByRole('region',{name:'Observaciones crudas R11',exact:true});
 await expect(native.getByRole('table')).toContainText('adc_counts');
 await native.getByRole('button',{name:'Guardar observaciones R11',exact:true}).click();
 await expect(native.getByRole('button',{name:'Abrir observaciones guardadas R11'})).toHaveCount(1);
 await native.getByRole('button',{name:'Abrir observaciones guardadas R11'}).click();
 await expect(native).toContainText('Observaciones guardadas:');
 const body=JSON.parse(await native.getByLabel('Observaciones JSON R11').inputValue());
 expect(body.raw_source_sha256).toBe(digest);
 await panel.getByLabel('Texto CSV R11').fill('index,time_ms,channel\n0,0,NaN\n');
 await expect(panel.getByRole('button',{name:'Usar observaciones CSV en R11'})).toHaveCount(0);
 await panel.getByRole('button',{name:'Convertir CSV R11'}).click();
 await expect(panel.getByRole('alert')).toBeVisible();
});
