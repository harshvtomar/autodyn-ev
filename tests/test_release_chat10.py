"""Additive final release checks; earlier tests are not edited."""
import unittest
from pathlib import Path
from autodyn_ev import __version__, CURRENT_RELEASE_VERSION, ACTIVE_APPLICATION_VERSION, FINAL_RELEASE_VERSION
from autodyn_ev.server import Handler
from scripts.chat10_release_audit import run

ROOT=Path(__file__).resolve().parents[1]
class TestFinalRelease(unittest.TestCase):
    def test_final_version(self): self.assertEqual(FINAL_RELEASE_VERSION,'1.0.0')
    def test_legacy_package_version(self): self.assertEqual(__version__,'0.7.0')
    def test_legacy_current_release(self): self.assertEqual(CURRENT_RELEASE_VERSION,'0.8.0')
    def test_legacy_active_application(self): self.assertEqual(ACTIVE_APPLICATION_VERSION,'0.9.0')
    def test_version_in_ui(self): self.assertIn('v1.0 · Session 10',(ROOT/'web/index.html').read_text())
    def test_footer_in_ui(self): self.assertIn('AutoDyn EV / Chat 10 of 10',(ROOT/'web/index.html').read_text())
    def test_keyboard_skip_link(self): self.assertIn('href="#main-content"',(ROOT/'web/index.html').read_text())
    def test_http_binding_local_only(self): self.assertIn('("127.0.0.1", args.port)',(ROOT/'autodyn_ev/server.py').read_text())
    def test_package_dependency_free(self): self.assertIn('dependencies = []',(ROOT/'pyproject.toml').read_text())
    def test_release_surface_audit(self): self.assertTrue(all(run()['checks'].values()))
    def test_quarter_mass_sensitivity_reference(self):
        from autodyn_ev.physics import Vehicle, Road, SimulationSettings
        from autodyn_ev.simulation import simulate
        base=simulate(Vehicle(sprung_mass_kg=300),Road(),SimulationSettings())
        modified=simulate(Vehicle(sprung_mass_kg=500),Road(),SimulationSettings())
        self.assertEqual(modified['vehicle']['sprung_mass_kg'],500.0)
        self.assertAlmostEqual(base['metrics']['body_acceleration_rms_m_s2'],0.9060817384319384,places=9)
        self.assertAlmostEqual(modified['metrics']['body_acceleration_rms_m_s2'],0.5556923125715003,places=9)
        self.assertGreater(abs(base['metrics']['body_acceleration_rms_m_s2']-modified['metrics']['body_acceleration_rms_m_s2']),0.3)
    def test_mass_diagnostic_script_present(self):
        self.assertTrue((ROOT/'scripts/check_mass_update.py').is_file())
    def test_dashboard_has_stale_result_safeguards(self):
        source=(ROOT/'web/app.js').read_text()
        self.assertIn('stale-results',source)
        self.assertIn('addEventListener("change"',source)
        self.assertIn('for (const id of ["metric-rms"',source)
        self.assertIn('The response used different vehicle parameters',source)
        self.assertIn('Verified run: sprung mass',source)
    def test_project_ci(self): self.assertTrue((ROOT/'.github/workflows/ci.yml').exists())
    def test_math_modules_exist(self):
        for m in ('physics','simulation','halfcar','braking','regen','optimization'):
            self.assertTrue((ROOT/'autodyn_ev'/f'{m}.py').exists())
