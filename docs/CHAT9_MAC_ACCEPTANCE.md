# AutoDyn EV Chat 9 — MacBook Air M2 setup and final acceptance

## Installation and run

1. Download and extract `AutoDyn_EV_Chat9_v0.9.0.zip` into `~/Downloads/`. Its root folder is `autodyn-ev-chat9`.
2. Open Terminal and run:

```bash
cd ~/Downloads/autodyn-ev-chat9
python3 -m unittest discover -s tests -v
python3 scripts/chat9_evidence.py --out docs/chat9_evidence
python3 -m autodyn_ev.server --port 8773
```

3. Manually enter `http://127.0.0.1:8773/` in Chrome, **without** a trailing `**` or query string. Port 8773 avoids prior Chat 1–8 servers. If already occupied, use 8774. Keep Terminal open while testing.
4. Expected header: `v0.9 · Session 09`. The footer shows `Chat 9 of 10`. Historical section titles may still refer to their original implementation chats.

## 12 user-verifiable acceptance checkpoints

1. Header `v0.9 · Session 09`, correct Chat 9 footer and visible 3D viewer.
2. Quarter-car defaults display the accepted baseline metrics (~0.906 m/s² RMS, ~48.06 mm peak suspension travel), and animation/graphs still run.
3. Quarter-car changed parameters update results **after** clicking Run simulation (results need not update while sliders are being dragged).
4. Half-car mode displays both axle responses, pitch/heave and default 0.500 s rear delay.
5. Conventional braking at 20 m/s and 5 m/s² reports 4 s and 40 m; grip cap and incomplete-stop handling remain correct.
6. Regenerative braking displays separate recovery/friction/loss components, and zero motor torque or battery power produces zero battery recovery.
7. 3D playback play/pause/restart, scrub, orbit, zoom and 2D fallback continue functioning.
8. Quarter-car optimization: 7 candidates, chart, Pareto identification and selected candidate.
9. Two-parameter 49-case quarter-car and 49-case half-car optimization: sensible table values and consistent road settings.
10. No-feasible constraint case returns a clearly empty feasible set without a false selected optimum; invalid requests are safely rejected.
11. Optimization CSV/JSON/text, legacy simulation CSV/JSON, braking/regen exports download and contain the appropriate source and scenario fields.
12. Narrow-window (~390 px) layout displays controls legibly with no browser console errors; run tests again if file permissions/dependencies differ.

## Verification distinctions

The Python unit suite and optional isolated Chromium checks were performed in a separate execution environment. They do **not** substitute for your local Mac browser checks. Record PASS/FAIL for each item and report screenshots for failures; do not mark Chat 9 formally accepted until confirmed. Physical road-test validation remains outside scope.
