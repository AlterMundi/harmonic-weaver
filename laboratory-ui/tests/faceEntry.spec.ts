import {test,expect} from '@playwright/test';
import {setupRecording} from './recordingFixture';
test('facial mirror opens independently while the existing body set stays mounted',async({page,context})=>{
 const fx=await setupRecording(page),before=JSON.stringify(fx.state.preset),source=await page.getByAltText('Cámara en vivo').elementHandle();
 const [mirror]=await Promise.all([context.waitForEvent('page'),page.getByRole('link',{name:'Espejo facial',exact:true}).click()]);
 await expect(mirror.getByRole('heading',{name:'Escuchá tu gesto.'})).toBeVisible();
 expect(JSON.stringify(fx.state.preset)).toBe(before);expect(fx.calls).toEqual([]);expect(await page.getByAltText('Cámara en vivo').evaluate((el:any,old:any)=>el===old,source)).toBe(true);
 await expect(mirror.getByRole('button',{name:'Activar sonido',exact:true})).toBeDisabled();await mirror.close();
});
