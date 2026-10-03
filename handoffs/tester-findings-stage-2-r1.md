# Tester findings, stage 2, R1 (core checkpoint 1199758)

Core evidence read: handoffs/core-builder-findings-stage-2-run-1.md (T1-T7, I1-I4). Checks corrected at the commit that adds this file; earlier checks 65d52fc.

## T1-T7 classification (each re-derived from the requirements)
- T1 CHECK DEFECT. Pair [t_1,t_2] at 19:00 occupies t_2 for [19:00,20:30); a pair [t_2,t_3] at 18:00 occupies [18:00,19:30): they overlap on t_2. Setup reordered (18:00 pair on t_2/t_3 first, then 19:30 and 21:00 bookings); the capacity assertions are unchanged.
- T2 CHECK DEFECT (serializability, ledger 180/181). A PATCH and a move of the SAME reservation can both succeed in a serial order (each replaces its own occupancy). Exactly-one-winner is now asserted for three DIFFERENT bookings needing t_3 at 19:00, plus a new check that the same-reservation race ends in a consistent state (one booking holds the slot).
- T3 CHECK DEFECT. 20:30 pair on t_1/t_2 overlaps the 21:00 booking on t_2. Post-export mutation now uses a free Friday slot.
- T4 CHECK RELIABILITY DEFECT. The port was probed once, right after kill. Now polled up to 15 s (wait_port_closed) and the process exit is required, before the destination starts or imports. The stopped-source proof stays real (actual frozen stage-1 process killed; no mock).
- T5 CHECK DEFECT. Token now chosen from the list of the owner who holds each booking (BOBSEED1 belongs to Bob).
- T6 CHECK DEFECT. Each observation starts with a re-import of the unchanged export, so the baseline is the imported source state.
- T7 CHECK DEFECT. Fuzz keeps a fixed source snapshot and path list; only the destination is restored after an accepted mutation.
- I1 pending (interface). I2 kickoff mismatch kept visible (test_L112_kickoff_matches_manifest fails: docs/participant-guide.md, harness/cli.py; both predate the run). I3 HARNESS_OUT/final-record checks wait for the integrated run. I4 metrics: the L196 check now looks for an interpreter that can import radon (METRICS_PYTHON, harness python, PATH, C:/Python314) instead of bare `python`; nothing installed.

## Run on exact core 1199758 (git archive copy of stage-2, S2_DIR), harness interpreter
- Inherited stage-1 suite against stage 2 (band-work/checks/tester-s2-core1-inh*): 178 tests, 0 unexpected failures, 0 errors, 0 skipped; 2 frozen strict-shape assertions superseded and listed (availability slot key set; reservation response key set), each replaced by a stage-2 check that passes.
- Stage-2 API/transfer/process group (band-work/checks/tester-s2-core1*): 89 tests, 7 failures, 0 errors, 0 skipped. All combined-table API, PATCH, move, seed, reset-validation, race, serializability, transfer (actual stage-1 process stopped, then imported), round-trip and import-validation checks pass. Remaining failures are not core defects: docker/HTML routes and assets (UI not built: GET / 404, no static assets), harness-claim and final-record (no evidence yet), kickoff manifest (environment), maintainability (interpreter lookup, fixed afterwards).
- Measurements (host): start 0.51 s, RSS 5 MiB, 150 mixed requests max 0.52 s, 50 logins 1.7 s, reset 150 users 5.1 s, 302 users 9.9 s.
