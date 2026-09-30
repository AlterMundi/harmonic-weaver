import { test, expect } from '@playwright/test';

test('explicit capture controls preserve settings, show failures and do not start on mount', async ({page}) => {
  test.skip(!process.env.LAB_COMPONENT_TEST_URL, 'requires isolated Vite');
  const origin=process.env.LAB_COMPONENT_TEST_URL!;
  const errors:string[]=[];page.on('pageerror',e=>errors.push(String(e)));
  await page.route(`${origin}/capture-test`,r=>r.fulfill({contentType:'text/html',body:'<div id="test-root"></div>'}));
  await page.goto(`${origin}/capture-test`);
  await page.addScriptTag({type:'module',content:`
    import React from '/node_modules/.vite/deps/react.js';
    import ReactDOM from '/node_modules/.vite/deps/react-dom_client.js';
    import {CapturePanel} from '/src/CapturePanel.tsx';
    let state={current:{status:'idle'},jobs:[]};window.captureCalls=[];
    const api=async(path,body)=>{
      window.captureCalls.push({path,body});
      if(path==='captures/start')state={current:{status:'recording'},jobs:[]};
      if(path==='captures/stop')state={current:{status:'complete'},jobs:[{id:'test',status:'complete',events:1205,timeline_rows:7,directory:'/synthetic/session',shaper:{directory:'/synthetic/audio'}}]};
      return state;
    };
    window.failCapture=()=>state={current:{status:'failed',error:'Synthetic disk failure'},jobs:[]};
    ReactDOM.createRoot(document.getElementById('test-root')).render(React.createElement(CapturePanel,{api,run:fn=>fn()}));
  `});
  const start=page.getByRole('button',{name:'Iniciar captura'});
  const stop=page.getByRole('button',{name:'Detener captura'});
  await expect(start).toBeEnabled();await expect(stop).toBeDisabled();
  await page.waitForTimeout(600);
  expect(await page.evaluate(()=>(window as any).captureCalls.every((x:any)=>x.path==='captures'))).toBe(true);
  await page.getByLabel('Duración máxima (s)').fill('60');
  await page.getByLabel('Capacidad de cola de audio (bloques)').fill('64');
  await page.getByLabel('Frecuencia del timeline (Hz)').fill('30');
  await start.click();await expect(start).toBeDisabled();await expect(stop).toBeEnabled();
  await expect(page.getByLabel('Duración máxima (s)')).toBeDisabled();
  expect(await page.evaluate(()=>(window as any).captureCalls.find((x:any)=>x.path==='captures/start').body)).toEqual({max_seconds:60,queue_blocks:64,timeline_hz:30});
  await stop.click();await expect(start).toBeEnabled();await expect(stop).toBeDisabled();
  await expect(page.getByText('Bitácora local: /synthetic/session')).toBeVisible();
  await expect(page.getByText('Audio local: /synthetic/audio')).toBeVisible();
  await page.evaluate(()=>(window as any).failCapture());
  await expect(page.getByRole('status')).toContainText('Synthetic disk failure');
  expect(errors).toEqual([]);
});
