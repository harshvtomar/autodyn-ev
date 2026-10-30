"""Isolated Chromium browser test through real local Python API (NOT Mac Chrome)."""
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError
import re,threading,json,os,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from autodyn_ev.server import Handler
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parents[1]
server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
base=f'http://127.0.0.1:{server.server_port}'
results=[]

def check(name,condition):
 results.append((name,bool(condition)))
 if not condition: raise AssertionError(name)

def backend_fetch(path,opts=None):
 opts=opts or {}
 request=Request(base+path,data=opts['body'].encode() if 'body' in opts else None,
                 headers=opts.get('headers') or {},method=opts.get('method','GET'))
 try:
  with urlopen(request,timeout=30) as resp:status=resp.status;body=resp.read().decode();mime=resp.headers.get('Content-Type','text/plain')
 except HTTPError as err:status=err.code;body=err.read().decode();mime=err.headers.get('Content-Type','application/json')
 return {'status':status,'body':body,'mime':mime}

html=(root/'web/index.html').read_text()
html=re.sub(r'<link rel="stylesheet" href="/styles.css"\s*/>','<style>'+ (root/'web/styles.css').read_text()+'</style>',html)
sources=re.findall(r'<script src="/([^"]+)" defer></script>',html)
html=re.sub(r'<script src="/([^"]+)" defer></script>','',html)
bridge='''<script>window.fetch=async (url,options={})=>{const out=await window.backendFetch(String(url),options);return new Response(out.body,{status:out.status,headers:{'Content-Type':out.mime}});};</script>'''
js=''.join('<script>'+(root/'web'/src).read_text().replace('</script>',r'<\/script>')+'</script>' for src in sources)
html=html.replace('</body>',bridge+js+'</body>')
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=os.getenv('CHROMIUM','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
  for width in (1280,390):
   context=browser.new_context(viewport={'width':width,'height':900})
   page=context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
   page.expose_function('backendFetch',backend_fetch)
   page.set_content(html,wait_until='load',timeout=30000)
   page.wait_for_function("document.querySelector('#metric-rms').textContent==='0.906'",timeout=30000)
   check(f'{width}: header confirms hotfix', 'Mass Hotfix' in page.locator('.version').inner_text())
   check(f'{width}: 300kg baseline',page.locator('#metric-rms').inner_text()=='0.906')
   # 'input' marks old values stale; 'change' auto-runs.
   page.evaluate('''() => { const input=document.querySelector('#sprung_mass_kg'); input.value='500';input.dispatchEvent(new Event('input',{bubbles:true}));}''')
   check(f'{width}: old RMS blanked',page.locator('#metric-rms').inner_text()=='—')
   check(f'{width}: stale status', 'Inputs changed' in page.locator('#status').inner_text())
   check(f'{width}: exports disabled while stale',page.locator('#csv').is_disabled())
   page.evaluate('''() => document.querySelector('#sprung_mass_kg').dispatchEvent(new Event('change',{bubbles:true}))''')
   page.wait_for_function("document.querySelector('#metric-rms').textContent==='0.556'",timeout=30000)
   check(f'{width}: auto run 500kg',page.locator('#metric-rms').inner_text()=='0.556')
   check(f'{width}: applied mass visible','sprung mass 500 kg' in page.locator('#status').inner_text())
   check(f'{width}: exports reenabled',page.locator('#csv').is_enabled())
   page.evaluate('''() => { const input=document.querySelector('#sprung_mass_kg');input.value='300';input.dispatchEvent(new Event('input',{bubbles:true}));}''')
   page.locator('#run').click()
   page.wait_for_function("document.querySelector('#metric-rms').textContent==='0.906'",timeout=30000)
   check(f'{width}: manual run restores 300kg',page.locator('#metric-rms').inner_text()=='0.906')
   check(f'{width}: quarter graphs exist',page.locator('#displacement').is_visible() and page.locator('#travel').is_visible())
   check(f'{width}: no JS error',len(errors)==0)
   context.close()
  browser.close()
finally:
 server.shutdown();server.server_close();thread.join(timeout=3)
print(f'Passed {sum(ok for _,ok in results)}/{len(results)} isolated browser checks')
(root/'docs').mkdir(exist_ok=True)
(root/'docs/mass_hotfix_browser_results.json').write_text(json.dumps({'environment':'Isolated Chromium with real Python API forwarded; NOT Mac Chrome acceptance','checks':[{'name':n,'passed':v} for n,v in results]},indent=2))
