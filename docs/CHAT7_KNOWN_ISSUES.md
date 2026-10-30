# Chat 7 Known Issues / Scope Boundaries

- **AD-EV-UI-006 (resolved in Chat 7):** Active footer used to say `Chat 5 of 10`. Updated current-revision footer labels, with automated and isolated browser verification. Historical reports retain their true version histories.
- **AD-EV-VIZ-007 (design limitation):** 3D visual is a software-projected, not measured, geometric schematic. Heave and pitch scales deliberately exaggerated. No CAD dimensions or physical tire contact.
- **AD-EV-VIZ-008 (design limitation):** The longitudinal models contain no measured/simulated chassis pitch. Braking 3D keeps vehicle level; only already-computed speed, distance, axle loads and braking/energy channels change.
- **AD-EV-VIZ-009 (documented numeric visualization behavior):** At times between solver grid points, the viewer linearly interpolates the returned channels for display. The underlying model, time series, energy accounting and exports remain unchanged.
- **AD-EV-ENV-010 (pending user acceptance):** The local environment blocked real Chromium navigation to localhost; the isolated Chromium harness passed with the actual UI and precomputed backend responses. Live browser acceptance on Mac pending.
- No physical vehicle validation or engineering safety certification is claimed.
