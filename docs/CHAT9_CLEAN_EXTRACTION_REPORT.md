# AutoDyn EV Chat 9 v0.9.0 — clean-extraction verification

- Accepted Chat 8 original ZIP hash: `c9919d5ebc406cf30ec652e9f187fa78607b618d20ed48aef217186c9b8a7e7a`; unchanged.
- Original archive integrity: PASS. Initial inherited suite: **332/332 PASS**.
- Source manifest: **162 original files retained**, **0 deleted**, 4 original integration/docs files modified, 8 protected authoritative physics/optimization modules byte-identical.
- Working-tree Chat 9 automated test suite: **372/372 PASS**.
- Pre-release authoritative physics-output comparison: **14/14 exact matches** against separately executed pristine Chat 8 source.
- Optional SciPy DOP853 independent force-balance integration comparison: **6/6 PASS** (development reference tool only).
- Optional Chromium harness with actual Python server responses through an isolated-page bridge: **20/20 PASS**. The bridge does not prove real network-browser deployment or Mac acceptance.
- Final ZIP CRC/integrity check: **PASS**.
- Archive freshly extracted to a separate clean directory; `python3 -m unittest discover -s tests -v`: **372/372 PASS**.
- `python3 -m compileall` and `node --check web/*.js`: **PASS**.
- Live local Mac Chrome/Safari verification: **PENDING**. Experimental real-vehicle validation and GitHub publication: **NOT PERFORMED**.

Only release documentation and verification tooling have been added; no claims of hardware testing, physical calibration or certified safety are made.
