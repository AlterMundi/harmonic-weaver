import {test,expect} from '@playwright/test';
test('save reload and portable JSON restore drafts without capture or export',async({page})=>{
 const profiles:Record<string,any>={};const mutations:string[]=[];
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  let value:any={status:'idle'},status=200;
  if(path==='/api/captures')value={current:{status:'idle'},jobs:[]};
  if(path==='/api/capture-exports/jobs')value=[];
  if(path==='/api/capture-profiles')value=Object.values(profiles);
  if(path.startsWith('/api/capture-profiles/')&&route.request().method()==='GET')value=profiles[path.split('/').at(-1)!];
  if(route.request().method()==='POST'){
   mutations.push(path);const body=route.request().postDataJSON();
   value={...body,id:body.id||'portable'};
   if(body.capture?.max_seconds==='bad'){status=422;value={detail:'invalid duration'};}
   else if(path==='/api/capture-profiles')profiles[value.id]=value;
  }
  await route.fulfill({status,json:value});
 });
 await page.goto('/tests/capture_harness/');
 await page.getByLabel('Nombre de configuración de captura').fill('Dúo 60 s');
 await page.getByLabel('Duración máxima (s)').fill('60');
 await page.getByRole('checkbox',{name:'Grabar preview de cámara durante esta captura'}).check();
 await page.getByRole('checkbox',{name:'Incluir figura de todos los osciladores grabados'}).check();
 await page.getByLabel('Estilo de figura exportada (JSON)').fill('{"color":"gold","components":true}');
 await page.getByRole('button',{name:'Guardar configuración de captura',exact:true}).click();
 await expect(page.getByText('Configuración guardada.',{exact:true})).toBeVisible();
 expect(profiles.portable.capture.max_seconds).toBe(60);
 expect(Object.keys(profiles.portable).sort()).toEqual(['capture','export','id','name','schema_version']);
 await page.reload();
 await expect(page.getByLabel('Duración máxima (s)')).toHaveValue('120');
 await page.getByRole('combobox',{name:'Configuración guardada',exact:true}).selectOption('portable');
 await page.getByRole('button',{name:'Cargar configuración de captura',exact:true}).click();
 await expect(page.getByLabel('Duración máxima (s)')).toHaveValue('60');
 await expect(page.getByRole('checkbox',{name:'Grabar preview de cámara durante esta captura'})).toBeChecked();
 await expect(page.getByLabel('Estilo de figura exportada (JSON)')).toHaveValue('{"color":"gold","components":true}');
 const json=page.getByLabel('Configuración de captura JSON',{exact:true});
 await json.fill(JSON.stringify({...profiles.portable,capture:{...profiles.portable.capture,max_seconds:'bad'}}));
 await page.getByRole('button',{name:'Aplicar JSON de captura',exact:true}).click();
 await expect(page.getByRole('alert').filter({hasText:'invalid duration'})).toBeVisible();
 await expect(page.getByLabel('Duración máxima (s)')).toHaveValue('60');
 await json.fill(JSON.stringify({...profiles.portable,capture:{...profiles.portable.capture,max_seconds:90}}));
 await page.getByRole('button',{name:'Aplicar JSON de captura',exact:true}).click();
 await expect(page.getByLabel('Duración máxima (s)')).toHaveValue('90');
 expect(profiles.portable.capture.max_seconds).toBe(60); // applying does not overwrite saved profile
 expect(mutations.every(path=>path.startsWith('/api/capture-profiles'))).toBe(true);
});
