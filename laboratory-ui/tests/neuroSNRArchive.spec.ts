import {test,expect} from '@playwright/test';

test('SNR archive recovers lost response and reopens frozen control',async({page})=>{
 test.skip(!process.env.LAB_R11_ARCHIVE_URL,'isolated R11 production UI fixture required');
 const url=process.env.LAB_R11_ARCHIVE_URL!;
 const enter=async()=>{await page.goto(url);await page.getByRole('button',{name:'Investigación',exact:true}).click();};
 await enter();
 const panel=page.getByRole('region',{name:'Control sintético SNR R11',exact:true});
 await panel.getByRole('button',{name:'Calcular control SNR R11'}).click();
 await expect(panel).toContainText('Estado SNR: finite');
 const requests:any[]=[];let lost=false;
 await page.route('**/api/research/r11/snr-records',async route=>{
  if(route.request().method()!=='POST'){await route.continue();return;}
  requests.push(route.request().postDataJSON());
  const response=await route.fetch();
  if(!lost){lost=true;await route.abort('failed');}else await route.fulfill({response});
 });
 await panel.getByRole('button',{name:'Guardar corrida SNR R11',exact:true}).click();
 await expect(panel.getByRole('button',{name:'Recuperar envío SNR R11'})).toBeVisible();
 await enter();
 await panel.getByRole('button',{name:'Recuperar envío SNR R11'}).click();
 await expect(panel.getByRole('button',{name:'Recuperar envío SNR R11'})).toHaveCount(0);
 expect(requests).toHaveLength(2);expect(requests[1]).toEqual(requests[0]);
 await expect(panel.getByRole('button',{name:'Abrir corrida SNR R11'})).toHaveCount(1);
 await panel.getByLabel('Amplitud signal',{exact:true}).fill('7');
 await panel.getByRole('button',{name:'Abrir corrida SNR R11'}).click();
 await expect(panel.getByLabel('Amplitud signal',{exact:true})).toHaveValue('2');
 await expect(panel).toContainText('Corrida SNR recuperada:');
 await expect(panel).toContainText('Estado SNR: finite');
 const response=await page.request.get(url+'/api/research/r11/snr-records');
 const rows=await response.json();expect(rows).toHaveLength(1);
 expect(rows[0].read_verification).toBe('recomputed');
 const frozen=await page.request.get(url+`/api/research/r11/snr-records/${rows[0].id}/artifacts/request.json`);
 expect(await frozen.json()).toEqual(requests[0]);
});
