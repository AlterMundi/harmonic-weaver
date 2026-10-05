import {test,expect} from '@playwright/test';

test('export polling waits for its reply and stops on unmount',async({page})=>{
 test.skip(!process.env.LAB_COMPONENT_TEST_URL,'temporary Vite component fixture required');
 const origin=process.env.LAB_COMPONENT_TEST_URL!;
 let calls=0;
 let release: (()=>void)|undefined;
 await page.route(`${origin}/api/comparison-exports`,async route=>{
  calls++;
  if(calls===1 || calls===3)await new Promise<void>(resolve=>{release=resolve});
  await route.fulfill({json:[]}).catch(()=>{});
 });
 await page.route(`${origin}/export-poll-test`,route=>route.fulfill({contentType:'text/html',body:'<div id="test-root"></div>'}));
 await page.goto(`${origin}/export-poll-test`);
 await page.clock.install();
 await page.addScriptTag({type:'module',content:`
  import React from '/node_modules/.vite/deps/react.js';
  import ReactDOM from '/node_modules/.vite/deps/react-dom_client.js';
  import {ComparisonExport} from '/src/ComparisonExport.tsx';
  const report={job_id:'synthetic',manifest:{runs:[{preset_index:0,pcm:{file:'synthetic.wav'}}],request:{presets:[{visual:{}}]}}};
  window.testRoot=ReactDOM.createRoot(document.getElementById('test-root'));
  window.testRoot.render(React.createElement(ComparisonExport,{report,run:report.manifest.runs[0]}));
 `});
 await expect(page.getByText('Exportar video, audio y figura',{exact:true})).toBeVisible();
 await expect.poll(()=>calls).toBe(1);
 await page.clock.runFor(3500);
 expect(calls).toBe(1);
 const reply=page.waitForResponse(r=>r.url()===`${origin}/api/comparison-exports`);
 release!();
 await reply;
 await page.waitForTimeout(100);
 await page.clock.runFor(1100);
 await expect.poll(()=>calls).toBe(2);
 await page.waitForTimeout(100);
 await page.clock.runFor(1100);
 await expect.poll(()=>calls).toBe(3);
 const aborted=page.waitForEvent('requestfailed',r=>r.url()===`${origin}/api/comparison-exports`);
 await page.evaluate(()=> (window as any).testRoot.unmount());
 expect((await aborted).failure()?.errorText).toContain('ERR_ABORTED');
 release!();
 const stopped=calls;
 await page.clock.runFor(3500);
 expect(calls).toBe(stopped);
});
