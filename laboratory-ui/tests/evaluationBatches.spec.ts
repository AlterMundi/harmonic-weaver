import {test,expect} from '@playwright/test';
test('comparison budget submits explicitly and continuation keeps frozen job',async({page})=>{
 test.skip(!process.env.LAB_COMPONENT_TEST_URL,'isolated Vite instance required');
 const origin=process.env.LAB_COMPONENT_TEST_URL!;
 await page.route(`${origin}/batch-test`,route=>route.fulfill({contentType:'text/html',body:'<div id="test-root"></div>'}));
 await page.goto(`${origin}/batch-test`);
 await page.addScriptTag({type:'module',content:`
 import React from '/node_modules/.vite/deps/react.js';
 import ReactDOM from '/node_modules/.vite/deps/react-dom_client.js';
 import {EvaluationPanel} from '/src/EvaluationPanel.tsx';
 let jobs=[];window.batchRequests=[];
 async function api(path,body){
  if(body){window.batchRequests.push({path,body});
   if(path==='evaluations'){jobs=[{id:'frozen',status:'partial',completed_runs:1,total_runs:4,resume_supported:true,directory:'/local/results'}];return jobs[0];}
   if(path==='evaluations/frozen/resume'){jobs=[{...jobs[0],status:'complete',completed_runs:4,resume_supported:false}];return jobs[0];}
   throw Error('Unexpected action');
  }
  if(path==='evaluations')return jobs;
  throw Error('Unexpected read');
 }
 ReactDOM.createRoot(document.getElementById('test-root')).render(React.createElement(EvaluationPanel,{
 assets:[{id:'source',name:'Synthetic source',duration_s:3,person_ids:['one']}],presets:[{id:'reference',name:'Reference',algorithm:{id:'baseline'}}],calibrations:[],person:'one',api,run:fn=>fn()}));
 `});
 await page.getByRole('checkbox',{name:'Reference · baseline'}).check();
 await page.getByRole('checkbox',{name:'Synthetic source'}).check();
 await page.getByRole('spinbutton',{name:'Máximo de corridas por tanda'}).fill('1');
 await page.getByRole('button',{name:'Comparar presets',exact:true}).click();
 await expect(page.getByRole('button',{name:'Continuar comparación congelada'})).toBeVisible();
 await expect(page.getByText('partial · 1/4 corridas',{exact:false})).toBeVisible();
 await page.getByRole('spinbutton',{name:'Máximo de corridas por tanda'}).fill('3');
 await page.getByRole('button',{name:'Continuar comparación congelada'}).click();
 await expect(page.getByRole('button',{name:'Ver comparación',exact:true})).toBeVisible();
 await expect(page.getByRole('button',{name:'Continuar comparación congelada'})).toHaveCount(0);
 const requests=await page.evaluate(()=>(window as any).batchRequests);
 expect(requests[0].path).toBe('evaluations');expect(requests[0].body.max_runs_per_invocation).toBe(1);
 expect(requests[0].body.pcm.enabled).toBe(false);
 expect(requests[1]).toEqual({path:'evaluations/frozen/resume',body:{max_runs:3}});
});
