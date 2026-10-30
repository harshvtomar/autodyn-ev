"""OPTIONAL Playwright Chromium isolated-browser interactive QA.

No third-party modules are required by the application. Browser test uses
Playwright installed only in the authoring/checking environment and injects
actual Python service functions for the local-only endpoints.
"""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
from autodyn_ev.simulation import simulate,scenario_from_mapping
from autodyn_ev.analysis import analysis_request

ROOT=Path(__file__).resolve().parent.parent
html=(ROOT/'web/index.html').read_text()
css=(ROOT/'web/styles.css').read_text()
js=(ROOT/'web/app.js').read_text()

def compute(endpoint,data):
    if endpoint=='simulate':return simulate(*scenario_from_mapping(data))
    return analysis_request(endpoint,data)

checks=[]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    for name,viewport in [('desktop',{'width':1440,'height':1050}),('mobile',{'width':390,'height':844})]:
        page=b.new_page(viewport=viewport,accept_downloads=True,device_scale_factor=1)
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(html,wait_until='domcontentloaded')
        page.add_style_tag(content=css)
        page.expose_function('__compute',compute)
        page.evaluate('''() => { window.fetch = async (url, opts) => {
          const endpoint=url.split('/').pop();
          const payload=await window.__compute(endpoint,JSON.parse(opts.body));
          return {ok:true,json:async()=>payload};
        };}''')
        page.add_script_tag(content=js)
        page.wait_for_function('document.getElementById("modal-output").textContent.includes("Mode 1:")',timeout=20000)
        assert float(page.locator('#metric-rms').inner_text()) > .90
        assert page.locator('#displacement').evaluate('(el)=>el.width')>0
        assert page.locator('#acceleration').evaluate('(el)=>el.width')>0
        assert page.locator('#travel').evaluate('(el)=>el.width')>0
        page.locator('#sprung_mass_kg').evaluate('(el)=>{el.value=500;el.dispatchEvent(new Event("input",{bubbles:true}));}')
        page.locator('#compare-run').click()
        page.wait_for_function('document.getElementById("compare-output").textContent.includes("RMS:")',timeout=20000)
        assert page.locator('#compare-plot').evaluate('(el)=>el.width')>0
        assert 'Identical road' in page.locator('#compare-output').inner_text()
        page.locator('#sweep-run').click()
        page.wait_for_function('document.getElementById("sweep-output").textContent.includes("7 controlled runs")',timeout=20000)
        assert page.locator('#sweep-plot').evaluate('(el)=>el.width')>0
        page.locator('#convergence-run').click()
        page.wait_for_function('document.getElementById("convergence-output").textContent.includes("Maximum body")',timeout=20000)
        assert page.locator('#convergence-plot').evaluate('(el)=>el.width')>0
        with page.expect_download() as dl:
            page.locator('#analysis-csv').click()
        assert 'time-step.csv' in dl.value.suggested_filename
        dl.value.save_as(ROOT/f'docs/browser-chat2-{name}-study.csv')
        with page.expect_download() as dl2:
            page.locator('#analysis-json').click()
        assert dl2.value.suggested_filename.endswith('.json')
        with page.expect_download() as dl3:
            page.locator('#provenance').click()
        assert dl3.value.suggested_filename=='autodyn-ev-response-provenance.json'
        page.locator('#road_kind').select_option('flat')
        page.locator('#run').click()
        page.wait_for_function('document.getElementById("metric-rms").textContent === "0.000"',timeout=20000)
        assert page.locator('#metric-travel').inner_text()=='0.00'
        assert page.locator('#metric-mode').inner_text()=='0.91' or float(page.locator('#metric-mode').inner_text())>0
        # Test legacy downloads as well.
        with page.expect_download() as dl4: page.locator('#csv').click()
        assert dl4.value.suggested_filename=='autodyn-ev-session1-response.csv'
        with page.expect_download() as dl5: page.locator('#report').click()
        assert dl5.value.suggested_filename=='autodyn-ev-session1-summary.json'
        page.locator('#play').click()
        assert page.locator('#play').get_attribute('aria-label')=='Play animation'
        assert not errors,errors
        page.screenshot(path=ROOT/f'docs/chat2-dashboard-{name}.png',full_page=True,animations='disabled')
        checks.append({'device':name,'legacy_charts':3,'additional_charts':3,'modal':'pass',
            'controlled_comparison':'pass','sweep':'pass','convergence':'pass',
            'study_exports':'pass','provenance_export':'pass','legacy_exports':'pass',
            'flat_road':'pass','animation':'pass','page_errors':errors,
            'screenshot':f'docs/chat2-dashboard-{name}.png'})
        page.close()
    b.close()
(ROOT/'docs/chat2_browser_harness_results.json').write_text(json.dumps({'method':'isolated Chromium DOM using shipped JS and HTML; fetch bridged to real Python functions','not_verified':'actual localhost browser roundtrip on user Mac', 'cases':checks},indent=2)+'\n')
print(json.dumps(checks,indent=2))
