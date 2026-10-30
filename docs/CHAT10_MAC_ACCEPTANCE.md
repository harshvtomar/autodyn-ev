# AutoDyn EV v1.0.0 — Mac Final Release Candidate Acceptance

The supplied owner acceptance handoff records all four final v1.0 checks as confirmed. The following detailed procedure is retained for reproduction, not as a new pending sign-off. This publication correction does not modify UI or physics.

## 1. Clean Mac start

Download and extract `AutoDyn_EV_Chat10_v1.0.0_MassFixed_RC.zip` to your Mac Downloads folder. The top-level folder is `autodyn-ev-chat10`.

```bash
cd ~/Downloads/autodyn-ev-chat10
python3 -m unittest discover -s tests -v
python3 -m autodyn_ev.server --port 8776
```

Expected: **393 tests, OK** (391 inherited plus two publication checks); then `AutoDyn EV v1.0.0 running at http://127.0.0.1:8776/`. Open that exact URL manually, not a ChatGPT-wrapped link. Older ports 8773, 8774 and 8775 may serve other builds. Keep the server running. If port 8776 is occupied use another unused port and match the browser URL.

## 2. Required browser acceptance (all must pass)

1. Header `v1.0 · Session 10`; footer `Chat 10 of 10`; four selectable models; projected 3D viewer and 2D fallback.
2. Default quarter-car: **300 kg → ~0.906 m/s² RMS**. Change to 500 kg, confirm the old metric becomes `—` and exports disable, release slider and confirm RMS **~0.556**, status identifies **500 kg**, and export is re-enabled. Clicking **Run simulation** must also work. Restore 300 kg and verify ~0.906. Do not accept a 500 kg run displaying 0.906.
3. Open a second Terminal in the same project directory: `python3 scripts/check_mass_update.py --port 8776` → PASS for both masses.
4. **Animation:** verify quarter-car native 2D play/pause/scrub and projected 3D play/pause/timeline; visible motion and pause state, half-car front/rear and pitch when selected. Reset camera and 2D fallback.
5. **Exports:** run each scenario, save and **open the downloaded files**, not merely click: quarter CSV/summary, quarter ride CSV/JSON, braking CSV/JSON, regeneration CSV/JSON, optimization CSV/JSON/text report; verify nonempty data and model, parameters and time columns.
6. Half-car: pitch/heave, front and rear input, ~0.500 s default delay.
7. Braking: default ~4 s / 40 m; friction cap and incomplete stopping cases.
8. Regeneration: default ~76.64 kJ stored, zero-torque/charge limit prevents recovery.
9. Optimization: seven and 49 candidates, no feasible under restrictive limits, Pareto markers; correct half-car cases.
10. Browser width ~390 px: no clipping, keyboard focus visible including Skip link; observe Console for JavaScript exceptions.
11. No physical vehicle certification claims; document the numerical and experimental limits accurately.
12. Record PASS/FAIL for every item and take screenshots of mass 500 kg and exported file contents.

### Independent evidence runner (optional)

```bash
python3 scripts/chat9_evidence.py --out docs/chat10_evidence
python3 scripts/chat10_release_audit.py --out docs/CHAT10_RELEASE_AUDIT.json
```

If the 300 → 500 kg Mac retest fails, stop final acceptance and share the v1.0 page screenshot, server Terminal, Chrome Console and Network `POST /api/simulate` request/response. Do **not** publish this release before diagnosis.
