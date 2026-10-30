"""Acceptance-blocker regression: 300 ↔ 500 kg RMS MUST change."""
import unittest
from pathlib import Path
from autodyn_ev.physics import Vehicle, Road, SimulationSettings
from autodyn_ev.simulation import simulate

ROOT=Path(__file__).resolve().parents[1]

class MassUpdateHotfix(unittest.TestCase):
    def test_300_and_500_different(self):
        a=simulate(Vehicle(sprung_mass_kg=300),Road(),SimulationSettings())
        b=simulate(Vehicle(sprung_mass_kg=500),Road(),SimulationSettings())
        self.assertAlmostEqual(a['metrics']['body_acceleration_rms_m_s2'],.9060817384319384,places=8)
        self.assertAlmostEqual(b['metrics']['body_acceleration_rms_m_s2'],.5556923125715003,places=8)
        self.assertGreater(a['metrics']['body_acceleration_rms_m_s2'],b['metrics']['body_acceleration_rms_m_s2'])
    def test_changed_controls_invalidate_old_values(self):
        js=(ROOT/'web/app.js').read_text()
        self.assertIn('"stale-results"',js)
        self.assertIn('$(id).textContent = "—"',js)
        self.assertIn('$("sprung_mass_kg").addEventListener("change"',js)
    def test_response_mass_verified_before_update(self):
        js=(ROOT/'web/app.js').read_text()
        self.assertLess(js.index('if (!data.vehicle || VEHICLE_FIELDS.some'),js.index('current=data;'))
        self.assertIn('Verified run: sprung mass',js)
    def test_hotfix_marked(self):
        self.assertIn('Session 09 · Mass Hotfix',(ROOT/'web/index.html').read_text())

if __name__=='__main__':unittest.main()
