"""Optional isolated browser tests: real shipped JS/CSS + real Python simulation functions.
Does NOT establish browser navigation to live localhost, nor Mac testing.
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from autodyn_ev.simulation import simulate,scenario_from_mapping
from autodyn_ev.analysis import analysis_request
from autodyn_ev.halfcar import simulate_half,scenario_half_from_mapping
ROOT=Path(__file__).resolve().parent.parent
html=(ROOT/'web/index.html').read_text()
css=(ROOT/'web/styles.css').read_text()
app=(ROOT/'web/app.js').read_text()
half=(ROOT/'web/halfcar.js').read_text()
def compute(path,body):
    if path.endswith('/halfcar/simulate'):return simulate_half(*scenario_half_from_mapping(body))
    if path=='/api/simulate':return simulate(*scenario_from_mapping(body))
    return analysis_request(path.removeprefix('/api/'),body)
checks=[]
with sync_playwright() as p:
  b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for device,viewport in [('desktop',{'width':1440,'height':960}),('mobile',{'width':390,'height':844})]:
    page=b.new_page(viewport=viewport,device_scale_factor=1,accept_downloads=True)
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(html,wait_until='domcontentloaded')
    page.add_style_tag(content=css)
    page.expose_function('__actual',compute)
    page.evaluate('''() => {window.fetch = async(url,opts)=>{try{const result=await window.__actual(url,JSON.parse(opts.body));return {ok:true,json:async()=>result};}catch(e){return {ok:false,status:400,json:async()=>({error:String(e)})}}};}''')
    page.add_script_tag(content=app)
    page.add_script_tag(content=half)
    page.wait_for_function('document.querySelector("#metric-rms").textContent === "0.906"',timeout=20000)
    assert page.locator('.app-grid').is_visible()
    assert page.locator('#model-select').is_visible(),device
    page.locator('#model-select').select_option('half')
    page.wait_for_function('document.querySelector("#half-rms").textContent !== "—"',timeout=25000)
    assert float(page.locator('#half-rms').inner_text())>0
    assert abs(float(page.locator('#half-delay').inner_text())-.5)<1e-8
    assert page.locator('.app-grid').is_hidden()
    for id in ('half-body-chart','half-axle-chart','half-travel-chart','half-accel-chart','half-sketch'):
      assert page.locator('#'+id).evaluate('(el)=>el.width')>0,id
    old=page.locator('#half-pitch').inner_text()
    page.locator('[name="pitch_inertia_kg_m2"]').fill('2000')
    page.locator('#half-run').click()
    page.wait_for_function('document.querySelector("#half-status").textContent.includes("samples")',timeout=25000)
    assert page.locator('#half-pitch').inner_text()!=old
    page.locator('#half-road-kind').select_option('flat')
    page.locator('#half-run').click()
    page.wait_for_function('document.querySelector("#half-rms").textContent === "0.000"',timeout=25000)
    assert page.locator('#half-pitch').inner_text()=='0.000'
    page.locator('#half-reset').click()
    page.wait_for_function('document.querySelector("#half-rms").textContent !== "0.000"',timeout=25000)
    with page.expect_download() as dl:page.locator('#half-export-csv').click()
    assert dl.value.suggested_filename=='autodyn-ev-chat3-halfcar-response.csv'
    dl.value.save_as(ROOT/f'docs/chat3-browser-{device}-response.csv')
    with page.expect_download() as dl:page.locator('#half-export-json').click()
    assert dl.value.suggested_filename=='autodyn-ev-chat3-halfcar-engineering-report.json'
    page.locator('#half-play').click()
    assert page.locator('#half-play').get_attribute('aria-label')=='Play half-car animation'
    page.locator('#half-scrub').fill('600')
    assert '3.00' in page.locator('#half-time').inner_text()
    page.screenshot(path=ROOT/f'docs/chat3-dashboard-{device}.png',full_page=True,animations='disabled')
    page.locator('#model-select').select_option('quarter')
    assert page.locator('.app-grid').is_visible()
    page.locator('#compare-run').click()
    page.wait_for_function('document.querySelector("#compare-output").textContent.includes("RMS:")',timeout=20000)
    page.locator('#sweep-run').click()
    page.wait_for_function('document.querySelector("#sweep-output").textContent.includes("7 controlled runs")',timeout=20000)
    page.locator('#convergence-run').click()
    page.wait_for_function('document.querySelector("#convergence-output").textContent.includes("Maximum body")',timeout=20000)
    assert not errors,errors
    checks.append({'device':device,'model_selector':'PASS','halfcar_charts':'4 plotted charts','halfcar_schematic':'PASS',
      'halfcar_parameter_variation':'PASS','flat_road_zero':'PASS','exports':'CSV and JSON PASS',
      'animation_controls':'PASS','quartercar_and_chat2_studies':'PASS','javascript_page_errors':errors,
      'screenshot':f'docs/chat3-dashboard-{device}.png'})
    page.close()
  b.close()
(ROOT/'docs/chat3_browser_harness_results.json').write_text(json.dumps({'environment':'isolated Playwright Chromium; functions bridged to Python in-process','not_verified':'browser navigation to localhost, or native Mac browser', 'checks':checks},indent=2)+'\n')
print(json.dumps(checks,indent=2))
