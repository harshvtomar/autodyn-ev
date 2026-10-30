> Historical pre-correction document. Current status: CHAT10_VERIFICATION_REPORT.md and KNOWN_ISSUES_CHAT10.md.

# AutoDyn EV v1.0.0 — Final candidate (Chat 10)

**Source of truth:** exact `AutoDyn_EV_Chat9_Mass_Update_Hotfix.zip` (SHA-256 `1acad1e175e021512ff077e741bd839192c4e978d6dad6e076c29c76aa2dc9b3`). Its upstream accepted v0.9.0 ZIP SHA-256 is `d61f75865a6174611940a0789ace26402bd946be888fc867446d3a262241c7b2`. Neither input ZIP was edited.

- Retains **all 376 inherited hotfix Python checks**, including user-confirmed Mac mass update (300 → 500 kg, RMS 0.906 → 0.556).
- Preserves the *hotfix's automatic slider-release recalculation, clearing stale metrics, disabling stale exports, validation of returned vehicle parameters, and applied-mass status*.
- Adds 15 final Chat 10 QA tests. **391/391 tests passed** locally and after source integration; final clean extraction independently retested in the release record.
- 46/46 isolated Chromium browser checks using actual local Python API responses. Additional 24/24 downloaded-export-content checks (not Mac Chrome). 14/14 exact no-drift outputs against hotfix and the accepted original Chat 9 physics code.
- Adds final-release header/footer, `final_release_version` to health API while preserving all older compatibility fields, keyboard skip navigation, responsive checks, security/release audit, portfolio case study and deployment plan.
- Independent models remain separate; no physical certification/road test is claimed.
- **Not published or deployed**. Owner authorization required before any GitHub repo creation, push, public visibility or hosted release.
- **Mac acceptance of merged v1.0.0 pending**: confirm automatic mass refresh, animation, downloaded CSV/JSON contents and local test count. The earlier Chrome test verified the *hotfix*, not yet this merged candidate.
