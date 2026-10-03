import {test,expect} from '@playwright/test';

for(const target of [0,1])test(`evaluation body change clears only segment ${target} calibration`,async({page})=>{
 test.skip(!process.env.LAB_EVAL_CALIBRATION_URL,'isolated production laboratory required');
 const origin=process.env.LAB_EVAL_CALIBRATION_URL!;
 // Declared UI control inventory, not measured body scale or tracking evidence.
 const asset={id:'synthetic-recording',name:'Calibration control video',person_ids:['one','two'],duration_s:10};
 const calibrations=[{id:'scale-one',source_id:asset.id,person_id:'one',torso_scale:.2,measured_at:'synthetic-one'},
                     {id:'scale-two',source_id:asset.id,person_id:'two',torso_scale:.4,measured_at:'synthetic-two'}];
 await page.route(`${origin}/api/media`,r=>r.fulfill({json:[asset]}));await page.route(`${origin}/api/calibrations`,r=>r.fulfill({json:calibrations}));
 await page.route(`${origin}/api/evaluations`,r=>r.request().method()==='POST'?r.fulfill({json:{id:'synthetic-form-control'}}):r.continue());
 const inventory=await(await page.request.get(`${origin}/api/presets`)).json();const preset=inventory.find((p:any)=>p.algorithm.id==='baseline');
 await page.goto(origin);await page.getByRole('button',{name:'Comparar',exact:true}).click();
 await page.getByRole('checkbox',{name:`${preset.name} · baseline`,exact:true}).check();
 await page.getByRole('checkbox',{name:asset.name,exact:true}).check();
 const scales=page.getByRole('combobox',{name:'Calibración de esta fuente',exact:true});
 await scales.nth(0).selectOption('scale-one');
 await page.getByRole('button',{name:'Agregar otro segmento de esta fuente',exact:true}).click();
 await expect(scales.nth(1)).toHaveValue('scale-one');
 const people=page.getByLabel(/Persona de Calibration control video/);
 await people.nth(target).fill('two');await expect(scales.nth(target)).toHaveValue('');
 const posted=page.waitForRequest(r=>r.url()===`${origin}/api/evaluations`&&r.method()==='POST');
 await page.getByRole('button',{name:'Comparar presets',exact:true}).click();const payload=(await posted).postDataJSON();
 expect(payload.segments[target].person_id).toBe('two');expect(payload.segments[target].calibration_id).toBeNull();
 expect(payload.segments[1-target].person_id).toBe('one');expect(payload.segments[1-target].calibration_id).toBe('scale-one');
 // A replacement scale is a fresh explicit choice; interval edits preserve it.
 await scales.nth(target).selectOption('scale-two');await page.getByLabel('Inicio (s)',{exact:true}).nth(target).fill('1');
 const again=page.waitForRequest(r=>r.url()===`${origin}/api/evaluations`&&r.method()==='POST');
 await page.getByRole('button',{name:'Comparar presets',exact:true}).click();expect((await again).postDataJSON().segments[target].calibration_id).toBe('scale-two');
});
