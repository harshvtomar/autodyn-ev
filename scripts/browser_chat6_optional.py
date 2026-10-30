"""Optional local real Chromium smoke; not a user's Mac acceptance."""
import json, subprocess, sys, time, re
from pathlib import Path
from urllib.request import urlopen
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
port=8876
server=subprocess.Popen([sys.executable,'-m','autodyn_ev.server','--port',str(port)],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
checks=[];errors=[]
def check(name,passed):
    checks.append({'name':name,'pass':bool(passed)})
    if not passed: raise AssertionError(name)
try:
    for _ in range(70):
        try:
            with urlopen(f'http://127.0.0.1:{port}/api/health',timeout=2) as response:
                if response.status==200:break
        except Exception:time.sleep(.1)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True, executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
        for viewport in [1280,390]:
            ctx=browser.new_context(viewport={'width':viewport,'height':900},accept_downloads=True)
            page=ctx.new_page();page.on('pageerror',lambda error: errors.append(str(error)))
            def proxy(path,payload):
                from urllib.request import Request
                from urllib.error import HTTPError
                req=Request(f'http://127.0.0.1:{port}'+path,payload.encode(),{'Content-Type':'application/json'},method='POST')
                try:
                    with urlopen(req,timeout=15) as response:return {'status':response.status,'body':response.read().decode()}
                except HTTPError as ex:return {'status':ex.code,'body':ex.read().decode()}
            page.expose_function('proxyApi',proxy)
            page.goto('about:blank')
            page.evaluate("""()=>{window.fetch=async(path,opts)=>{const r=await window.proxyApi(path,opts.body);return new Response(r.body,{status:r.status,headers:{'Content-Type':'application/json'}})}}""")
            html=(ROOT/'web'/'index.html').read_text()
            html=re.sub(r'<script src="[^"]+" defer></script>','',html).replace('<link rel="stylesheet" href="/styles.css" />','')
            page.set_content(html,wait_until='domcontentloaded')
            page.add_style_tag(content=(ROOT/'web'/'styles.css').read_text())
            for filename in ['app.js','halfcar.js','ride.js','braking.js','regen.js']:
                page.add_script_tag(content=(ROOT/'web'/filename).read_text())
            page.locator('#metric-rms').get_by_text('0.906').wait_for(timeout=15000)
            check(f'{viewport}px homepage rendered',page.locator('#metric-rms').inner_text()=='0.906')
            check(f'{viewport}px Chat6 release label','v0.6' in page.locator('.version').inner_text())
            check(f'{viewport}px legacy selector has all four models',page.locator('#model-select option').count()==4)
            page.locator('#model-select').select_option('regen')
            page.locator('#regen-status').get_by_text('kJ stored',exact=False).wait_for(timeout=10000)
            check(f'{viewport}px regen lab visible',page.locator('#regen-lab').is_visible())
            check(f'{viewport}px metrics',page.locator('#regen-metrics .card').count()==12)
            check(f'{viewport}px graphs',page.locator('#regen-lab .braking-charts canvas').count()==6)
            check(f'{viewport}px initial battery recovery', '76.64 kJ' in page.locator('#regen-status').inner_text())
            check(f'{viewport}px export enabled',page.locator('#regen-csv').is_enabled() and page.locator('#regen-json').is_enabled())
            with page.expect_download() as downloaded:page.locator('#regen-csv').click()
            d=downloaded.value;path=ROOT/'docs'/f'chat6-browser-{viewport}-regen.csv';d.save_as(path)
            source=path.read_text()
            check(f'{viewport}px CSV export',source.startswith('model,version,') and 'cumulative_battery_energy_j' in source and source.count('\n')>30)
            with page.expect_download() as downloaded:page.locator('#regen-json').click()
            d=downloaded.value;path=ROOT/'docs'/f'chat6-browser-{viewport}-regen.json';d.save_as(path)
            r=json.loads(path.read_text());check(f'{viewport}px JSON export',r['version']=='0.6.0' and r['metrics']['battery_energy_stored_j']>0)
            page.locator('#regen-form [name="battery_charge_limit_w"]').fill('0')
            check(f'{viewport}px editable form remains valid',page.locator('#regen-form').evaluate('(f)=>f.checkValidity()'));page.locator('#regen-run').click();page.locator('#regen-status').get_by_text('0.00 kJ stored',exact=False).wait_for(timeout=10000)
            check(f'{viewport}px zero battery case','0.00 kJ stored' in page.locator('#regen-status').inner_text())
            page.locator('#regen-reset').click();page.locator('#regen-status').get_by_text('76.64 kJ stored',exact=False).wait_for(timeout=10000)
            page.locator('#regen-form [name="profile"]').select_option('ramp');page.locator('#regen-run').click();page.wait_for_function("document.getElementById('regen-run').disabled===false && document.getElementById('regen-status').textContent.includes('kJ stored')")
            check(f'{viewport}px ramp controls work',page.locator('#regen-metrics .card').count()==12)
            page.locator('#model-select').select_option('braking')
            check(f'{viewport}px inherited braking visible',page.locator('#braking-lab').is_visible() and page.locator('#regen-lab').is_hidden())
            page.locator('#model-select').select_option('half')
            check(f'{viewport}px inherited halfcar visible',page.locator('#halfcar-lab').is_visible())
            page.locator('#model-select').select_option('quarter')
            check(f'{viewport}px quarter UI restored',page.locator('.app-grid').is_visible())
            page.locator('#model-select').select_option('regen')
            page.screenshot(path=str(ROOT/'docs'/f'chat6-dashboard-{viewport}.png'),full_page=True)
            check(f'{viewport}px horizontal overflow',page.evaluate('document.documentElement.scrollWidth <= window.innerWidth+2'))
            ctx.close()
        browser.close()
    check('no JS exceptions',len(errors)==0)
    print(json.dumps({'checks':len(checks),'passed':sum(int(x['pass']) for x in checks),'errors':errors,'items':checks},indent=2))
    (ROOT/'docs'/'chat6_browser_results.json').write_text(json.dumps({'checks':checks,'errors':errors},indent=2))
finally:
    server.terminate()
    try:server.wait(timeout=5)
    except Exception:server.kill()
