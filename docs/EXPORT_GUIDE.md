# Export versions and scenario pairing

Application release: v1.0.0. Existing export names, model revisions and schema versions are compatibility identifiers, not the application build ID. Values such as 0.3.0, 0.4.0, 0.5.0, 0.6.0 and 0.8.0 are intentionally preserved. Record the source archive checksum alongside exported evidence to identify the application build.

Legacy quarter-car CSV contains 12 time-series columns. Its companion summary contains vehicle, road, settings, sample count and metrics. A provenance sidecar must describe the same scenario. Browser suffixes such as (1) are download counters and do not establish matching pairs.

Reviewed uploads:
- Quarter-car response (1) and (8): 500 kg bump; summary (1) or (7). RMS 0.5556923125715002 m/s².
- Quarter-car response (2) through (7): 300 kg bump; summaries (2) through (6). RMS 0.9060817384319384 m/s².
- Unnumbered response and unnumbered summary: 500 kg sine; RMS 2.5756700730154347 m/s². The unnumbered summary has no dedicated provenance block but includes scenario parameters and assumptions.
- Both separately uploaded provenance sidecars describe a 300 kg bump. Do not attach them to the 500 kg sine or bump pair.

The supplied upload files are retained unchanged. Correctly paired representative examples are in examples/reviewed_exports, with their source names recorded in MANIFEST.json.

Braking CSV: demanded_decel_m_s2 is the instantaneous commanded deceleration, which varies during a ramp. The JSON scenario.demanded_decel_m_s2 is the configured target. Use the CSV and JSON together to retain both. No existing column has been renamed.

Original simulation RMS is sample-based; ride-study RMS is trapezoidal time-weighted. At 500 kg bump these are 0.555692 and 0.555970 m/s² respectively. Both round to 0.556. Neither is an ISO comfort rating.
