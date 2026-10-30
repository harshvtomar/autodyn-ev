# AutoDyn EV Chat 8 — MacBook Air M2 setup and 12-check acceptance

## Local setup

1. Extract `AutoDyn_EV_Chat8_v0.8.0.zip` into `~/Downloads/autodyn-ev-chat8` (avoid nested folders; check with Finder).
2. Open Terminal and run:

```bash
cd ~/Downloads/autodyn-ev-chat8
python3 -m unittest discover -s tests -v
python3 -m autodyn_ev.server --port 8772
```

3. Manually type `http://127.0.0.1:8772/` in Chrome. Do not append wildcard characters or URL query parameters. Leave Terminal running. If port 8772 is in use, use 8773 and open that port instead. Python 3 standard library is sufficient. Browser access to the local server is required; no external CDNs or network accounts.
4. Confirm header `v0.8 · Session 08` and footer `Chat 8 of 10`. The new **Explore designs. Show the trade-offs.** lab sits immediately below the 3D viewer.

## 12 Mac acceptance checks (report pass/fail individually)

1. **Version/legacy navigation** — Active v0.8 header/footer; four existing model choices remain accessible.
2. **Quarter-car regression** — Default simulation, three original plots, original 2D animation and existing CSV/JSON exports still work (default RMS display near 0.906 m/s²).
3. **Half-car regression** — Heave/pitch, front/rear axle response, 0.500 s default rear delay, existing graphs and exports still work.
4. **Braking and regeneration** — Independent braking and regenerative views still show correct default stopping/energy results, without new coupled score.
5. **Quarter-car 7-point grid** — Choose quarter, first damper, second `None`, click Run bounded study. Confirm seven candidate rows, RMS units and trade-off chart.
6. **Quarter-car 49-point grid** — Choose second parameter `Spring stiffness`. Confirm exactly 49 cases with deterministic ordering, not more.
7. **Half-car front/rear** — Choose half-car, first front damper, second rear damper. Confirm 49 cases, separate parameter values, heave RMS, and front/rear metrics in JSON.
8. **Constraint feasibility** — Set maximum RMS below all results (e.g. `0`) and rerun; observe zero feasible, no selected case, no crash. Clear the limit; try moderate travel limit and confirm feasible/infeasible cases.
9. **Reproducibility** — Rerun identical study with identical inputs; candidate sequence, objective numbers and Pareto membership must match exactly.
10. **Downloads/provenance** — Download Study CSV, Study JSON, Engineering report; inspect CSV header for release/model/road/solver/constraints and JSON for all candidates, objectives/units and warnings.
11. **3D/2D and responsive** — Test viewer play/pause/scrub, 2D fallback, 390 px Chrome viewport, table horizontal scrolling, visible graphs and usable buttons.
12. **Input validation** — Choose duplicate parameters and check readable error. Verify negative/nonfinite constraints are rejected. Oversized grids via API should respond HTTP 400; the normal UI does not offer >7 points per axis.

### Evidence to report

User-confirmed pass/fail for 12 cases, screenshot(s) of a quarter/half trade-off plot and the downloaded report filenames. The engineering computations in the ZIP were tested in the development environment; live macOS Chrome/Safari acceptance is not claimed until you confirm it. Physics is educational and not physically calibrated.
