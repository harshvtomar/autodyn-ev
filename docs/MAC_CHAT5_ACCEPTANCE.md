# Chat 5 — MacBook Air M2 setup and 10-point acceptance

## Install/run

1. Extract `AutoDyn_EV_Chat5_v0.5.0.zip` to `~/Downloads/autodyn-ev-chat5` (the ZIP contains this folder).
2. Close earlier server if desired (`Control+C` in the previous Terminal). A different port is also fine.
3. Run:

```bash
cd ~/Downloads/autodyn-ev-chat5
python3 -m unittest discover -s tests -v
python3 -m autodyn_ev.server --port 8769
```

4. Type exactly `http://127.0.0.1:8769/` in the Chrome address bar. Do **not** use a link with an injected `/**` or `?utm_source=...` suffix. If the port is occupied, choose e.g. `--port 8770` and manually open the corresponding URL.
5. Check the header says `v0.5 · Session 05`.

## Manual acceptance (do not claim PASS unless you performed each)

- [ ] **1. Legacy quarter-car:** default RMS approximately 0.906 m/s²; existing plots/animation/ride studies and exports still work.
- [ ] **2. Legacy half-car:** switch to `Half-car · 4 DOF`; heave/pitch, front/rear data, animation and 0.500 s default rear-axle delay still work.
- [ ] **3. Braking mode selection:** `Braking & load transfer` displays independent inputs and five plots; quarter/half panels are hidden but remain accessible on switching back.
- [ ] **4. Constant-demand reference:** default speed 20 m/s and deceleration 5 m/s² yield exactly about 4.00 s stopping time and 40.00 m stopping distance; peak front ~7439 N and minimum rear ~4329 N.
- [ ] **5. Friction limit:** set demanded decel to 12 m/s², keep μ=0.8. Confirm `Demand capped` and actual decel ~7.845 m/s², under the requested 12 m/s².
- [ ] **6. Ramp profile:** select `Linear ramp`, set demanded decel to 5 m/s² and ramp time 1 s, run. Expect ~4.50 s and ~49.792 m from 20 m/s.
- [ ] **7. No brake:** set demanded deceleration to 0, duration 12 s; verify `Not reached`, final speed 20 m/s, travelled distance ~240 m and stopping distance not reported as 240 m.
- [ ] **8. Exports:** restore defaults and download Braking CSV and JSON; confirm CSV columns include `time_s`, `speed_m_s`, `front_normal_n` and repeated v0.5.0/scenario data; JSON includes `version`, `scenario`, `metrics`, `warnings`, `provenance.units` and `channels`.
- [ ] **9. Validation & model separation:** invalid vehicle mass or CG geometry is rejected; returning to quarter/half view preserves the original simulation and road-delay settings rather than coupling to brake speed.
- [ ] **10. Responsive:** narrow Chrome to around 390 px; verify all inputs, cards, graphs, action buttons, and warnings fit without horizontal overflow.

**Failure handling:** note which check fails, the exact values/error, and attach a screenshot. Do not start Chat 6 before either accepting Chat 5 or explicitly recording a deferred non-critical issue.

No physical vehicle tests or Mac-specific browser checks were performed in the development environment; these must be user-confirmed.
