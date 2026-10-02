import {test,expect} from '@playwright/test';
test('inferred 3D projections keep coordinates and states explicit',async({page})=>{
 test.skip(!process.env.LAB_R09_VIEW_URL,'isolated fixture required');await page.goto(process.env.LAB_R09_VIEW_URL!);
 const panel=page.getByRole('region',{name:'Observaciones espaciales R09'});
 await panel.getByLabel('Modalidad R09').selectOption('validate');
 await panel.getByLabel('Observaciones JSON R09').fill(JSON.stringify({source_id:'synthetic',subject_slot:'slot',provider:'monocular_3d',dimensions:3,coordinate_frame:'model',units:'model_units',clock:{source_clock:'source',common_clock:'session',offset_s:0,rate:1,uncertainty_s:.1,method:'declared_assumption'},frames:[{index:0,source_time_s:0,points:[{label:'hand',state:'inferred',position:[.1,.2,.3]}]}]}));
 await panel.getByRole('button',{name:'Procesar observaciones R09'}).click();
 const circle=panel.getByLabel('Puntos proyectados R09').locator('circle');await expect(circle).toHaveAttribute('cx','210');await expect(circle).toHaveAttribute('cy','170');await expect(circle).toHaveAttribute('fill','none');
 await panel.getByLabel('Proyección R09').selectOption('0,2');await expect(circle).toHaveAttribute('cy','180');
 await panel.getByLabel('Centro horizontal R09').fill('.1');await expect(circle).toHaveAttribute('cx','200');
 await panel.getByLabel('Escala de vista R09').fill('10000');await expect(circle).toHaveCount(0);await expect(panel.getByText(/fuera del encuadre 1/)).toBeVisible();
});
