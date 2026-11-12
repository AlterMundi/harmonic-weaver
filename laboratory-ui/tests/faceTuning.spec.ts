import {test,expect} from '@playwright/test';
import {contourVoices} from '../src/face/contourSound';
import {voicesFor} from '../src/face/sound';
import {FEATURES,calibrate} from '../src/face/geometry';
import {documentFor,validateSession,csv,V4_PROTOCOL} from '../src/face/research';
import {FACE_FUNDAMENTAL} from '../src/face/tuning';
test('40.4Hz is a real reference partial and survives research export without relabeling history',async()=>{
 const zero=Object.fromEntries(FEATURES.map(k=>[k,0])) as any;
 for(const delta of [zero,{...zero,mouthCurve:-.06},{...zero,browL:-.03,browR:-.03}]){
  const contour=contourVoices(delta);expect(contour[0].frequency_hz).toBe(40.4);expect(voicesFor(delta)[0].frequency_hz).toBe(40.4);
 }
 const aligned=contourVoices({...zero,mouthCurve:-.06});[40.4,80.8,121.2,161.6,202,242.4,282.8,323.2].forEach((hz,i)=>expect(aligned[i].frequency_hz).toBeCloseTo(hz,10));
 expect(contourVoices(zero,1,40.3)).toEqual([]);expect(voicesFor(zero,1,40.3)).toEqual([]);
 const baseline=calibrate(Array.from({length:20},(_,i)=>({time:i*100,values:zero})),'eyes');
 const trial:any={id:'f0',origin:'synthetic',task:'rest',startedAt:new Date().toISOString(),center:'eyes',baseline,durationMs:10000,complete:true,endReason:null,soundEnabled:false,audioEvents:[],sensitivity:1,fundamental:FACE_FUNDAMENTAL,volume:.25,mapping:{id:'contour',richness:1,detune:.8},samples:[{timeMs:0,values:zero,delta:zero}],reflection:{felt:'',perceived:'',tension:null,pleasantness:null}};
 const doc=await documentFor([trial]);expect(doc.schema).toBe('face-mirror-session/v5');expect(validateSession(doc)[0].fundamental).toBe(40.4);expect(csv([trial])).toContain('"fundamental_hz"');expect(csv([trial])).toContain('"40.4"');
 expect(()=>validateSession({...doc,schema:'face-mirror-session/v4',protocol:V4_PROTOCOL})).toThrow();
 expect(validateSession({...doc,schema:'face-mirror-session/v4',protocol:V4_PROTOCOL,trials:[{...trial,fundamental:110}]})[0].fundamental).toBe(110);
});
test('visible base, real Web Audio and legacy comparison keep40.4Hz; explicit reset restores it',async({page})=>{
 await page.addInitScript(()=>{const Original=window.AudioContext;(window as any).__faceOscillators=[];window.AudioContext=class extends Original{createOscillator(){const o=super.createOscillator();(window as any).__faceOscillators.push(o);return o;}};});
 await page.goto('./?mode=face');await expect(page.getByText('Ajustar el instrumento · f₀ 40,4 Hz',{exact:true})).toBeVisible();await page.getByText('Ajustar el instrumento · f₀ 40,4 Hz',{exact:true}).click();
 const f=page.getByLabel('Frecuencia base del rostro',{exact:true});await expect(f).toHaveValue('40.4');await expect(f).toHaveAttribute('step','.1');
 await page.getByRole('button',{name:'Tomar referencia',exact:true}).click();await expect(page.getByRole('button',{name:'Activar sonido',exact:true})).toBeEnabled();await page.getByRole('button',{name:'Activar sonido',exact:true}).click();
 await page.waitForFunction(()=>Math.abs((window as any).__faceOscillators[0]?.frequency.value-40.4)<.01);
 await page.getByLabel('Mapeo de contornos').selectOption('legacy');await page.waitForFunction(()=>Math.abs((window as any).__faceOscillators[0]?.frequency.value-40.4)<.01);
 await f.focus();await f.press('End');await expect(f).toHaveValue('220');await page.getByRole('button',{name:'Volver a 40,4 Hz',exact:true}).click();await expect(f).toHaveValue('40.4');await page.waitForFunction(()=>Math.abs((window as any).__faceOscillators[0]?.frequency.value-40.4)<.01);
 await page.getByRole('button',{name:'Silenciar sonido',exact:true}).click();
});
