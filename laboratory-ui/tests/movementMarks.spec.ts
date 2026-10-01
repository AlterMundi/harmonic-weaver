import {test,expect} from '@playwright/test';
test('marks require explicit save and preserve text after failure',async({page})=>{
 test.skip(!process.env.LAB_COMPONENT_TEST_URL,'isolated Vite required');
 const origin=process.env.LAB_COMPONENT_TEST_URL!;
 await page.route(`${origin}/marks-test`,r=>r.fulfill({contentType:'text/html',body:'<div id="root"></div>'}));
 await page.goto(`${origin}/marks-test`);
 await page.addScriptTag({type:'module',content:`
 import React from '/node_modules/.vite/deps/react.js';
 import ReactDOM from '/node_modules/.vite/deps/react-dom_client.js';
 import {MovementMarks} from '/src/MovementMarks.tsx';
 window.calls=[];window.fail=false;
 ReactDOM.createRoot(document.getElementById('root')).render(React.createElement(MovementMarks,{
 api:async(path,body)=>{window.calls.push({path,body});if(window.fail)throw Error('synthetic');},run:fn=>fn().catch(()=>{})}));
 `});
 const save=page.getByRole('button',{name:'Guardar marca'});
 await expect(save).toBeDisabled();
 await expect(page.getByLabel('Tipo de marca')).toHaveValue('note');
 await page.getByLabel('Tipo de marca').selectOption('preparation');
 await page.getByLabel('Marcar un momento').fill('Preparación percibida');
 expect(await page.evaluate(()=>(window as any).calls)).toEqual([]);
 await page.evaluate(()=>{(window as any).fail=true});await save.click();
 await expect(page.getByLabel('Marcar un momento')).toHaveValue('Preparación percibida');
 await page.evaluate(()=>{(window as any).fail=false});await save.click();
 await expect(page.getByLabel('Marcar un momento')).toHaveValue('');
 await expect(page.getByLabel('Tipo de marca')).toHaveValue('preparation');
 expect(await page.evaluate(()=>(window as any).calls[1])).toEqual({path:'marks',body:{text:'Preparación percibida',category:'preparation'}});
});
