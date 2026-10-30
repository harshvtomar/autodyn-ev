# AutoDyn EV — Chat 3 MacBook Air M2 setup and live browser acceptance

## 1. Run the v0.3.0 source

Extract `AutoDyn_EV_Chat3_v0.3.0.zip` in Downloads; it creates `autodyn-ev-chat3`.

```bash
cd ~/Downloads/autodyn-ev-chat3
python3 --version
python3 -m unittest discover -s tests -v
python3 -m autodyn_ev.server --port 8767
```

Navigate to **http://127.0.0.1:8767/** in Chrome or Safari while the Terminal stays open. Use Ctrl+C to stop. If `Address already in use`, use port 8768 (or close the old server); do **not** kill other applications blindly. Python 3.10+; no `pip install` is necessary for the app. Optional NumPy/SciPy and Playwright harnesses are development-only and do not need to be installed on your Mac.

## 2. Browser checks — verify yourself, do not assume PASS

1. Confirm **v0.3 · Session 03** and **Quarter-car · 2 DOF** is the default selection; ensure the old three plots, animation, 57 legacy behaviors, and Chat 2 analysis panels still work.
2. Select **Half-car · 4 DOF**; confirm the new configuration, four graphs, schematic and metrics render without error. Defaults: body 600 kg, pitch inertia 1000 kg·m², distances 1.2/1.3 m, speed 5 m/s, bump 60 mm, 1.5 m. Road-delay metric should display **0.500 s** (2.5/5).
3. Change **Pitch inertia** to `2000` and press **Run half-car model**. Verify new pitch response differs. Return to defaults using **Defaults**.
4. Change **Road profile → Flat road**, run; body acceleration RMS and peak pitch should both read `0.000`. Restore defaults.
5. Change **Road profile → Step displacement** and run. Inspect that rear road response begins approximately 0.5 s after the front. Check front/rear axle graph.
6. Pause, scrub and replay the half-car schematic; ensure front and rear wheels/body visibly follow changing state as displayed on the timeline.
7. Click **Half-car CSV** and **Half-car JSON**. Open CSV and confirm column names include `body_pitch_rad`, `front_road_m`, `rear_road_m`, `front_suspension_force_n`; inspect JSON for `schema_version: half-car-1.0`, `road_delay_s` and `provenance`. The exports must be downloadable.
8. Return to **Quarter-car · 2 DOF**. Verify legacy baseline comparison, parameter sweep, convergence, original CSV/JSON and animation still work.
9. Narrow the Chrome window to approximately phone width; confirm the model selector remains visible, all fields editable, charts and buttons usable, and panels stack rather than clipping essential controls.
10. Confirm that a deliberately invalid half-car setting (for example `Vehicle speed=0`) is blocked by browser input validation or rejected with a clear API error. Return valid values before final use.

Report pass/fail for each check. Mac interaction is **not** claimed by this release; only your confirmation can close it. Browser screenshots `docs/chat3-dashboard-desktop.png` and `...-mobile.png` were made using an isolated Chromium testing harness, not on your Mac.

## Troubleshooting

- Check `pwd` ends with `autodyn-ev-chat3`. If not, navigate to the extracted folder.
- Run `python3 -m unittest discover -s tests -v`; look for `Ran 136 tests` and `OK` before making changes.
- Keep the terminal open; a stopped server means the page will not respond.
- A root `/favicon.ico` 404 is not a simulation failure.
- Browser cache: hard reload with Shift+Command+R and ensure version badge displays v0.3. The server supplies `Cache-Control: no-store`.
- If tests/exports fail, send the complete Terminal error and browser screenshot before advancing to Chat 4.
