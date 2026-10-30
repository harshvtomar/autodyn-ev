# AutoDyn EV Chat 8 — clean extraction verification

**Release:** `AutoDyn_EV_Chat8_v0.8.0.zip`. Complete source, not a patch.

- ZIP integrity/CRC: **PASS** (no missing/corrupt members).
- Fresh extraction into isolated work directory: **PASS**.
- Python unittest suite: **332/332 PASS** (298 inherited, 34 Chat 8 tests).
- Node syntax checks: **PASS** for all JS files, including new optimization UI.
- Python compilation: **PASS**.
- Original Chat 7 source archive: **unchanged**, SHA-256 `ab402d8b2bb5e213f9e6535b370cc078425e5c9a143454dc564fb7dcc664401c`.
- All 146 baseline files preserved (with five intentionally modified integration files and zero deletions).
- Browser harness: 36/36 passing (isolated desktop/mobile, not live Mac Chrome).
- Legacy physics endpoint JSON: 10/10 byte-identical outputs versus source v0.7.0.

This record is included in the release only because the packaging process requires all statements above to pass before it finishes. Live user Mac acceptance and real vehicle validation remain pending.
