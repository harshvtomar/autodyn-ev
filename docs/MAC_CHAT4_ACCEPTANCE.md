# AutoDyn EV Chat 4 — MacBook Air M2 setup and acceptance

**Baseline:** user-accepted Chat 3 v0.3.0; **candidate:** Chat 4 v0.4.0. Python 3.10+ and Chrome/Safari; no mandatory `pip`, npm, paid subscription or hosted services.

## Launch

1. Download `AutoDyn_EV_Chat4_v0.4.0.zip` and extract into **Downloads**.
2. Open Terminal and run:

```bash
cd ~/Downloads/autodyn-ev-chat4
python3 -m unittest discover -s tests -v
python3 -m autodyn_ev.server --port 8768
```

3. Open the URL **by typing it manually**, with nothing appended: `http://127.0.0.1:8768/`. The version badge should read `v0.4 · Session 04`. Keep the Terminal open. If 8768 is in use, use another free port (`--port 8769`) and open the corresponding URL. Ctrl+C stops the server. **Do not add `/**`, tracking parameters or other path suffixes**; those previously returned 404 in older sessions.

## User Mac browser acceptance (pending until you personally check)

Check each item and report PASS/FAIL with any screenshot, avoiding claims of physical vehicle validation:

1. **Legacy quarter-car:** quarter-car selected, original charts/animation/CSV, Chat 2 comparison/sweep/convergence; default 300 kg raised-cosine bump reference remains about 0.906 m/s² RMS.
2. **New quarter road inputs:** select *Smooth pothole*, click Run simulation, confirm road displacement goes **negative**; select *Two smooth bumps*, confirm two separated road peaks; select *Frequency chirp*, confirm a changing-frequency road trace. Frequency start/end and ramp duration controls should be visible for chirp.
3. **Quarter ride study:** click **Run ride study** and confirm time-weighted RMS, peak-to-peak suspension travel, tire-deflection proxy, settling (if defined), and three unit-separated charts.
4. **Quarter controlled comparison:** click Save model baseline, modify **only sprung mass**, then Compare saved baseline. Confirm two acceleration traces; if you change the road or duration, a clear comparison-rejection message should appear.
5. **Half-car preservation:** select Half-car · 4 DOF, default heave/pitch and 0.500 s rear delay still work; front/rear graphs and animation render.
6. **Half-car new profile:** select Two smooth bumps, run half-car and study. Confirm the front/rear road peaks are separated by 0.500 seconds at 5 m/s, and the new study reports separate front/rear travel and tire proxies.
7. **Half-car comparison:** Save model baseline, change pitch inertia to 2000 kg·m², compare and confirm a changed response, without altering road or time settings.
8. **Exports:** download *Quarter Ride CSV/JSON* and *Half Ride CSV/JSON*. Inspect that CSV contains `release`, road/vehicle parameters and `time_s`; JSON includes `release: 0.4.0`, `windows`, `metrics`, `waveforms`, `warnings` and the correct `model`.
9. **No false settling/comfort claim:** select sine or chirp, run ride study; post-event settling must say Not defined / not reached. No ISO comfort label is shown.
10. **Responsive/mobile:** Chrome around 390 px width; original and new controls remain usable, study cards stack, graphs plot without horizontal clipping; invalid or under-resolved inputs produce a readable validation message rather than a frozen UI.

## If the application does not load

First check the Terminal output for `AutoDyn EV v0.4.0 running at ...` and ensure the displayed port matches the URL. If a prior server owns the port, stop that server using Ctrl+C or use a different port. If you see `{"error":"not found"}`, manually type the root URL ending only in `/`. If API errors occur, report the error text and selected scenario settings. Keep the original accepted v0.3.0 archive unchanged as a rollback copy.

## Interpretation limits

The new ride-RMS is **unweighted time-integrated RMS**, not ISO 2631. Tire deflection is a **proxy** with permanently engaged tires. Small-angle pitch is conditional and no results are real-vehicle validated. Passing a browser checklist is *software acceptance*, not vehicle design approval.
