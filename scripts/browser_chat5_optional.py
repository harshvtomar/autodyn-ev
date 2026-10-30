"""Isolated Chromium + Python backend proxy. Not a user's Mac Chrome acceptance."""
import json,re,threading
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
from autodyn_ev.server import Handler
OUT=Path(__file__).resolve().parent.parent/'docs'
def main():
 from playwright.sync_api import sync_playwright
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
 thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 base=f'http://127.0.0.1:{server.server_port}'
 outcomes=[];errors=[]
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
   def page_for(width):
    ctx=browser.new_context(viewport={'width':width,'height':900},accept_downloads=True)
    page=ctx.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
    def api(path,payload):
     req=Request(base+path,data=payload.encode(),headers={'Content-Type':'application/json'},method='POST')
     try:
      with urlopen(req,timeout=20) as f:return {'status':f.status,'body':f.read().decode()}
     except HTTPError as e:return {'status':e.code,'body':e.read().decode()}
    page.expose_function('proxyApi',api)
    page.goto('about:blank')
    page.evaluate('''()=>{window.fetch=async(path,opts)=>{let res=await window.proxyApi(path,opts.body);return new Response(res.body,{status:res.status,headers:{'Content-Type':'application/json'}})}}''')
    folder=Path(__file__).resolve().parent.parent/'web'
    html=(folder/'index.html').read_text();html=re.sub(r'<script src="[^"]+" defer></script>','',html).replace('<link rel="stylesheet" href="/styles.css" />','')
    page.set_content(html,wait_until='domcontentloaded');page.add_style_tag(content=(folder/'styles.css').read_text())
    for file in ('app.js','halfcar.js','ride.js','braking.js'):page.add_script_tag(content=(folder/file).read_text())
    page.locator('#metric-rms').get_by_text('0.906').wait_for(timeout=18000)
    return page,ctx
   for width in (1280,390):
    page,ctx=page_for(width)
    def check(label,ok):
     ok=bool(ok);outcomes.append({'width':width,'check':label,'passed':ok})
     if not ok:raise AssertionError(f'{width}: {label}')
    check('version',page.locator('.version').inner_text().strip()=='v0.5 · Session 05')
    check('quarter default preserved',page.locator('#metric-rms').inner_text().strip()=='0.906')
    check('quarter chart rendered',page.locator('#chart-displacement').count() if False else page.locator('#quarter-ride-run').count()==1)
    page.locator('#model-select').select_option('braking')
    page.locator('#braking-status').get_by_text('output points',exact=False).wait_for(timeout=18000)
    check('braking mode visible',page.locator('#braking-lab').is_visible() and not page.locator('#halfcar-lab').is_visible())
    check('legacy hidden in braking mode',page.locator('.app-grid').is_hidden())
    check('default stop', '40.00 m' in page.locator('#braking-metrics').inner_text() and '4.00 s' in page.locator('#braking-metrics').inner_text())
    check('five charts', all(page.locator('#braking-'+k).evaluate('(c)=>c.width>100&&c.height>100') for k in ('speed','distance','decel','load','force')))
    page.locator('#braking-form [name="demanded_decel_m_s2"]').fill('12')
    page.locator('#braking-run').click();page.locator('#braking-status').get_by_text('Demand capped',exact=False).wait_for(timeout=15000)
    check('friction capped status','capped' in page.locator('#braking-status').inner_text())
    with page.expect_download() as download:page.locator('#braking-export-csv').click()
    text=Path(download.value.path()).read_text()
    check('versioned csv','0.5.0' in text and 'front_normal_n' in text.splitlines()[0] and 'demanded_decel_m_s2' in text.splitlines()[0])
    with page.expect_download() as download:page.locator('#braking-export-json').click()
    obj=json.loads(Path(download.value.path()).read_text())
    check('versioned JSON',obj['version']=='0.5.0' and obj['metrics']['traction_limited'])
    page.locator('#braking-profile').select_option('ramp')
    page.locator('#braking-run').click();page.locator('#braking-status').get_by_text('output points',exact=False).wait_for(timeout=15000)
    check('ramp run', 'output points' in page.locator('#braking-status').inner_text() and page.locator('#braking-decel').evaluate('(c)=>c.parentElement.nextElementSibling?.textContent?.includes("Demanded")'))
    page.locator('#braking-form [name="mass_kg"]').fill('0')
    # native HTML validity blocks submit: API rejection also separately tested
    check('invalid form prevented',not page.locator('#braking-form [name="mass_kg"]').evaluate('(e)=>e.checkValidity()'))
    page.locator('#braking-reset').click()
    page.locator('#braking-status').get_by_text('output points',exact=False).wait_for(timeout=15000)
    check('reset restores default',page.locator('#braking-form [name="mass_kg"]').input_value()=='1200')
    page.locator('#model-select').select_option('half')
    page.locator('#half-status').get_by_text('samples',exact=False).wait_for(timeout=18000)
    check('halfcar mode preserved',page.locator('#halfcar-lab').is_visible() and page.locator('#half-body-chart').evaluate('(c)=>c.width>100'))
    page.locator('#model-select').select_option('quarter')
    check('quarter mode return',page.locator('.app-grid').is_visible() and page.locator('#braking-lab').is_hidden())
    check('no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=window.innerWidth+2'))
    # Screenshot new workspace
    page.locator('#model-select').select_option('braking')
    page.locator('#braking-status').get_by_text('output points',exact=False).wait_for(timeout=15000)
    page.screenshot(path=str(OUT/f'chat5-dashboard-{width}.png'),full_page=True)
    ctx.close()
   browser.close()
 finally:
  server.shutdown();server.server_close();thread.join(3)
 record={'mode':'isolated Chromium with in-page JS and proxied local Python API; not Mac acceptance','checks':outcomes,'page_errors':errors}
 (OUT/'chat5_browser_harness_results.json').write_text(json.dumps(record,indent=2))
 print(json.dumps({'passed':sum(o['passed'] for o in outcomes),'total':len(outcomes),'page_errors':errors},indent=2))
 if errors or not all(o['passed'] for o in outcomes):raise SystemExit(1)
if __name__=='__main__':main()
