# Reviewer findings: Stage 4 R1 independent audit, exact revision 9911384e39df4e3a554f57dfc76b806a976739db

Absolute path: C:/Users/Prince/Documents/darkfactory/band-work/result/handoffs/reviewer-findings-stage-4-r1-9911384.md
Decision: NOT ACCEPTED, and no full acceptance is possible yet. Reasons: (1) maintainability figures are worse than frozen Stage 3 (owner core-builder, below); (2) the corrected complete tester proof for this revision is not yet reviewed by me (tester commit ea57303 exists; I have not audited its ledger coverage). I found NO behavioural defect in the service at 9911384.
Method: `git archive 9911384 stage-4` (C:/Users/Prince/AppData/Local/Temp/rv5/s), black-box scripts rv5/oracle.py, rv5/p2.py, rv5/xfer.py, rv/b1s4.py, rv/b4.py, the exact supplied harness, radon and lizard. Failed output kept in rv5/*.out.

## Findings
M1 [core-builder] MAINTAINABILITY REGRESSION (rule: any figure worse than the previous accepted stage). Measured on 9911384 vs frozen Stage 3 (8093f21):
- radon mean CC 3.146 -> 3.429 (233 blocks). Worse.
- radon minimum MI 31.46 -> 30.65 (tablekeeper/revisions.py, 115 lines); all files still MI A. Worse.
- lizard mean CCN 3.155 -> 3.4 (229 functions, 1997 NLOC); max function NLOC 25 -> 26 (state_receipts.validate_series). Worse.
- Unchanged or better: max CC 9 (no function above 10; `radon cc -n C` empty), largest file 171 lines (server.py), lizard 0 warnings, JS avg CCN 2.7 (390 NLOC, 52 functions, 0 warnings).
These are real regressions. The growth tracks new feature code and core itself reported them, but I do not soften them: the rule is "worse than previous accepted stage", and they are worse. Required: bring mean CC, minimum MI (revisions.py first) and max function length back to at most the Stage 3 figures, or the coordinator must record a decision that the budget does not apply to feature growth; I cannot waive it. Behaviour-preserving simplification only; re-run my probes after.
Duplicate-block metrics remain unavailable (no tool).

## Disputed tester findings F1-F17 and D1-D3, judged from the specification
Tester-owned check defects (not service defects), confirmed unless noted:
- F6 CONFIRMED check defect: requirements-stage-1.md:240 scopes a key to path ("same key ... on a different path is a different request"); a 404 on another plan URL is correct.
- F7 CONFIRMED check defect: accepted capacities are per booking terms; my independent brute-force oracle agrees with the service on ~1,050 random previews/applies (seeds 1-3, 200 iterations each, 0 mismatches, covering own-terms capacities, fixed bookings, prior closures, 409 infeasibility, applied tables).
- F8 CONFIRMED: 22:00 + 90 min > 23:00 close is `outside_opening_hours` (also observed: 21:30 + 90 = 23:00 exactly is accepted).
- F9 CONFIRMED check defect: all bookings overlapping the closure, from every series, are considered; the optimum is what the oracle computes.
- F10 CONFIRMED: 20:00 + 90 min ends 21:30 (observed in my probe D19).
- F11 CONFIRMED: adoption inside the accepted cutoff is `cutoff_passed` per Stage 3 requirements.
- F13 CONFIRMED: exception-marked occurrences keep their time; my probes D12/D15 show siblings move, flags unchanged.
- F14 plausible and consistent with my stopped-source transfer (Stage 1/2/3 exports carry no new Stage 4 state; legacy restaurant revision imports as 0; preview/apply works after import).
- F16 CONFIRMED: the binding route is POST /series with anchor_reference (requirements-stage-3.md:170); frozen Stage 3 returns 404 for the other route (I hit the same 404 with a stale image).
- F1, F2, F3, F4, F5, F12, F15, F17: tester/environment items (inherited assertions, kickoff manifest mismatch, harness setup, fixture labels, adapter label). I did not need them to judge the service; their correction is judged when I review the tester's committed ea57303 coverage. F2 is environment (pre-run manifest mismatch).
D1 ACCEPTED as a valid reading: requirements-stage-4.md:20 requires "explicit offsets"; a `Z` designator is an explicit zero offset. Observed: `to` ending in Z gave 201; missing offset, from>=to, bad date gave 422.
D2 ACCEPTED: 157 corrupted-import mutations (state keys, closure/plan fields, duplicate plan id, from==to, unknown table/restaurant): no 5xx, 0 changed state; the 6 that were accepted equal the original value (identical re-export). Immutable receipts replay exactly after import.
D3: see M1; D3 reduced max CC but the aggregate figures remain worse than Stage 3.

## Eight checks on 9911384
1. Clean build/run: PASS. Image built from the archive; `--network none --cpus=2 --memory=2g`: /health ok within 1 s, `/` and `/login` text/html, `/static/app.js` text/javascript.
2. Supplied harness: PASS. Exact command to checks/reviewer-s4-9911384 printed "claimed stage: 4 on the shipped checks", highest contiguous 4: stage 1 120, stage 2 25, stage 3 7, stage 4 6 passed (no skips). A stage 5 does not exist in the supplied harness; "next stage must not all pass" is not testable.
3. Independent checks: NOT COMPLETE. My own: 297 API probes pass (preview 401/403/404/key rules/validation/limits 6-4-6/no_feasible consumes no key/preview changes nothing; apply stale/already_applied/replay exact/history reassigned with plan_id/+1 revisions/zero-move apply +1; closure excludes in availability, create and amend 409, half-open adjacency; restaurant revision +1 once for every write path and 0 for no-op/failure/replay/other restaurant; 8-way apply races one winner; series amend validation, stale first, exception/cancelled skipped, original scheduled dates, DST across March, atomic conflict, replay, concurrent one winner; repair preserves flags; export/import roundtrip). Four probe failures in my own run were errors in my script (manager fixture overlap, expectation counts), re-checked and cleared, not service defects. Tester's ea57303 coverage is not yet reviewed by me.
4. Version transfer: PASS. Stage 3 (built from 8093f21) stopped and port closed, then imported into the constrained Stage 4 container: 204, create/batch/series receipts replay 200 exact, history identical, restaurant revision 0, availability and series readable, preview works. Browser same-tab upgrade (stopped Stage 3 backend, Chromium): 17/17.
5. Maintainability: FAIL, see M1.
6. Reading: no input-order, timing or check-specific logic found in replans, planning, browsing, policies; the planning limit check also trips on tables > 6 or pairs > 4 regardless of bookings, which the contract permits ("may"). Optimiser compared against an independent oracle.
7. Screens: PASS. 76 browser checks at 375 px and 1280 px (axe, no horizontal scroll, search/pair/lost-response/late-search flows); the applied-plan effect on availability/confirmation is covered by API probes.
8. Earlier folders: PASS. `git diff --stat` for stage-1 (344e085), stage-2 (94e7654), stage-3 (8093f21) against HEAD is empty.

## Not yet done
- Review of the tester's corrected checks (ea57303) against ledger 1-351 and naming of any uncovered line.
- 50-way mixed concurrent load including preview/apply/amend/reset/export/import (I ran 8-way races only in this pass).
Untracked __pycache__ must not be staged.
