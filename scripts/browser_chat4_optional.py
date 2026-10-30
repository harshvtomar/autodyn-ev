"""Optional Chromium regression. Uses a local HTTP server and an intercepting proxy route.

This does NOT establish real Mac Chrome/Safari acceptance. Optional Playwright is
used only in development, not by the app or user setup.
"""
import json
import threading
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer

from autodyn_ev.server import Handler

OUT=Path(__file__).resolve().parent.parent/'docs'
OUT.mkdir(exist_ok=True)

def main():
    from playwright.sync_api import sync_playwright
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{server.server_port}'
    results=[];errors=[]
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
            def make_page(width):
                import re
                ctx=browser.new_context(viewport={'width':width,'height':900},accept_downloads=True)
                page=ctx.new_page()
                page.on('pageerror',lambda err: errors.append(str(err)))
                def proxy_api(path, payload):
                    req=Request(base+path, data=payload.encode('utf-8'),
                        headers={'Content-Type':'application/json'},method='POST')
                    try:
                        with urlopen(req,timeout=20) as r:
                            return {'status':r.status,'body':r.read().decode()}
                    except HTTPError as e:
                        return {'status':e.code,'body':e.read().decode()}
                page.expose_function('proxyApi',proxy_api)
                page.goto('about:blank')
                page.evaluate('''() => { window.fetch = async (path,options) => {
                    const result = await window.proxyApi(path,options.body);
                    return new Response(result.body,{status:result.status,headers:{'Content-Type':'application/json'}});
                }; }''')
                directory=Path(__file__).resolve().parent.parent/'web'
                html=(directory/'index.html').read_text()
                html=re.sub(r'<script src="[^"]+" defer></script>','',html)
                html=html.replace('<link rel="stylesheet" href="/styles.css" />','')
                page.set_content(html,wait_until='domcontentloaded')
                page.add_style_tag(content=(directory/'styles.css').read_text())
                for script in ['app.js','halfcar.js','ride.js']:
                    page.add_script_tag(content=(directory/script).read_text())
                page.locator('#metric-rms').get_by_text('0.906').wait_for(timeout=12000)
                return page,ctx
            for width in [1280,390]:
                page,ctx=make_page(width)
                def check(name,ok):
                    results.append({'viewport':width,'name':name,'passed':bool(ok)})
                    if not ok:raise AssertionError(f'{width} {name}')
                check('v0.4 homepage',page.locator('.version').inner_text().strip()=='v0.4 · Session 04')
                page.locator('#road_kind').select_option('pothole')
                page.locator('#run').click()
                page.locator('#status').get_by_text('Simulation complete',exact=False).wait_for(timeout=12000)
                check('quarter pothole simulated',page.locator('#road_kind').input_value()=='pothole')
                page.locator('#quarter-ride-run').click()
                page.locator('#quarter-ride-status').get_by_text('Study complete',exact=False).wait_for(timeout=12000)
                check('quarter ride metrics', 'm/s²' in page.locator('#quarter-ride-summary').inner_text())
                check('quarter plot painted',page.locator('#quarter-ride-accel').evaluate('(c)=>c.width>0&&c.height>0'))
                page.locator('#quarter-ride-save').click()
                page.locator('#sprung_mass_kg').fill('500')
                page.locator('#quarter-ride-compare').click()
                page.locator('#quarter-ride-status').get_by_text('baseline overlaid',exact=False).wait_for(timeout=12000)
                check('quarter same-road comparison','baseline overlaid' in page.locator('#quarter-ride-status').inner_text())
                with page.expect_download() as dl:page.locator('#quarter-ride-csv').click()
                check('quarter ride csv',dl.value.suggested_filename.endswith('.csv') and 'road_bump_spacing_m' in Path(dl.value.path()).read_text().splitlines()[0])
                with page.expect_download() as dl:page.locator('#quarter-ride-json').click()
                check('quarter ride json',dl.value.suggested_filename.endswith('.json') and json.loads(Path(dl.value.path()).read_text())['release']=='0.4.0')
                page.locator('#model-select').select_option('half')
                page.locator('#half-road-kind').select_option('double_bump')
                page.locator('#half-run').click()
                page.locator('#half-status').get_by_text('samples',exact=False).wait_for(timeout=12000)
                page.locator('#half-ride-run').click()
                page.locator('#half-ride-status').get_by_text('Study complete',exact=False).wait_for(timeout=12000)
                check('half road/ride study', 'double_bump' in page.locator('#half-ride-status').inner_text())
                check('half chart painted',page.locator('#half-ride-travel').evaluate('(c)=>c.width>0&&c.height>0'))
                page.locator('#half-ride-save').click()
                page.locator('[name="pitch_inertia_kg_m2"]').fill('2000')
                page.locator('#half-ride-compare').click()
                page.locator('#half-ride-status').get_by_text('baseline overlaid',exact=False).wait_for(timeout=12000)
                check('half comparison','baseline overlaid' in page.locator('#half-ride-status').inner_text())
                with page.expect_download() as dl:page.locator('#half-ride-csv').click()
                check('half ride CSV',dl.value.suggested_filename.endswith('.csv') and 'body_pitch_rad' in Path(dl.value.path()).read_text().splitlines()[0])
                with page.expect_download() as dl:page.locator('#half-ride-json').click()
                check('half ride JSON',dl.value.suggested_filename.endswith('.json') and json.loads(Path(dl.value.path()).read_text())['current']['model']=='half')
                page.screenshot(path=str(OUT/f'chat4-dashboard-{width}.png'),full_page=True)
                ctx.close()
            browser.close()
    finally:
        server.shutdown();server.server_close();thread.join(3)
    doc={'mode':'isolated Chromium, intercepted HTTP proxy to local Python application; not live Mac browser acceptance',
         'results':results,'errors':errors}
    (OUT/'chat4_browser_harness_results.json').write_text(json.dumps(doc,indent=2))
    print(json.dumps({'passed':sum(r['passed'] for r in results),'total':len(results),'errors':errors},indent=2))
    if errors or not all(r['passed'] for r in results):raise SystemExit(1)

if __name__=='__main__':main()
