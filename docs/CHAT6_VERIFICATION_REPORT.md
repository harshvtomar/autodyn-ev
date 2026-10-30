# AutoDyn EV — Chat 6 v0.6.0 Engineering Verification Report

**Date:** 2026-10-29. **Release status:** development/automated tests PASS; **live user Mac browser acceptance PENDING**. This is a software-only educational model, not experimental EV validation.

## Exact accepted origin

`AutoDyn_EV_Chat5_v0.5.0.zip` SHA-256 `fd7f4f37cf615203b90eb94b7250330b5e78e25d4c6c1658022f1ebdb9a4cffa`. ZIP integrity checked before edit and original archive retained unchanged. From an untouched source extraction, all **231/231 inherited tests** passed before Chat 6 code was written. Later, all 231 inherited tests still passed alongside the new tests.

## Executed validations

| Gate | Result | Evidence |
|---|---|---|
| Inherited Chat 1–5 standard-library tests | 231/231 passed | `docs/chat6_automated_test_log.txt` |
| New regenerative physics + API tests | 60/60 passed | `tests/test_regen_chat6.py` |
| Full Python unittest suite | **291/291 passed** | `python3 -m unittest discover -s tests -v` |
| Independent randomized numerical comparison | **100/100 passed** | `scripts/chat6_reference_check_optional.py`, `docs/chat6_scipy_reference_results.json` |
| Desktop and 390px Chromium harness | **35/35 passed** | `scripts/browser_chat6_optional.py`, `docs/chat6_browser_results.json` |
| JS syntax | Passed | `node --check` of all five JavaScript files |
| Python compilation | Passed | `python3 -m compileall -q autodyn_ev` |
| Live user's Mac Chrome/Safari testing | **PENDING** | Requires user's confirmation |
| Real EV / battery / road safety validation | **NOT DONE** | Outside the project scope |
| GitHub publication | **NOT DONE** | Outside this milestone |

The browser checks use an isolated Linux Chromium instance with the real local Python API proxied into an in-page document because direct browser navigation to localhost is administratively restricted in the authoring environment. That is **not** a complete end-to-end Chrome-on-Mac test and should never be reported as one. Optional test packages SciPy/Playwright/Chromium/Node are **not** required to run the standard-library application.

### Independent reference accuracy

100 seeded randomized valid scenarios used **SciPy DOP853**, independently integrating speed, travel distance and motor mechanical regenerative work against the same physical inputs and caps. There were **50 ramp cases** and **65 completed stops**. Worst observed absolute differences:

- Elapsed time: **1.8224150855061794×10⁻⁶ s** (allowed ≤ 0.0002 s).
- Travel distance: **3.3414714337709484×10⁻⁵ m** (allowed ≤ 0.002 m).
- Integrated motor mechanical recovered energy: **0.08375105727827759 J** (case tolerance `max(1 J, mass*initial_speed²*2e-5)`).
- Reported energy-closure residual: **1.1641532182693481×10⁻¹⁰ J** maximum.

These are numerical agreement metrics under the **simplified** assumed physics, not general model-to-real-world accuracy. Mechanical regen and friction work are each separately quadrature-integrated; the published friction energy uses conservation closure and the pre-closure residual is exposed in `uncorrected_work_quadrature_residual_j`.

### Compatibility and known constraints

- The v0.5.0 `autodyn_ev/braking.py` and all inherited test files are preserved byte-for-byte. The original braking endpoint `/api/braking/simulate` continues to output version 0.5.0 and exact legacy stopping metrics.
- For old compatibility tests `/api/health` still returns `version: 0.4.0` and `application_version: 0.5.0`; the new explicit `release_version: 0.6.0` field records Chat 6's application release.
- Quarter/half-car constant-speed models are untouched; no longitudinal speed is coupled to suspension road delays.
- A linear/ramped single-track friction cap is retained. No ABS, axle-specific tire grip, battery chemistry, charge SOC/thermal map, physical hardware, regeneration safety certification or real-world stopping-distance claim.

## Reproduction

```bash
python3 -m unittest discover -s tests -v
python3 -m autodyn_ev.server --port 8770
# Optional, only with extra verification packages installed:
PYTHONPATH=. python3 scripts/chat6_reference_check_optional.py
python3 scripts/browser_chat6_optional.py
```

The final complete source ZIP is accompanied by a separate `AutoDyn_EV_Chat6_ZIP_SHA256.txt` file and change manifest. Clean extraction/test results are recorded in the final release handoff outside the source tree.
