import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {join} from 'node:path';

for(const condition of ['frozen','prefix'])test(`R13 reserved recordings ${condition}: native import worker repeat and live isolation`,async({page})=>{
 test.skip(!process.env.LAB_R13_RECORDINGS_URL||!process.env.LAB_R13_RECORDINGS_ROOT,'explicit private frozen-recording fixture required');
 const origin=process.env.LAB_R13_RECORDINGS_URL!,root=process.env.LAB_R13_RECORDINGS_ROOT!;
 const requestPath=join(root,condition+'-first','request.json');
 const request=JSON.parse(readFileSync(requestPath,'utf8'));
 const expected=JSON.parse(readFileSync(join(root,condition+'-first','result.json'),'utf8'));
 expect(request.reservation).toBe('take');
 const train=new Set(request.sequences.filter((s:any)=>s.role==='train').map((s:any)=>s.recording_id));
 expect(request.sequences.filter((s:any)=>s.role==='test').every((s:any)=>!train.has(s.recording_id))).toBe(true);
 expect(request.sequences.every((s:any)=>s.provider==='evaluation_features')).toBe(true);
 const errors:string[]=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(origin);const before=await(await page.request.get(`${origin}/api/state`)).json();
 await page.getByRole('button',{name:'Investigación',exact:true}).click();
 const panel=page.getByRole('region',{name:'Transferencia reservada R13'});
 await panel.getByLabel('Importar experimento R13',{exact:true}).setInputFiles(requestPath);
 await expect(panel.getByLabel('Reserva R13',{exact:true})).toHaveValue('take');
 await expect(panel.getByLabel('Horizonte (muestras)',{exact:true})).toHaveValue('6');
 const posted=page.waitForResponse(r=>r.url()===`${origin}/api/research/r13`&&r.request().method()==='POST');
 await panel.getByRole('button',{name:'Correr transferencia R13',exact:true}).click();
 const accepted=await posted;expect(accepted.ok()).toBe(true);const id=(await accepted.json()).id;
 const table=panel.getByRole('table',{name:`Resultados transferencia ${id}`});await expect(table).toBeVisible({timeout:20000});
 const resultResponse=await page.request.get(`${origin}/api/research/r13/${id}/artifacts/result.json`);expect(resultResponse.ok()).toBe(true);
 const actual=await resultResponse.json();
 // Browser JSON normalizes metadata 0.0 to 0; that changes the request digest,
 // not the observations or numerical model. Check those separately from binding.
 const {request_sha256: _expectedDigest,...expectedNumerics}=expected;
 const {request_sha256: actualDigest,...actualNumerics}=actual;
 expect(actualNumerics).toEqual(expectedNumerics);
 const manifest=await(await page.request.get(`${origin}/api/research/r13/${id}/artifacts/manifest.json`)).json();
 expect(actualDigest).toBe(manifest.request_sha256);
 const frozen=await(await page.request.get(`${origin}/api/research/r13/${id}/artifacts/request.json`)).json();expect(frozen).toEqual(request);
 const repeat=page.waitForResponse(r=>r.url()===`${origin}/api/research/r13/${id}/repeat`);
 await table.locator('..').getByRole('button',{name:'Repetir corrida R13',exact:true}).click();const repeated=await repeat;expect(repeated.ok()).toBe(true);const repeatId=(await repeated.json()).id;
 await expect(panel.getByRole('table',{name:`Resultados transferencia ${repeatId}`})).toBeVisible({timeout:20000});
 const repeatedManifest=await(await page.request.get(`${origin}/api/research/r13/${repeatId}/artifacts/manifest.json`)).json();expect(repeatedManifest.hashes).toEqual(manifest.hashes);
 const after=await(await page.request.get(`${origin}/api/state`)).json();expect(after.preset).toEqual(before.preset);expect(after.session.desired_revision).toBe(before.session.desired_revision);
 await expect(panel.getByRole('alert')).toHaveCount(0);expect(errors).toEqual([]);
});
