import {test,expect} from '@playwright/test';
import {measure,changes,type Values} from '../src/face/geometry';
import {example} from '../src/face/examples';
import {contourDrive,contourVoices,DEFAULT_MAPPING} from '../src/face/contourSound';
const baseline=()=>{const m=measure(example(),800,800,'eyes');if(!m.ok)throw Error(m.reason);return m.values;};
const delta=(id:string)=>{const m=measure(example(id),800,800,'eyes');if(!m.ok)throw Error(m.reason);return changes(m.values,{schema:'face-baseline/v1',center:'eyes',values:baseline(),noise:baseline(),frames:20,durationMs:1900});};
test('geometric bends/openings enrich an integer series; contraction offsets upper partials',()=>{
 const rest=contourVoices(delta('rest'),1,110),wide=contourVoices(delta('wide'),1,110),open=contourVoices(delta('open'),1,110),contract=contourVoices(delta('contract'),1,110);
 expect(rest.filter(v=>v.gain>1e-6)).toHaveLength(3);expect(wide.filter(v=>v.gain>1e-6)).toHaveLength(8);expect(open.filter(v=>v.gain>1e-6)).toHaveLength(8);
 for(const voices of [rest,wide,open])voices.forEach((v,i)=>expect(v.frequency_hz).toBeCloseTo(110*(i+1),8));
 expect(contract[0].frequency_hz).toBe(110);expect(contract[1].frequency_hz).not.toBe(220);
 expect(Object.keys(contourDrive(delta('wide'))!)).not.toContain('emotion');
});
test('digital power stays constant across richness and intended reference partial stays fixed',()=>{
 for(const id of ['rest','wide','smile','contract','open','one'])for(const f0 of [40.4,55,110,220])for(const sensitivity of [.25,1,3]){
  const voices=contourVoices(delta(id),sensitivity,f0);expect(voices).toHaveLength(8);expect(voices[0].frequency_hz).toBe(f0);
  expect(voices.reduce((s,v)=>s+v.gain*v.gain,0)).toBeCloseTo(.22**2,10);
  for(const v of voices){expect(Number.isFinite(v.frequency_hz)).toBe(true);expect(v.frequency_hz).toBeGreaterThanOrEqual(40.4);expect(v.frequency_hz).toBeLessThan(2000);expect(v.gain).toBeGreaterThanOrEqual(0);}
 }
});
test('richness/deviation controls are independent; malformed input cannot create stale invalid audio',()=>{
 expect(contourVoices(delta('wide'),1,110,{...DEFAULT_MAPPING,richness:0}).filter(v=>v.gain>0)).toHaveLength(3);
 contourVoices(delta('contract'),1,110,{...DEFAULT_MAPPING,detune:0}).forEach((v,i)=>expect(v.frequency_hz).toBe(110*(i+1)));
 expect(contourVoices({...delta('rest'),mouth:NaN})).toEqual([]);expect(contourVoices(delta('wide'),1,0)).toEqual([]);
 expect(contourVoices(delta('wide'),1,110,{id:'contour',richness:2,detune:1})).toEqual([]);
});
test('integrated face mode exposes geometry controls and an unchanged legacy option',async({page})=>{
 await page.goto('./?mode=face');await expect(page.getByRole('navigation',{name:'Instrumento del laboratorio'})).toBeVisible();
 await expect(page.getByRole('link',{name:'Cuerpo · HarMoCAP'})).toHaveAttribute('href','./');
 await expect(page.getByLabel('Centro de comparación')).toHaveValue('eyes');await expect(page.getByLabel('Mapeo de contornos')).toHaveValue('contour');
 await page.getByRole('button',{name:'Tomar referencia',exact:true}).click();await expect(page.getByRole('button',{name:'Activar sonido',exact:true})).toBeEnabled({timeout:10000});
 await page.getByLabel('Gesto del ejemplo').selectOption('contract');await expect(page.getByLabel('Respuesta de los contornos')).toContainText('Contracción de cejas');
 await page.getByLabel('Mapeo de contornos').selectOption('legacy');await expect(page.getByLabel('Respuesta de riqueza')).toHaveCount(0);
 await page.getByLabel('Mapeo de contornos').selectOption('contour');await expect(page.getByLabel('Respuesta de riqueza')).toHaveValue('1');
});
