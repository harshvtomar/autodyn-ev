# AutoDyn EV Chat 6 — MacBook Air M2 setup and 12-point live acceptance

**Local Mac browser acceptance is PENDING** until the user actually executes and confirms it. No Mac tests were run by the model's separate browser harness.

1. Download and extract the entire `AutoDyn_EV_Chat6_v0.6.0.zip` in `~/Downloads/` so the directory is named `autodyn-ev-chat6`.
2. Open Terminal and run:

```bash
cd ~/Downloads/autodyn-ev-chat6
python3 --version
python3 -m unittest discover -s tests -v
python3 -m autodyn_ev.server --port 8770
```

3. Open Chrome and **manually type** `http://127.0.0.1:8770/` without added `**` or tracking query strings. Keep Terminal running. If `Address already in use`, choose another free port, e.g. `--port 8771`, and browse to that exact address.

### Acceptance checklist (do not tick without performing)

- [ ] 1. Header reads **v0.6 · Session 06**; all four model choices appear.
- [ ] 2. Original quarter-car default simulation still yields approximately **0.906 m/s² RMS**, graphs, animation and original CSV/summary exports.
- [ ] 3. Original 4-DOF half-car model preserves heave/pitch plots, animation, front/rear results and **0.500 s** default rear-axle delay.
- [ ] 4. Original road profiles, ride studies, modal comparison, parameter sweep, convergence and study exports remain operational.
- [ ] 5. Original **Braking & load transfer** default remains ~**4.00 s** and **40.00 m** at 20 m/s, 5 m/s².
- [ ] 6. Select **Regenerative braking · EV**; run default scenario; expect approximately **76.64 kJ** stored, **13.52 kJ** conversion loss, **149.84 kJ** friction heat, **4.00 s**, **40.00 m**, and **240 kJ** initial kinetic energy. All six plots should be populated.
- [ ] 7. Set motor shaft max torque to **0** and run: stored battery energy becomes 0; friction braking fills demand. Reset defaults.
- [ ] 8. Set battery charging limit to **0**: no stored battery energy. Restore; then set battery power limit to **3000 W** and verify peak battery charge power cannot exceed 3.00 kW.
- [ ] 9. Lower friction coefficient from 0.8 to 0.3: actual brake force is grip-limited and stopping distance increases. Restore defaults.
- [ ] 10. Select **Linear ramp**: stopping time increases relative to the constant-command default and the charts and energy accounting refresh. Set duration to **1 s** to verify an *incomplete stop* is clearly reported with nonzero final kinetic energy.
- [ ] 11. Download **Regen CSV** and **Regen JSON**; check CSV header contains `cumulative_battery_energy_j` and `friction_force_n` and JSON contains `version: 0.6.0`, `provenance`, `scenario`, and `uncorrected_work_quadrature_residual_j` in metrics.
- [ ] 12. Narrow Chrome to approximately 390 px. Check form fields, plots, summaries and buttons stack without horizontal overflow; invalid negative efficiency is rejected. Restore defaults.

**After testing:** report checks as PASS/FAIL rather than assuming screenshots or automated test results prove Mac acceptance. If a check fails, preserve a screenshot and Terminal error. Physical vehicle validation and GitHub publication are separate future tasks and are not included in acceptance.
