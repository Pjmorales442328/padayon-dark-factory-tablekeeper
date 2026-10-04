# Tester final evidence, stage 2, exact target 94e7654 (focused rerun after handoff 682be17)

Target: 94e7654c4427fa3c087279675edbe1cda4f5a4fc (stage-1 and stage-2 trees identical at HEAD). Checks at 52dbf4c30006155a20a1bd54d653079bb5da5f89 (full hash from git; author tester). Historical full run kept: 326 tests, 4 failures, 0 errors, 0 skipped (band-work/checks/tester-s2-94e7654-r3). That run is NOT clean and stays recorded as is.

## The four failures of that run, classified
1. test_L112_kickoff_matches_manifest: pre-existing environment mismatch (docs/participant-guide.md, harness/cli.py; mtime 2026-10-03, before any seat commit). Unchanged, still failing, not hidden.
2. test_L197_final_report_record_exists: coordinator-pending at that time.
3-4. Availability.test_L057_L058_L059_shape_and_grid and Create.test_L062_shape: inherited stage-1 strict key-set assertions REPLACED by stage-2 requirements (available_options, table_ids); stage-2 replacements pass.

## Focused rerun after coordinator record 682be17 (harness interpreter, nothing installed)
- test_L197_final_report_record_exists: PASS (stage record now has the stage-2 report with the claimed stage 2 line). Log band-work/checks/tester-s2-l197.
- test_L114_L195_harness_claimed_stage_2 with HARNESS_OUT=harness-s2-94e7654.console.txt: PASS.
- After this rerun the suite state is: 326 tests, only kickoff-manifest failure (environment) plus the 2 superseded assertions; still not "clean".

## Maintainability, supplied lizard 1.24.0 (venv python) vs frozen stage-1 baseline (tablekeeper/*.py)
- stage-1: 747 NLOC, 101 functions, avg NLOC 6.7, avg CCN 2.6, max CCN 9 (_read_json_body), max function NLOC 25, 0 warnings.
- stage-2: 893 NLOC, 116 functions, avg NLOC 6.9, avg CCN 2.8, max CCN 9 (_read_json_body), max function NLOC 25, 0 warnings. Largest file server.py 171 lines.
- stage-2 JavaScript (static/*.js): 359 NLOC, 46 functions, avg CCN 2.7, max CCN 14, max function NLOC 39, 0 warnings.
- radon (unchanged): stage-1 mean CC 2.64 / max 9 / min MI 31.3; stage-2 mean CC 2.81 / max 9 / min MI 31.5; all files rank A.
- Duplicate-block metrics: unavailable (neither tool reports clones here).

## Timing of the five check defects corrected inside the integrated run (all +08:00, 2026-10-04)
Source: log file creation/modification times and git commit times. unittest logs carry no per-test timestamps, so the failing moment inside a run is bounded by the run interval; I do not claim finer times.
- Run A (band-work/checks/tester-s2-94e7654): started 08:19:31, finished 08:24:42; 9 failures: kickoff, L197-pending, and my four defects below (first observed in this run, individual moment not recoverable).
  1. stale-session login (test_L124 combined lost responses, 401 from the stale token) 
  2. capacity expectation (test_L121_L124 pair conflict: t_1 is too small for a party of 5)
  3. failed-search assertion (visual L133, keyword-only regex; the UI did show the server message)
  4. upgrade source-stopped check without port-closure wait
  Isolated reproduction/diagnosis reruns: log of band-work/checks/tester-dbg created 08:25:08. Corrections committed c76b77b at 08:26:25. Interval from run end to commit: 1 min 43 s; run start to commit: 6 min 54 s.
- Run B (tester-s2-94e7654-r2): started 08:26:26, finished 08:30:50; 5 failures, one new: 
  5. same-reservation race (test_L180_self_amendments: PATCH 422 because a valid serial order carried party size 8 to a 6-seat table). First observed in this run (bounded 08:26:26-08:30:50). Six isolated reruns passed (dbg log last modified 08:31:04); correction committed 52dbf4c at 08:31:09. Interval run end to commit: 19 s; run start to commit: 4 min 43 s.
- Run C (tester-s2-94e7654-r3): started 08:31:10, finished 08:36:11; failures only kickoff and L197 (+2 superseded). Findings commit 8be25eb at 08:36:33.
- Earlier R1 corrections (T1-T7): committed d4ffa21 at 07:52:32 (checks first committed 65d52fc at 07:38:12); the core evidence message time is not stored in the repo, so that interval is bounded only by those commit times.
Limitation: no seat logged the exact moment each individual failure was read; the figures above are bounding timestamps, not measurements of reading/fixing effort.
