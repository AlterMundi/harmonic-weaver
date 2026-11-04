const {test,before,after}=require('node:test');
const assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
const {resolve}=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require('../laboratory-ui/node_modules/@playwright/test');
const directory=process.env.CURVE_DEMO_QA_DIR;if(!directory)throw Error('Set CURVE_DEMO_QA_DIR to the private QA folder.');
let browser,url;
before(async()=>{const file=resolve(directory,'qualified-demo.html');execFileSync(process.execPath,[resolve(__dirname,'../research/laboratory/facial_curves/render_demo.mjs'),file]);url=pathToFileURL(file).href;browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']});});
after(async()=>{await browser?.close();});
test('delivered controls preserve center-independent shape and reveal the three-point counterexample',async()=>{
 const page=await browser.newPage();const errors=[],external=[];page.on('pageerror',e=>errors.push(String(e)));page.on('request',r=>{if(/^https?:/.test(r.url()))external.push(r.url());});
 try{
  await page.goto(url);await page.waitForFunction(()=>window.__curveDemo);const read=()=>page.evaluate(()=>({mean:window.__curveDemo.current.meanCurvature,projection:window.__curveDemo.current.meanCenterProjection,inflections:window.__curveDemo.current.inflections,bulge:window.__curveDemo.midpointBulge}));const start=await read();
  await page.locator('#center').fill('-0.85');const moved=await read();assert.ok(Math.abs(start.mean-moved.mean)<1e-9);assert.notEqual(start.projection,moved.projection);
  await page.locator('#opening').fill('0.55');const opened=await read();assert.ok(Math.abs(start.mean-opened.mean)<1e-9);
  await page.locator('#local').fill('0');const simple=await read();await page.locator('#local').fill('0.35');const curved=await read();assert.ok(Math.abs(simple.bulge-curved.bulge)<1e-9);assert.equal(simple.inflections,0);assert.ok(curved.inflections>0);
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);assert.equal(await page.locator('video,audio').count(),0);
  await page.screenshot({path:resolve(directory,'demo-desktop.png'),fullPage:true});
 }finally{await page.close();}
});
test('standalone note fits a narrow screen with readable controls and keyboard access',async()=>{
 const page=await browser.newPage({viewport:{width:390,height:844}});
 try{await page.goto(url);await page.waitForFunction(()=>window.__curveDemo);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.ok(await page.locator('label').first().evaluate(e=>parseFloat(getComputedStyle(e).fontSize)>=16));await page.locator('#compare').focus();await page.keyboard.press('Enter');assert.equal(await page.locator('#local').inputValue(),'0');await page.screenshot({path:resolve(directory,'demo-narrow.png'),fullPage:true});}finally{await page.close();}
});
