import {test,expect} from '@playwright/test';
import {measure,FEATURES} from '../src/face/geometry';
import {example} from '../src/face/examples';
import {expressionValues,expressionReference,suggestExpression} from '../src/face/expression';
function turn(mesh:ReturnType<typeof example>,yaw:number,pitch=0){return mesh.map(p=>{const x=p.x-.5,y=p.y-.5,z=p.z||0;const xx=x*Math.cos(yaw)+z*Math.sin(yaw),zz=-x*Math.sin(yaw)+z*Math.cos(yaw);return {x:xx+.5,y:y*Math.cos(pitch)-zz*Math.sin(pitch)+.5,z:y*Math.sin(pitch)+zz*Math.cos(pitch)};});}
test('head-relative measurements preserve a gesture through moderate yaw and pitch',()=>{
 const reference=measure(example('wide'),800,800,'eyes','head-aligned');expect(reference.ok).toBe(true);if(!reference.ok)return;
 for(const yaw of [-.65,.65])for(const pitch of [-.2,.2]){const result=measure(turn(example('wide'),yaw,pitch),800,800,'eyes','head-aligned');expect(result.ok).toBe(true);if(result.ok)for(const k of FEATURES)expect(result.values[k]).toBeCloseTo(reference.values[k],7);}
 expect(measure(turn(example('wide'),.65),800,800,'eyes','projected').ok).toBe(false);
});
test('pupil/iris positions never gate or change the expression; steep profile remains unknown',()=>{
 const rest=measure(example(),800,800,'eyes','head-aligned');if(!rest.ok)throw Error();const r=expressionReference(Array.from({length:20},()=>expressionValues(rest)!));
 const mesh=turn(example('wide'),.65,.12);for(let i=468;i<478;i++)mesh[i]={x:NaN,y:999,z:NaN};
 const m=measure(mesh,800,800,'eyes','head-aligned');expect(m.ok).toBe(true);expect(suggestExpression(expressionValues(m),r).id).toBe('joy');
 expect(measure(turn(example(),1.15),800,800,'eyes','head-aligned').ok).toBe(false);
 const bad=example();bad[6]={...bad[168]};expect(measure(bad,800,800,'eyes','head-aligned').ok).toBe(false);
});
test('overlay uses cool contours and a mode change requires a new reference',async({page})=>{
 await page.goto('./?mode=face');await page.getByRole('button',{name:'Tomar referencia',exact:true}).click();await expect(page.getByRole('button',{name:'Activar sonido',exact:true})).toBeEnabled();
 await page.getByLabel('Gesto del ejemplo').selectOption('wide');await expect(page.locator('.face-expression-label')).toHaveText('Alegría posible');
 const colours=await page.locator('.face-contours [stroke],.face-contours [fill]').evaluateAll(els=>els.flatMap(e=>[e.getAttribute('stroke'),e.getAttribute('fill')]).filter(v=>v&&v!=='none'));
 expect(colours).toContain('#c084fc');expect(colours).toContain('#38bdf8');expect(colours).toContain('#60a5fa');expect(colours).toContain('#34d399');
 expect(colours.some(c=>['#ffda8a','#ffcb8b','#ffb4ab'].includes(c!))).toBe(false);
 await page.getByLabel('Seguimiento del rostro',{exact:true}).selectOption('projected');await expect(page.getByRole('button',{name:'Activar sonido',exact:true})).toBeDisabled();
 await expect(page.locator('.face-expression-label')).toHaveText('Sin lectura de expresión');
});
