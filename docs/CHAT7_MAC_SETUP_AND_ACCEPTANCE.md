# AutoDyn EV — Chat 7 Mac Setup & Interactive Acceptance

**Do not overwrite the accepted Chat 6 ZIP.** The new ZIP contains the entire extended project.

## Run locally on MacBook Air M2

1. Download and extract `AutoDyn_EV_Chat7_v0.7.0.zip` into Downloads. This should create `~/Downloads/autodyn-ev-chat7`.
2. In Terminal:

```bash
cd ~/Downloads/autodyn-ev-chat7
python3 --version
python3 -m unittest discover -s tests -v
python3 -m autodyn_ev.server --port 8771
```

3. In Chrome, **manually type exactly** `http://127.0.0.1:8771/` (no `/**` or tracking parameters). Keep Terminal open. If port is occupied, choose `--port 8772` and open that port instead.
4. Header: **`v0.7 · Session 07`**. The new **Model-aware 3D viewer** appears below the intro, before the individual model dashboard. The viewing geometry is illustrative only.

## Required 12-point user acceptance

- [ ] **1. Start and tests:** Python tests all pass on your Mac; page loads and shows `v0.7 · Session 07`.
- [ ] **2. Quarter-car 3D:** viewer starts paused, drawing a sprung body, wheel, spring and road; time-zero readouts are correct. Change road/spring settings and run: model-specific values update.
- [ ] **3. Half-car geometry:** select Half-car · 4 DOF and run; two axle/wheel positions appear; scrub to 0.75 s and observe heave/pitch; pitch is labelled positive nose-up.
- [ ] **4. Quarter/half physics regression:** old 2D animation, road studies, plots, numerical metrics, API and CSV/JSON work as before.
- [ ] **5. Friction braking 3D:** select Braking & load transfer; speed/distance/front/rear load readings appear; at default 4.00 s, speed is 0 m/s and travel is about 40.00 m; no fake pitch movement.
- [ ] **6. Regeneration 3D:** select Regenerative braking · EV; confirm battery-stored energy, regen/friction forces and normal-load indicators match the existing output. Default battery recovery ≈ 76.64 kJ at complete stop.
- [ ] **7. Playback:** Play, Pause, Restart; selected model advances from start to final authoritative time, then stops (no negative speeds). 0.5×, 1× and 2× controls work.
- [ ] **8. Scrub synchronization:** timeline at start, half and end matches displayed exact simulation time and model-dependent numerical readings; model switches reset time safely.
- [ ] **9. Camera and keyboard:** drag to orbit; focus the 3D viewer and use arrow keys; adjust zoom and Reset camera. Ensure model numbers do not change when moving camera.
- [ ] **10. 2D fallback:** select Viewer mode `2D fallback`. SVG diagram and numeric readouts remain available; original engineering graphs and exports are still accessible. Restore `Projected 3D`.
- [ ] **11. Footer/cosmetic fix:** both active quarter/half footer labels say `Chat 7 of 10`, never `Chat 5 of 10`. Historical docs may still mention older milestones.
- [ ] **12. Mobile/accessibility:** narrow Chrome to ~390 px. Inputs, controls, view and readouts remain usable; keyboard focus is visible; if Mac/Chrome has Reduce Motion enabled, 3D view does not auto-play; no uncaught browser errors.

## Common issues

- `Address already in use`: a previous server still occupies the port; use `--port 8772` or stop the earlier server with `Control+C`.
- Browser `{"error":"not found"}`: remove extra `/**` from the URL and type the root address manually.
- 3D unavailable: switch to **2D fallback**. The existing 2D plots, models, tests and exports are independent.
- Input sliders changed but old metrics still shown: click the model's **Run** button; the viewer only displays the most recent completed result, not speculative unsimulated data.
- No Python package installation is required. Optional `node` enables extra pure JavaScript math tests; these are skipped if Node is unavailable.

**Acceptance boundary:** This checklist is for the user's Mac. Isolated browser tests in the development environment do not count as live Mac acceptance. The program does not control real vehicles and must not be used as braking safety guidance.
