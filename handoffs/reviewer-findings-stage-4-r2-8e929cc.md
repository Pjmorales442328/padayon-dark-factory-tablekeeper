# Reviewer decision: Stage 4 R2, exact core revision 8e929cc6112064969df170d443ecf2cdcd90c7f0

Path: C:/Users/Prince/Documents/darkfactory/band-work/result/handoffs/reviewer-findings-stage-4-r2-8e929cc.md
Repository HEAD when audited: b01852eb7921e85a4d5e8a0f6255ea1edd01b7e8 (stage-4 identical to 8e929cc; stage-1/2/3 identical to 344e085/94e7654/8093f21; tracked tree clean).
Decision: ACCEPTED, revision 8e929cc6112064969df170d443ecf2cdcd90c7f0 (interface baseline unchanged, bedf742, no interface file touched). M1 from 0638b7d is closed.

## M1 re-measurement (same tools, 8e929cc vs frozen Stage 3 8093f21, observed by me)
- radon mean CC 3.146 -> 3.116; minimum MI 31.46 -> 31.46 (equal); max CC 9, no function rank C or worse.
- lizard mean CCN 3.155 -> 3.1; max function NLOC 25 -> 25; 0 warnings; largest file 171 lines; duplicate blocks 0.00% in both (lizard -Eduplicate).
- Reading of 9911384..8e929cc: real extraction (state_revisions, state_revision_targets, shared conflict/table-set rules in planning); no input-order, timing or check-specific logic found.

## Eight checks
1. Clean build, fresh `git archive`, `--network none --cpus=2 --memory=2g`: healthy in about 3 s. PASS.
2. Exact supplied harness to checks/reviewer-s4-8e929cc: stages 1-4 pass 120/25/7/6, "claimed stage: 4". No stage 5 exists in the harness, so "next stage must not all pass" is not testable. PASS.
3. Independent: my 297 API probes (4 failures are my script's own expectations, identical to R1: A14, D23, D26, F6; rechecked, F6/A14 pass in p3); brute-force optimiser oracle 3 seeds x 200 iterations, 0 mismatches (1,051 previews, 779 feasible, 272 infeasible); 157 corrupted imports: no 5xx, no state change; 9 history mutations all 422. Tester evidence: coverage_map4 reports 351/351 lines covered (759 checks); harness 120/25/7/6; api 97/0; browser 6/6; inherited superseded assertions listed visibly with passing replacements. PASS.
4. Version transfer: Stage 3 (built from 8093f21) stopped and port closed, then export imported into Stage 4: 204; create/batch/series receipts replay 200 exact; history identical; legacy restaurant revision 0; preview works. Same-tab browser upgrade with the Stage 3 container removed: 17/17. PASS.
5. Maintainability: PASS (above).
6. Reading: PASS (above).
7. Screens: 76 browser checks at 375 px and 1280 px with axe, no horizontal scroll, late search, pair, lost-response, 409 flows: 0 failed. PASS.
8. Earlier folders: git diff against 344e085, 94e7654, 8093f21 is empty. PASS.
Also: 50 workers mixed load (book, amend, cancel, preview+apply, series, moves, export, import, reset): 482 requests, 0 5xx, max latency 0.60 s, health 200 after. Same without reset/import: 449 requests, 0 5xx, 17 confirmed bookings, 0 table overlaps.

## Non-blocking items (not service defects)
T1 [tester, check defect]: inherited3 reports `errors 1` (test_L281_L272_history_sequence_and_events_are_validated: KeyError 'revision') that the tester report does not list. Cause: the frozen Stage 3 check picks the longest list of dicts with "seq" in the opaque state; Stage 4 adds `restaurant_events` (also seq lists), so it can pick the wrong list. The service is correct: I ran the same eight history mutations plus an empty accepted_terms against the real `histories` list: all 422, original re-import 204. Tester should record this error as superseded or fix the selector; it does not change my decision.
E1 [environment]: test_L112_kickoff_matches_manifest (docs/participant-guide.md, harness/cli.py modified before the run) is an environment mismatch, as the tester stated.
Superseded frozen assertions (3 + 2 + 3 + RUN.md stage-3 regex) are legitimate: Stage 3/4 adds revision/terms fields; replacements pass.

Failed output kept in C:/Users/Prince/AppData/Local/Temp/rv5, rv6 and /tmp/rv6.
