"""Isolated real phone pages -> WebSocket -> native Weaver -> feedback browser.

Run against a task-owned silent receiver with virtual events, never an active
participant's room. Requires the optional existing Playwright developer package.
"""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base',default='http://127.0.0.1:19869/qa-room/pair/')
parser.add_argument('--out',type=Path,required=True)
args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
init="""(() => {window.__permissions=[];for(const name of ['DeviceMotionEvent','DeviceOrientationEvent']){const C=window[name]||class extends Event{};C.requestPermission=async()=>{window.__permissions.push(name);return 'granted';};window[name]=C;}Object.defineProperty(navigator,'wakeLock',{value:{request:async()=>({addEventListener(){},release:async()=>{}})}});window.AudioContext=class{constructor(){throw Error('Browser synthesis is forbidden in the native receiver');}};})()"""
pump="""() => {window.__pump=setInterval(()=>{const t=Date.now()/1000;const o=new Event('deviceorientation');Object.assign(o,{alpha:100+Math.sin(t*.8)*70,beta:20+Math.sin(t)*20,gamma:0});window.dispatchEvent(o);const m=new Event('devicemotion');Object.assign(m,{acceleration:{x:0,y:0,z:2+Math.sin(t*4)}});window.dispatchEvent(m);},20);}"""
checks=[];errors=[]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
 try:
  phones=[]
  for role in ['A','B']:
   context=browser.new_context(viewport={'width':390,'height':844});page=context.new_page();page.add_init_script(init);page.on('pageerror',lambda e:errors.append(str(e)));page.goto(args.base+'phone?device='+role);page.get_by_role('button',name='Iniciar sensores',exact=True).click();page.evaluate(pump);page.get_by_text('Enviando a Weaver',exact=True).wait_for();assert page.evaluate('window.__permissions.sort()')==['DeviceMotionEvent','DeviceOrientationEvent'];phones.append(page)
  op=browser.new_page(viewport={'width':1280,'height':600});op.on('pageerror',lambda e:errors.append(str(e)));op.add_init_script(init);op.goto(args.base);op.get_by_text('2/2 teléfonos enviando',exact=True).wait_for()
  checks.append('Both actual sender pages request both permission paths and feed real native Weaver over persistent WebSockets')
  first=op.locator('#needle-a').get_attribute('transform');op.wait_for_timeout(600);assert op.locator('#needle-a').get_attribute('transform')!=first
  assert op.locator('#outputs span').count()==28
  assert any(float(v.rstrip('%'))>2 for v in op.locator('#outputs span').evaluate_all('(items)=>items.map(x=>x.style.height)'))
  checks.append('Orientation arrows, measured halos, shared support and actual Weaver output bars update without browser synthesis')
  for name in ['resume','pause','cut']:
   box=op.locator('#'+name).bounding_box();assert box and box['y']+box['height']<=600,(name,box)
  op.screenshot(path=str(args.out/'native-pair-desktop.png'),full_page=True)
  async_script="""async()=>{const value=await(await fetch('./api/status')).json();return {accepted:value.accepted,writes:value.metrics.instrument_writes+ (value.metrics.lab_frames_submitted||0)};}"""
  before=op.evaluate(async_script)
  op.evaluate("""() => {window.__slowMonitor=true;const nativeFetch=window.fetch;window.fetch=async(...args)=>{if(window.__slowMonitor&&String(args[0]).endsWith('/api/status'))await new Promise(r=>setTimeout(r,600));return nativeFetch(...args);};}""")
  op.wait_for_timeout(2200);op.evaluate('window.__slowMonitor=false');after=op.evaluate(async_script)
  assert after['accepted']-before['accepted']>=60,(before,after)
  assert after['writes']>before['writes']
  checks.append('600ms monitor delays leave phone streaming and the existing laboratory control submissions running')
  op.get_by_role('button',name='Pausar modulación',exact=True).click();op.get_by_text('Ensayo silencioso · modulación pausada',exact=True).wait_for()
  op.get_by_role('button',name='Continuar modulación',exact=True).click();op.get_by_text('Ensayo silencioso · sin salida de audio',exact=True).wait_for()
  checks.append('Pause/resume are native source/scene actions and retain both phone feeds')
  for width in [320,390,768,1024,1440]:
   op.set_viewport_size({'width':width,'height':800});assert op.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
  op.set_viewport_size({'width':390,'height':844});op.screenshot(path=str(args.out/'native-pair-mobile.png'),full_page=True);phones[0].screenshot(path=str(args.out/'native-pair-phone.png'),full_page=True)
  checks.append('Readable movement feedback reflows from320px; all modulation controls fit1280x600')
  op.get_by_role('button',name='Cortar modulación',exact=True).click();op.get_by_text('Ensayo silencioso · modulación cortada',exact=True).wait_for()
  op.get_by_role('button',name='Continuar modulación',exact=True).click()
  for page in phones:page.get_by_role('button',name='Detener',exact=True).click()
  op.get_by_text('0/2 teléfonos enviando',exact=True).wait_for();assert errors==[],errors
  checks.append('Explicit modulation cut latches until resume; Stop releases the actual role and no virtual stream remains')
  pending=browser.new_page();pending.add_init_script("""(() => {window.__permissionResolvers=[];for(const name of ['DeviceMotionEvent','DeviceOrientationEvent'])window[name].requestPermission=()=>new Promise(resolve=>window.__permissionResolvers.push(resolve));})()""");pending.goto(args.base+'phone?device=A');pending.get_by_role('button',name='Iniciar sensores',exact=True).click();pending.evaluate("() => {window.dispatchEvent(new Event('pagehide'));for(const resolve of window.__permissionResolvers)resolve('granted');}");pending.wait_for_timeout(200);assert pending.locator('#stop').is_disabled();assert pending.locator('#start').is_enabled();assert pending.locator('#status').inner_text()=='Envío detenido'
  checks.append('Leaving while sensor permission is pending cannot restart a stopped phone stream')
  report={'status':'passed','checks':checks,'page_errors':errors,'slow_monitor_counts':{'before':before,'after':after},'scope':'Actual current LaboratoryRuntime and application, private loopback edge, native Weaver, actual WebSocket/browser code and virtual sensors. Silent output; native Shaper HTTP/kernel separately verified in Python. No physical phone, audio device, Mac import or hearing.'}
  (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
 finally:browser.close()
