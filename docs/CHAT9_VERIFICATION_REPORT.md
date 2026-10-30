# AutoDyn EV — Chat 9 v0.9.0 engineering verification report

**Milestone:** Independent Engineering Verification, Sensitivity & Credibility Hardening  
**Source:** accepted Chat 8 v0.8.0, SHA-256 `c9919d5ebc406cf30ec652e9f187fa78607b618d20ed48aef217186c9b8a7e7a`  
**Scope:** Software and numerical-reference evidence only. **No** physical or real-vehicle validation.

## Baseline preservation

- Original archive located, exact SHA-256 verified; full ZIP CRC test passed.
- Original extracted into a separate Chat 9 working directory; unmodified v0.8.0 ZIP retained.
- **332/332 inherited tests passed before any change.** No inherited test files modified.
- Existing `autodyn_ev/physics.py`, `halfcar.py`, `simulation.py`, `braking.py`, `regen.py`, `analysis.py`, `ride.py`, and `optimization.py` remain byte-identical with the accepted v0.8.0 source. No dynamics, numerical integration, constraints, Pareto/selection algorithm, or JSON physics-output semantics altered.

## Added engineering evidence

- `autodyn_ev/verification.py`: independently coded Newton-force balances for 2-DOF and 4-DOF; independent mechanical-energy expressions; direct trapezoidal RMS; independent non-dominated candidate classification, grid, constraint and deterministic selection checks; constant-deceleration closed-form stopping reference.
- `tests/test_verification_chat9.py`: 40 new tests including sign conventions, force/moment balances, energy positivity, axle delay, flat-road equilibrium, smooth-road convergence, braking events, zero regeneration, all legacy API routes, invalid request handling, and API security headers.
- `scripts/chat9_evidence.py`: reproducible 12 engineering-reference cases, six 7-/49-case optimization matrices including zero-feasible outcomes, and six road/time-step ranking sensitivity comparisons.
- `scripts/chat9_no_drift.py`: separately executes pristine Chat 8 and Chat 9 code; **14/14 exact sorted serialized output JSON matches** across four physics modes. See `docs/CHAT9_NO_DRIFT.json`.
- `scripts/chat9_scipy_optional.py`: six numerical cases comparing separately derived force-balance equations integrated with SciPy DOP853 to inherited RK4 quarter/half channels. All six passed, maximum state-channel difference **1.83 × 10⁻⁵** (channel-dependent SI units), against a per-channel absolute tolerance of 2 × 10⁻⁴.
- `scripts/chat9_browser_optional.py`: **20/20** optional Chromium checks at 1280 px and 390 px. The HTML/CSS/JS run inside an isolated document and requests are forwarded to the **real Python API server** through a Python bridge. Checks cover current header, optimization chart/panel, 7/49 candidate rows, half-car 49-case grid, infeasible state, JSON downloads and JS error collection. **This is not direct Mac browser validation** and the bridge limits what can be claimed about networking and deployment.

## Computed sensitivity, not certification

- Quarter-car smooth-sine 0.01 s versus 0.0025 s reference: maximum sampled body-displacement difference ~3.13 × 10⁻⁷ m; 0.005 s versus 0.0025 s ~1.72 × 10⁻⁸ m.
- Half-car smooth-sine 0.01 s versus 0.0025 s: ~1.56 × 10⁻⁷ m; 0.005 s versus 0.0025 s ~8.58 × 10⁻⁹ m.
- Finite bump/pothole cases also refined on aligned time grids (see generated matrix). A fine RK4 result is a **numerical comparison reference**, not physical ground truth; do not assume fourth-order convergence near discontinuities or unaligned event boundaries.
- The 7-case quarter-car damping study selected candidate 1 for bump/pothole but candidate 7 for sinusoidal forcing under these specified simulation inputs. This demonstrates **road-input-dependent ranking**. For the tested values, halving the time step did not change the selected ID; that is not a universal robustness guarantee.
- In a 49-case study, 49 candidate grid positions are examined, not an unconstrained design continuum; feasibility and Pareto classification follow the stored objectives and constraints. The no-feasible case reports selected ID `null`, not an invented optimum.

## Test gates and limitations

| Gate | Evidence | Result |
|---|---|---|
| Pre-edit inherited suite | Baseline test log | 332/332 pass |
| Full stdlib suite after changes | `docs/CHAT9_TEST_LOG.txt` | 372/372 pass |
| Separate physics-output no-drift | `docs/CHAT9_NO_DRIFT.json` | 14/14 exact |
| Optional SciPy DOP853 | `docs/CHAT9_SCIPY_REFERENCES.json` | 6/6 pass |
| Optional Chromium with real API bridge | `docs/CHAT9_BROWSER_RESULTS.json` | 20/20 pass |
| Reproducible engineering matrix | `docs/chat9_evidence/` | 12 + 6 + 6 cases |
| Original physics module preservation | `docs/CHAT9_CHANGE_MANIFEST.json` | Byte-identical |
| Live Mac Chrome acceptance | User action required | PENDING |
| Real physical vehicle comparison | No hardware/measurements supplied | NOT PERFORMED |
| GitHub public deployment | Deferred to Chat 10 | PENDING |

### Model limitations

The suspension calculations use small-displacement linear springs, viscous damping, static-equilibrium-relative coordinates and always-connected linear tire forces, without contact loss or nonlinear geometry. The braking and regeneration models omit ABS, wheel slip, aero/rolling resistance, real motor efficiency maps and dynamic battery state. The optimization output is a bounded discrete trade-off demonstration, **not** a physical optimum, performance guarantee, combined vehicle score, ISO 2631 comfort rating, road-safe braking distance or safety-certified design.

**End state:** Chat 9 implementation, release packaging and clean-extraction verification completed successfully (372/372 tests plus Python/JavaScript syntax checks). Live Mac browser acceptance is still pending. Chat 10 remains preparation-only.
