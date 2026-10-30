"""Chat 7 presentation-layer contract checks; no physics modules are modified."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from autodyn_ev import __version__
from autodyn_ev.server import FILES, WEB_DIR

ROOT=Path(__file__).resolve().parents[1]

class TestVisualizationIntegration(unittest.TestCase):
    def test_version_current(self):
        self.assertEqual(__version__, '0.7.0')
    def test_local_assets(self):
        for path in ('/viz3d.js','/viz3d_math.js'):
            self.assertIn(path,FILES)
            self.assertTrue((WEB_DIR/FILES[path]).is_file())
    def test_no_remote_script_or_webgl_dependency(self):
        s=(WEB_DIR/'index.html').read_text()
        self.assertIn('src="/viz3d.js"',s)
        self.assertIn('src="/viz3d_math.js"',s)
        self.assertNotIn('https://cdn.',s)
        self.assertNotIn('src="https:',s)
        self.assertIn('id="viz-fallback"',s)
        self.assertIn('id="viz-timeline"',s)
        v=(WEB_DIR/'viz3d.js').read_text()
        self.assertIn("getContext('2d'",v)
        self.assertNotIn("getContext('webgl'",v)
    def test_all_live_footer_labels_fixed(self):
        html=(WEB_DIR/'index.html').read_text()
        self.assertNotIn('AutoDyn EV / Chat 5 of 10',html)
        self.assertIn('AutoDyn EV / Chat 7 of 10',html)
        self.assertIn('v0.7 · Session 07',html)
        self.assertGreaterEqual(html.count('Chat 7 of 10'),2)
    def test_all_model_presentation_hooks(self):
        for file,model in [('app.js','quarter'),('halfcar.js','half'),('braking.js','braking'),('regen.js','regen')]:
            text=(WEB_DIR/file).read_text()
            self.assertIn('autodyn:result',text)
            self.assertIn('model:"'+model+'"',text)
        self.assertIn('autodyn:result',(WEB_DIR/'viz3d.js').read_text())
    @unittest.skipUnless(shutil.which('node'),'Node syntax checks optional')
    def test_js_syntax(self):
        for file in ('viz3d_math.js','viz3d.js','app.js','halfcar.js','braking.js','regen.js'):
            p=subprocess.run(['node','--check',str(WEB_DIR/file)],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,file+': '+p.stderr)
    @unittest.skipUnless(shutil.which('node'),'Node math checks optional')
    def test_pure_presentation_math_node(self):
        p=subprocess.run(['node',str(ROOT/'tests/test_viz_math.cjs')],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)

if __name__=='__main__':unittest.main()
