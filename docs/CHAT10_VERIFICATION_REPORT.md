# AutoDyn EV v1.0.0 — Publication correction verification

Date: 29 October 2026.

The supplied MassFixed source checksum was verified as 45699ee0a0c397ad97cca3286549755d74092d147f2d77876cd7b916c858349d. This corrected package is a derivative; see the accompanying checksum for its new identity.

## Correction scope

- Git metadata is informational, not a failing release condition. The audit now works in extracted archives, Git checkouts and worktrees. Eight substantive release checks remain enforced, including the existing heuristic credential scan.
- Added two regression tests covering .git directories and worktree metadata files.
- No physics, API, web UI, export column or numerical algorithm changes.
- Added an export interpretation guide and correctly paired, unchanged user-supplied examples.
- Reconciled final acceptance and test counts; historical evidence remains explicitly historical.

## Evidence

- Original supplied suite: 391/391 passed in this inspection environment.
- Corrected suite: 393 tests (391 inherited + 2 Git-layout regression tests); 393/393 PASS in the correction environment; see PUBLICATION_TEST_LOG.txt.
- Baseline mass response: 300 kg = 0.9060817384; 500 kg = 0.5556923126 m/s².
- Owner Mac acceptance: supplied acceptance handoff records all four final checks as confirmed. Previous browser checks and uploaded file-content inspections substantiate the mass, playback and export evidence. The correction changes no UI or solver code; it is not a new Mac browser run.
- Packaged 46/46 browser, 24/24 download-content and 14/14 no-drift reports are historical results, not reruns in this correction session.
- Public GitHub Actions and hosting have not been executed. The compile, unittest, release-audit and example-export CI commands passed locally inside a Git repository. This is not a hosted CI result.

No real-vehicle validation or certification is claimed. No license has been selected. Public hosting requires a separate backend deployment review.
