# Chat 9 mass-update hotfix (before Chat 10)

This is an additive UI/debugging hotfix to the **accepted v0.9.0** source, not Chat 10 implementation. The underlying 4 physics modes, numerical algorithms and APIs are unchanged.

## Reason
A Mac acceptance report observed that changing sprung mass 300 → 500 kg while clicking **Run simulation** left the old 0.906 RMS on screen. The root cause on the reported Mac session is unconfirmed; the source backend correctly calculates 0.906 (300 kg) and 0.556 (500 kg).

## Mitigation
- Changing inputs immediately clears old metric numbers and visually flags them stale.
- Releasing the sprung-mass slider triggers recalculation; **Run simulation** remains supported.
- Before displaying the new result, the browser rejects a response carrying the wrong vehicle parameters.
- After a successful run, the status shows **the mass actually simulated and the RMS**.
- The header says **Mass Hotfix** to distinguish this installation from previous browser tabs.
- Exports are disabled while quarter-car inputs are stale.

## Mac acceptance
1. Extract ZIP to `~/Downloads/autodyn-ev-chat9-massfix` and run from that directory.
2. `python3 -m unittest discover -s tests -v`
3. `python3 -m autodyn_ev.server --port 8775`
4. Open **http://127.0.0.1:8775/** manually in Chrome. Verify header contains `Mass Hotfix`.
5. Confirm default **300 kg → 0.906** RMS. Drag sprung mass to 500 kg. Old metrics must blank and status must say inputs changed; on slider release a fresh run should produce **0.556**. Alternatively click **Run simulation**.
6. Move back to 300 kg and verify **0.906** returns.
7. Independently check the API in another Terminal: `cd ~/Downloads/autodyn-ev-chat9-massfix && python3 scripts/check_mass_update.py --port 8775`.

Do not proceed to Chat 10 until steps 5–7 pass on your Mac. If results differ, supply screenshots of the status line, header and Terminal.
