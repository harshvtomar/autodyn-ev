# Chat 3 v0.3.0 Release Notes

**New:** separate 4-DOF half-car (heave, pitch, front/rear wheels) with independently set suspension parameters, spatial front/rear delay, time-domain engineering metrics, compact 2D side-view simulation, four plots, model-specific CSV/JSON and isolated responsive browser tests.

**Unchanged:** Chat 1 2-DOF quarter-car numerical model, original API data contract, original dashboard graphs/animation/exports; Chat 2 baseline/variant study, one-at-a-time sweep, modal and convergence analysis; 95 tests and original Git-agnostic source files. No repository was rewritten. This ZIP carries the files in the accepted parent archive, not a `.git` history (none was supplied).

**Passing:** 136 Python tests; optional reference checks, JS syntax and isolated browser smoke tests. **Not verified:** user's native Mac browser. See acceptance guide. The software is an engineering education simulator, not a safety-certifiable vehicle dynamics solver.
