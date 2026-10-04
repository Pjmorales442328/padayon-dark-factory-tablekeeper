# Tester report, Stage 4 R2, core candidate 8e929cc6112064969df170d443ecf2cdcd90c7f0 (checks at fbe5efcd87db9ae2ef4c87a459c6d3b1f64d157c)
Outputs: C:/Users/Prince/Documents/darkfactory/band-work/checks/r2-8e929cc/
Run (cwd verification/stage4, harness python): run_stage4.py --part api|browser|inherited1|inherited2|inherited3 --out <folder>; harness: exact kickoff command (prints "claimed stage: 4").
Coverage: 351/351 ledger lines, coverage_map4.py.
Results: harness stages 1-4 = 120/25/7/6 passed, claimed stage 4. api 97/0 fail/0 err/0 skip. browser 6/0. inherited1 178 run, 3 superseded only. inherited2 135 run, 2 superseded only. inherited3 153 run, 1 real failure (test_s3_http.Process3.test_L112_kickoff_matches_manifest, environment manifest mismatch, F2, untouched) + 3 superseded.
Maintainability (core-s4-metrics.py, same tools, frozen Stage 3 vs stage-4): radon mean CC 3.146->3.116; min MI 31.458->31.458; lizard mean CCN 3.155->3.122; max function NLOC 25->25; max CC 9; max file 171; no function over 10.
Timing: start-to-healthy 0.51s; 50-way bursts max 0.79s n=150; 50 logins 2.09s; reset with 302 users 6.79s; L324 cutoff test ~2 min.
