"""Optional real-backend browser smoke via same-origin HTTP forwarding.

Chromium visits an isolated hostname. Playwright forwards HTTP requests to the
real local AutoDyn server running in this Python process. Actual page scripts
and API outputs are used; this is NOT direct Chrome-on-Mac acceptance.
Requires optional playwright + a Chromium binary, not runtime dependencies.
"""
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from pathlib import Path
import re
import json
import threading
import sys
import os

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from autodyn_ev.server import Handler
from playwright.sync_api import sync_playwright


def run():
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    runner=threading.Thread(target=server.serve_forever,daemon=True)
    runner.start()
    base=f'http://127.0.0.1:{server.server_port}'
    results=[]
    def check(label,boolean):
        results.append({'label':label,'passed':bool(boolean)})
        if not boolean: raise AssertionError(label)

    def backend_fetch(path, options=None):
        options=options or {}
        body=options.get('body')
        if body is not None:
            body=body.encode('utf-8')
        headers=options.get('headers') or {}
        request=Request(base+path,data=body,headers=headers,method=options.get('method','GET'))
        try:
            with urlopen(request,timeout=25) as response:
                code=response.status;payload=response.read();ctype=response.headers.get('Content-Type','text/plain')
        except HTTPError as e:
            code=e.code;payload=e.read();ctype=e.headers.get('Content-Type','application/json')
        return {'status':code,'payload':payload.decode('utf-8'),'content_type':ctype}

    root=Path(__file__).resolve().parents[1]
    html=(root/'web/index.html').read_text()
    css=(root/'web/styles.css').read_text()
    html=re.sub(r'<link rel="stylesheet" href="/styles.css"\s*/>',
                lambda _: '<style>'+css+'</style>',html)
    sources=re.findall(r'<script src="/([^"]+)" defer></script>',html)
    html=re.sub(r'<script src="/([^"]+)" defer></script>','',html)
    bridge="""<script>window.fetch=async (url,opts={})=>{const result=await window.backendFetch(String(url),opts);return new Response(result.payload,{status:result.status,headers:{'Content-Type':result.content_type}});};</script>"""
    js=''.join('<script>'+ (root/'web'/source).read_text().replace('</script>',r'<\/script>')+'</script>' for source in sources)
    html=html.replace('</body>',bridge+js+'</body>')

    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.getenv('CHROMIUM','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
            for width in (1280,390):
                context=browser.new_context(viewport={'width':width,'height':900},accept_downloads=True)
                page=context.new_page();errors=[];page.on('pageerror',lambda exc:errors.append(str(exc)))
                page.expose_function('backendFetch',backend_fetch)
                page.set_content(html,wait_until='load',timeout=20000)
                page.wait_for_timeout(500)
                check(f'{width}: header v1.0',page.locator('.version').inner_text().strip()=='v1.0 · Session 10')
                check(f'{width}: engineering panel',page.locator('#optimization-lab').is_visible())
                check(f'{width}: keyboard skip link', page.locator('a.skip-link').count()==1 and page.locator('main#main-content').count()==1)
                page.keyboard.press('Tab')
                check(f'{width}: skip link keyboard focus',page.evaluate('document.activeElement.classList.contains(\"skip-link\")'))
                check(f'{width}: final release shown', 'Chat 10 of 10' in page.locator('.footer-note').last.inner_text())
                check(f'{width}: projected scene',page.locator('#viz-canvas').is_visible())
                page.evaluate("el=>{el.value='500';el.dispatchEvent(new Event('input',{bubbles:true}));}",page.locator('#sprung_mass_kg').element_handle())
                check(f'{width}: changed quarter input flags stale',page.locator('.metric-grid.stale-results').count()==1)
                page.locator('#run').click()
                page.wait_for_function("document.querySelector('#status').textContent.includes('Verified run: sprung mass 500')",timeout=30000)
                check(f'{width}: updated mass result',abs(float(page.locator('#metric-rms').inner_text())-0.556)<.002)
                check(f'{width}: stale flag clears',page.locator('.metric-grid.stale-results').count()==0)
                page.locator('#reset').click()
                page.wait_for_timeout(300)

                # Regression for the reported Mac acceptance blocker: a mass change
                # must change both the API input and visible RMS, not only the label.
                page.wait_for_function("document.querySelector('#metric-rms').textContent==='0.906'",timeout=15000)
                page.evaluate('''() => {const el=document.querySelector('#sprung_mass_kg');el.value='500';el.dispatchEvent(new Event('input',{bubbles:true}));}''')
                check(f'{width}: input dirty state flagged', 'Inputs changed' in page.locator('#status').inner_text())
                page.locator('#run').click()
                page.wait_for_function("document.querySelector('#metric-rms').textContent==='0.556'",timeout=15000)
                check(f'{width}: changed mass produces new RMS', page.locator('#metric-rms').inner_text()=='0.556')
                check(f'{width}: response provenance visible', 'sprung mass 500 kg' in page.locator('#status').inner_text())
                page.evaluate('''() => {const el=document.querySelector('#sprung_mass_kg');el.value='300';el.dispatchEvent(new Event('input',{bubbles:true}));}''')
                page.locator('#run').click()
                page.wait_for_function("document.querySelector('#metric-rms').textContent==='0.906'",timeout=15000)
                check(f'{width}: restoring mass restores RMS', page.locator('#metric-rms').inner_text()=='0.906')
                page.locator('#opt-run').click()
                page.wait_for_function("document.querySelectorAll('#opt-table-body tr').length === 7",timeout=30000)
                check(f'{width}: 7-case table',page.locator('#opt-table-body tr').count()==7)
                check(f'{width}: study export enabled',page.locator('#opt-json').is_enabled())
                with page.expect_download() as download:
                    page.locator('#opt-json').click()
                saved=download.value
                check(f'{width}: JSON download',saved.suggested_filename.endswith('.json'))
                page.locator('#opt-p2').select_option('suspension_stiffness_n_m')
                page.locator('#opt-run').click()
                page.wait_for_function("document.querySelectorAll('#opt-table-body tr').length === 49",timeout=30000)
                check(f'{width}: 49-case table',page.locator('#opt-table-body tr').count()==49)
                page.locator('#opt-limit-rms').fill('0')
                page.locator('#opt-run').click()
                page.wait_for_function("document.querySelector('#opt-status').textContent.includes('0 feasible')",timeout=30000)
                check(f'{width}: no feasible reported','0 feasible' in page.locator('#opt-status').inner_text())
                page.locator('#opt-limit-rms').fill('')
                page.locator('#opt-model').select_option('half')
                page.locator('#opt-p2').select_option('rear_damping_n_s_m')
                page.locator('#opt-run').click()
                page.wait_for_function("document.querySelectorAll('#opt-table-body tr').length === 49",timeout=30000)
                check(f'{width}: half 49-case',page.locator('#opt-table-body tr').count()==49)
                page.locator('#model-select').select_option('braking')
                page.wait_for_timeout(300)
                check(f'{width}: braking view',page.locator('#braking-lab').is_visible())
                page.locator('#model-select').select_option('regen')
                page.wait_for_timeout(300)
                check(f'{width}: regen view',page.locator('#regen-lab').is_visible())
                page.locator('#viz-mode').select_option('2d')
                page.wait_for_timeout(300)
                check(f'{width}: 2D fallback',page.locator('#viz-fallback').is_visible())
                page.locator('#viz-mode').select_option('3d')
                page.locator('#model-select').select_option('quarter')
                page.screenshot(path=str(root/'docs'/f'chat10-final-{width}.png'),full_page=True)
                check(f'{width}: no JS errors',not errors)
                context.close()
            browser.close()
    finally:
        server.shutdown();server.server_close();runner.join(timeout=2)
    return {'mode':'Isolated Chromium; HTTP requests forwarded to real local API server via Python proxy',
            'not':'direct Mac browser test or physical engineering validation',
            'checks':results,'passed':sum(x['passed'] for x in results),'total':len(results)}

if __name__=='__main__':
    r=run();path=Path('docs/CHAT10_BROWSER_RESULTS.json');path.write_text(json.dumps(r,indent=2)+'\n')
    print(f"Passed {r['passed']}/{r['total']} isolated browser-real-API checks")
