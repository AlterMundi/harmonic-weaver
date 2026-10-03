import {test,expect} from '@playwright/test';

test('Fourier bank runs offline, restores portable config and compares common support',async({page})=>{
 test.skip(!process.env.LAB_SAI_FOURIER_URL,'isolated production UI required');
 await page.goto(process.env.LAB_SAI_FOURIER_URL!);
 await page.getByRole('button',{name:'Investigación',exact:true}).click();
 const panel=page.getByRole('region',{name:'Controles Fourier Sai',exact:true});
 await panel.getByLabel('Muestras Fourier',{exact:true}).fill('64');
 await panel.getByLabel('Semillas Fourier (JSON)',{exact:true}).fill('[7,19]');
 const configDownload=page.waitForEvent('download');await panel.getByRole('button',{name:'Exportar configuración Fourier',exact:true}).click();
 const configStream=await(await configDownload).createReadStream();let config='';for await(const chunk of configStream!)config+=chunk.toString();
 expect(JSON.parse(config)).toEqual({schema_version:1,samples:64,hz:60,seeds:[7,19]});
 await panel.getByRole('button',{name:'Correr banco Fourier Sai',exact:true}).click();
 await expect(panel.getByRole('button',{name:'Abrir banco Fourier',exact:true})).toHaveCount(1,{timeout:30000});
 await panel.getByRole('button',{name:'Abrir banco Fourier',exact:true}).click();
 await expect(panel.getByRole('table',{name:'Descriptores sobre soporte Fourier común',exact:true})).toContainText('independent');
 await panel.getByLabel('Semilla de resultado Fourier',{exact:true}).selectOption('19');
 await panel.getByLabel('Escenario Fourier',{exact:true}).selectOption('static');
 await expect(panel).toContainText('Soporte común de tres condiciones: 0/64');
 await expect(panel.getByRole('table',{name:'Descriptores sobre soporte Fourier común',exact:true})).toContainText('Sin soporte');
 const links=panel.getByRole('link',{name:'result.json',exact:true});
 const firstURL=new URL((await links.first().getAttribute('href'))!,page.url()).href;const first=await page.request.get(firstURL);expect(first.ok()).toBeTruthy();const firstBody=await first.body();
 await panel.getByRole('button',{name:'Correr banco Fourier Sai',exact:true}).click();
 await expect(panel.getByRole('button',{name:'Abrir banco Fourier',exact:true})).toHaveCount(2,{timeout:30000});
 const results=await panel.getByRole('link',{name:'result.json',exact:true}).evaluateAll(nodes=>nodes.map(n=>(n as HTMLAnchorElement).href));
 for(const url of results){expect((await(await page.request.get(url)).body()).equals(firstBody)).toBeTruthy();}
 await page.reload();await page.getByRole('button',{name:'Investigación',exact:true}).click();
 await panel.getByRole('button',{name:'Abrir banco Fourier',exact:true}).first().click();
 await expect(panel.getByLabel('Muestras Fourier',{exact:true})).toHaveValue('64');
 await panel.getByLabel('Importar configuración Fourier',{exact:true}).setInputFiles({name:'config.json',mimeType:'application/json',buffer:Buffer.from(config)});
 await expect(panel.getByRole('button',{name:'Abrir banco Fourier',exact:true})).toHaveCount(2);
 await panel.getByLabel('Descriptor Fourier',{exact:true}).selectOption('zone.6.I');
 await expect(panel.getByRole('table',{name:'Preservación espectral Fourier',exact:true})).toContainText('shared');
});
