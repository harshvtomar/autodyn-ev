# Chat 7 — Release & Clean Extraction Verification

- Immutable baseline: `AutoDyn_EV_Chat6_v0.6.0.zip`, SHA-256 `1d70af9c90c8a2822f449134f672747f5f116c1bffe3ba654135a53de3af4227` matched.
- Baseline ZIP integrity passed. All 291 inherited Python tests passed before editing.
- Source preservation: no original files deleted; physics modules remain byte-identical; all legacy export routines preserved.
- Full suite on modified tree: 298/298 tests passed.
- Independent response hashes: 10/10 exactly identical to pristine Chat 6.
- Browser evidence: 35/35 isolated Chromium checks, 1280px and 390px screenshots, fallback and reduced-motion checks, no page JS errors. This is not a real localhost/Mac test.
- Release archive ZIP integrity: passed (archive CRC and complete member extraction).
- Clean-extraction Python test suite: 298/298 passing.
- User Mac browser acceptance and physical vehicle calibration: pending.

The only changes to `autodyn_ev` are the release metadata and HTTP static asset routes/current release metadata, not model equations.
