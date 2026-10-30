"""Browser download-content audit with the actual Python API and isolated Chromium.
Requires optional Playwright/Chromium for QA only; no runtime dependency.
"""
from http.server import ThreadingHTTPServer
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from pathlib import Path
import json,re,threading,tempfile,sys,os,csv
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from autodyn_ev.server import Handler
ROOT=Path(__file__).resolve().parents[1]
server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
base=f'http://127.0.0.1:{server.server_port}'
checks=[]
def chk(label,ok):
 checks.append({'name':label,'passed':bool(ok)})
 if not ok: raise AssertionError(label)
def backend(path,opts=None):
 opts=opts or {}
 req=Request(base+path,data=opts['body'].encode() if 'body' in opts else None,headers=opts.get('headers') or {},method=opts.get('method','GET'))
 try:
  with urlopen(req,timeout=30) as r:code=r.status;body=r.read().decode();mime=r.headers.get('Content-Type','text/plain')
 except HTTPError as e:code=e.code;body=e.read().decode();mime=e.headers.get('Content-Type','application/json')
 return {'status':code,'payload':body,'mime':mime}
html=(ROOT/'web/index.html').read_text()
html=re.sub(r'<link rel="stylesheet" href="/styles.css"\s*/>','<style>'+(ROOT/'web/styles.css').read_text()+'</style>',html)
sources=re.findall(r'<script src="/([^"]+)" defer></script>',html)
html=re.sub(r'<script src="/([^"]+)" defer></script>','',html)
bridge='''<script>window.fetch=async (path,opts={})=>{const x=await window.backend(String(path),opts);return new Response(x.payload,{status:x.status,headers:{'Content-Type':x.mime}});};</script>'''
js=''.join('<script>'+(ROOT/'web'/s).read_text().replace('</script>',r'<\/script>')+'</script>' for s in sources)
html=html.replace('</body>',bridge+js+'</body>')
with tempfile.TemporaryDirectory() as temp:
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path=os.getenv('CHROMIUM','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
   context=browser.new_context(accept_downloads=True,viewport={'width':1280,'height':900})
   page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.expose_function('backend',backend)
   page.set_content(html,wait_until='load',timeout=30000)
   page.wait_for_function("document.querySelector('#metric-rms').textContent==='0.906'",timeout=30000)
   def grab(selector):
    with page.expect_download(timeout=20000) as d:page.locator(selector).click()
    download=d.value;destination=Path(temp)/download.suggested_filename;download.save_as(destination)
    chk('nonempty '+selector,destination.stat().st_size>50)
    return destination.read_text(encoding='utf-8')
   quarter_csv=grab('#csv');quarter_json=grab('#report')
   chk('quarter CSV includes time channel', 'time_s' in quarter_csv.splitlines()[0])
   chk('quarter CSV 1001 rows',len(quarter_csv.splitlines())==1002)
   chk('quarter summary 300kg',json.loads(quarter_json)['vehicle']['sprung_mass_kg']==300)
   page.locator('#quarter-ride-run').click()
   page.wait_for_function("document.querySelector('#quarter-ride-csv').disabled===false",timeout=30000)
   ride_csv=grab('#quarter-ride-csv');ride_json=grab('#quarter-ride-json')
   chk('ride csv has acceleration', 'body_acceleration_m_s2' in ride_csv.splitlines()[0])
   chk('ride json has result', 'current' in json.loads(ride_json))
   page.locator('#opt-run').click()
   page.wait_for_function("document.querySelector('#opt-json').disabled===false",timeout=30000)
   opt_csv=grab('#opt-csv');opt_json=grab('#opt-json');opt_report=grab('#opt-report')
   chk('opt json seven candidates',len(json.loads(opt_json)['candidates'])==7)
   chk('opt CSV rows',len(list(csv.reader(opt_csv.splitlines())))==8)
   chk('opt report provenance','Selection rule' in opt_report)
   page.locator('#model-select').select_option('braking')
   page.wait_for_function("document.querySelector('#braking-export-json').disabled===false",timeout=30000)
   braking_csv=grab('#braking-export-csv');braking_json=grab('#braking-export-json')
   chk('braking csv has time', 'time_s' in braking_csv.splitlines()[0])
   chk('braking json includes scenario','scenario' in json.loads(braking_json))
   page.locator('#model-select').select_option('regen')
   page.wait_for_function("document.querySelector('#regen-json').disabled===false",timeout=30000)
   regen_csv=grab('#regen-csv');regen_json=grab('#regen-json')
   chk('regen csv energy channels','time_s' in regen_csv.splitlines()[0] and 'energy' in regen_csv.splitlines()[0])
   chk('regen json scenario + channels',all(k in json.loads(regen_json) for k in ('scenario','channels')))
   chk('browser no javascript exceptions',not errors)
   browser.close()
 finally:
  server.shutdown();server.server_close();thread.join(timeout=3)
report={'environment':'isolated Chromium browser+actual local Python API; NOT Mac Chrome','checks':checks,'passed':sum(c['passed'] for c in checks),'total':len(checks)}
(ROOT/'docs/CHAT10_EXPORT_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'Export audit: {report["passed"]}/{report["total"]} checks passed')
