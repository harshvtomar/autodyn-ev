# AutoDyn EV v1.0.0 — Current known issues

## Resolved in publication preparation

- Stale mass response: accepted MassFixed source produces 0.556 m/s² at 500 kg; solver and UI preserved.
- Release audit rejected Git repositories: corrected; Git metadata is informational, with checkout/worktree regression tests.
- Conflicting final status and test counts: current count is 393 (391 inherited + 2 publication tests). Owner Mac acceptance remains attributed to the supplied handoff.
- Mixed export pairings: representative examples are regrouped with a manifest; see EXPORT_GUIDE.md. Original upload contents are unchanged.

## Remaining scope limits

- GitHub publication, hosted CI, and public demo deployment have not been performed.
- Eight-check release audit is a heuristic source scan, not an exhaustive security or asset-rights audit. Review assets before public publication.
- No open-source license selected; do not claim MIT/Apache licensing.
- Model/schema export versions retain historical compatibility values; application release is v1.0.0.
- Braking CSV uses instantaneous ramp demand; configured target is in companion JSON. See EXPORT_GUIDE.md.
- No real-vehicle calibration, tire contact separation, ABS/slip, coupled braking/suspension, ISO certification, or global optimum. Regeneration assumes illustrative constant efficiency.
- Formal accessibility and assistive-technology audits have not been performed.
