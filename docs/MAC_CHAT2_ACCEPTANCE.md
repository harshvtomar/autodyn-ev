# AutoDyn EV Chat 2 — MacBook Air M2 Setup & Acceptance

**Source:** `AutoDyn_EV_Chat2_v0.2.0.zip`. Chat 1 is preserved. Do not use the old `autodyn-ev-chat1` folder for Chat 2 verification.

## 1. Extract and run

Open Finder → Downloads → double-click the Chat 2 ZIP. Open Terminal:

```bash
cd ~/Downloads/autodyn-ev-chat2
python3 --version
python3 -m unittest discover -s tests -v
python3 -m autodyn_ev.server --port 8765
```

Open Chrome or Safari at `http://127.0.0.1:8765/`. If an earlier Chat 1 server is still running on port 8765, **stop its Terminal server with Ctrl+C first**; alternatively start Chat 2 on `--port 8766` and open `http://127.0.0.1:8766/`. Do not accidentally test the old v0.1 page. The top-right badge must read **v0.2 · Session 02**.

**Requirements:** Python 3.10+ with standard library and an updated local browser. No `pip install`, npm, Docker, FreeCAD, model downloads or recurring fees needed. Run on your own Mac; previous authoring tests were performed on Linux.

## 2. Browser acceptance checklist (user-executed, not yet verified on Mac)

1. **Baseline:** App loads with the four original metric cards, original three plots, animated mechanism; no console error. Check first RMS ~0.906 for the default bump.
2. **Modal:** Scroll to `07 / ENGINEERING STUDIES`. Modal card shows **two oscillatory pole pairs**, frequencies ~1.147 Hz and 10.882 Hz, damping ratios ~0.285 and 0.269 with default inputs; note original undamped first mode remains ~1.18 Hz on top.
3. **Compare:** Before changing inputs, click **Save current as baseline**. Change *Sprung mass* to 500 kg, click **Compare to baseline**. Check that baseline and variant overlay lines render and RMS changes. Save an intentionally different road and see the *road changed* caveat.
4. **Sweep:** Choose damper coefficient and click **Run 7-point study**. Check a connected curve, result line and parameter unit. Optionally repeat on spring stiffness. Never describe a sampled minimum as the verified global optimum.
5. **Numerical sensitivity:** Click **Check time-step sensitivity**. Confirm 0.010 / 0.005 / 0.0025 s results and a graph. Read the refinement/discontinuity disclaimer.
6. **New exports:** After a study, click **Study CSV**, **Study JSON**, and **Simulation provenance**. Confirm readable files. In the study CSV look for a `model_revision` and `solver` column; in the provenance JSON look for `model_revision`, `vehicle`, `road`, `units`, `requested_settings`.
7. **Regression:** Select *Flat / no input*, click **Run simulation**; top acceleration and travel must be zero. Change back to the bump; original three plots and animation must work. Download the original **Export CSV** and **Export summary**, and inspect nonempty files.
8. **Responsiveness:** Check desktop and narrow/mobile-width Chrome. New analyses should stack without clipping; canvas graphs visible and buttons clickable.
9. **API:** Optionally visit `http://127.0.0.1:8765/api/health`, expect JSON with version `0.2.0`. The local server intentionally does not expose arbitrary files.

## 3. Troubleshooting

- `Address already in use`: stop old server (Ctrl+C) or use 8766, and ensure URL matches the selected port.
- `No module named autodyn_ev`: move Terminal into `~/Downloads/autodyn-ev-chat2` and verify `autodyn_ev/` is visible via `ls`.
- Old site appears: check top-right badge, stop Chat 1 server and hard-reload Chrome `Cmd+Shift+R`.
- Comparison says different integration settings: save the baseline again after selecting your final duration/integration step; comparison requires the same time grid.
- Analysis refuses resolution: lower simulation duration, lower speed, increase bump length or reduce RK4 dt according to error message.
- If a modal output warns it cannot resolve nearly repeated poles, choose an adjacent damper setting. Do not interpret that as physical instability.

**Mac acceptance stays pending until you personally execute and confirm the checklist.** Chat 2 passes the packaged automated tests, but it is not a calibrated physical EV simulator.
