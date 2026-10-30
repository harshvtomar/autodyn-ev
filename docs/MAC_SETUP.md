# AutoDyn EV — MacBook Air M2 Setup and Acceptance Checklist

## A. Extract ZIP

1. Download `AutoDyn_EV_Chat1_v0.1.0.zip` and double-click it in Finder.
2. Place the extracted `autodyn-ev-chat1` folder inside `~/Downloads` (or adjust the commands below to its actual location).
3. Open **Terminal** using Spotlight (`Command + Space`, type Terminal).

## B. Run exact Terminal commands

```bash
cd ~/Downloads/autodyn-ev-chat1
pwd
python3 --version
python3 -m unittest discover -s tests -v
python3 -m autodyn_ev.server --port 8765
```

- Python **3.10 or newer** is required; macOS with Apple Silicon is supported in principle because the app only uses Python standard library and browser features.
- Avoid `sudo` or global package installation. Nothing has to be installed with pip.
- If port 8765 is busy, run `python3 -m autodyn_ev.server --port 8766` instead.
- Leave Terminal running, and open **http://127.0.0.1:8765/** in Chrome or Safari.
- Stop the server with **Control + C** in Terminal.

## C. Live-browser acceptance (user to verify; not claimed as passed)

- [ ] Website loads with AutoDyn EV header and 4 dashboard metric cards.
- [ ] Initial run shows **1,001 samples** with default settings, and body acceleration RMS ≈ **0.906 m/s²**.
- [ ] All 3 graphs render and have readable axes/legends.
- [ ] Choose **Flat / no input** and Run; body acceleration RMS and suspension travel show zero.
- [ ] Select **Raised cosine bump**, adjust sprung mass to 500 kg, Run; metrics and plots change.
- [ ] Adjust the spring and damper sliders, and confirm the displayed output labels update correctly.
- [ ] Select **Continuous sine wave**, Run; verify an oscillatory response.
- [ ] Pause animation, move time scrubber, resume; sprung body, wheel and ground move.
- [ ] Download CSV and confirm it has header + 1,001 rows for the 5 s / 0.005 s default scenario.
- [ ] Download JSON summary and confirm it contains parameters, metrics and assumptions, but not sample arrays.
- [ ] Resize the window; check mobile layout if available.
- [ ] Change to a deliberately too-fast/short bump for the chosen time step; verify the application displays a safe error instead of an unreliable result.
- [ ] Check browser DevTools Console for errors; note any failures.

**Note:** Mac acceptance is intentionally left unchecked until you run it. An isolated Chromium test harness passed under the authoring runtime, but actual navigation to its HTTP server was blocked in that environment.

## D. Export canonical example again (optional)

Open a second Terminal tab while server is running, or stop the server and run:

```bash
cd ~/Downloads/autodyn-ev-chat1
python3 -m scripts.export_example
```

This overwrites only `examples/default_bump_metrics.json` and `examples/default_bump_response.csv` with deterministic reference output.

## E. Troubleshooting

- **`zsh: command not found: python3`**: install a Python 3.x distribution from python.org, close and reopen Terminal, and retry.
- **`No module named autodyn_ev`**: verify `pwd` ends in `/autodyn-ev-chat1`; run commands from the project root.
- **`Address already in use`**: use `--port 8766`, 8767, etc. with the matching browser URL.
- **Blank dashboard**: confirm the server Terminal is still active; refresh the browser; check `http://127.0.0.1:8765/api/health` in another tab. Do not double-click `index.html` directly; the app requires its local API.
- **An under-resolved bump/sine warning**: decrease integrator time step or reduce speed/frequency; do not disable numerical safety checks.
- **Browser cannot connect**: test `curl http://127.0.0.1:8765/api/health` in a second Terminal tab, and verify no VPN/browser policy blocks localhost.

## F. GitHub publication (optional, do not need until ready)

Using GitHub's website, create a new empty repository named `autodyn-ev` under your account. Then in Terminal:

```bash
cd ~/Downloads/autodyn-ev-chat1
git init
git add .
git commit -m "AutoDyn EV v0.1.0: validated quarter-car simulation"
git branch -M main
git remote add origin https://github.com/harshvtomar/autodyn-ev.git
git push -u origin main
```

The commands **assume** you created that repository yourself, are authenticated with GitHub and have permission to push. The link does not exist unless you create it; it is not a claim of publication. Do not commit private vehicle calibration data.
