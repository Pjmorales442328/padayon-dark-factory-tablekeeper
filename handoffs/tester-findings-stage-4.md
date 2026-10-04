# Tester findings, Stage 4 — correction of owned check defects F1–F17

Source under test: 9911384e39df4e3a554f57dfc76b806a976739db (interface bedf7427 included). Builder findings: handoffs/core-builder-findings-stage-4-first.md (53acf09d).
Each finding was adjudicated against the Stage 4 contract, not accepted by default. The rerun results are appended in a later commit.

1. F1 ACCEPTED. Frozen Stage 3 RUN.md regex ("stage-3") and "claimed stage: 3" cannot hold for Stage 4. Both stay visible in SUPERSEDED (run_stage4.py, never skipped); replacements: test_s4_http.Packaging4 (RUN.md stage-4) and HarnessRun ("claimed stage: 4", exact harness command). Old L281 entry also listed (F3).
2. F2 NOT A CHECK DEFECT. Kickoff manifest mismatch (docs/participant-guide.md, harness/cli.py) is environment evidence; untouched and still reported as a failure.
3. F3 ACCEPTED. Frozen test picks the longest seq-bearing list, which can be restaurant_events. Owned adapter test_s4_import_adapter.ImportValidation4 selects reservation histories by shape (seq, event, changes, revision); frozen test marked SUPERSEDED.
4. F4 ACCEPTED. Base4.ta/tb are now fresh-login properties (reset invalidates tokens).
5. F5 ACCEPTED. Native transfer tests assigned read-only properties; now cached `_tk` attributes.
6. F6 ACCEPTED. Idempotency keys are scoped user/method/path: unknown plan URL with same key is 404; changed JSON on the same URL is 409 idempotency_key_reuse; other user is 403. Test rewritten.
7. F7 ACCEPTED by arithmetic. t_3 alone seats 6, so a pair loses to the single table; L303/L312 expectations rewritten from the contract objective (changed table sets, unused seats, rank vector).
8. F8 ACCEPTED. A 22:00 start with 90 minutes ends after 23:00 closing (outside_opening_hours); seeds and blockers moved.
9. F9 ACCEPTED. Optimum plans now come from the brute-force oracle instead of hand-picked tables.
10. F10 ACCEPTED for L324 only (policy-change expectation ["21:30","21:30","21:00","21:00"]); L322 end "22:30" was already right.
11. F11 ACCEPTED. Adoption is refused inside the cancellation cutoff; the test adopts outside it and waits for the clock to reach the boundary (adds about 2 minutes).
12. F12 ACCEPTED. 90-minute overlaps in seeds fixed (transfer pair, MixedConcurrency seeds, series amend blockers).
13. F13 ACCEPTED. Final series times are ["21:00","20:00","21:00"] (party-amended exception keeps its own time).
14. F14 ACCEPTED by contract. Stage 1/2 imports declare no manager_user_ids: replan 403 forbidden; history/decision 404 before migration, 200 for the owner after; legacy series adopted through POST /series.
15. F15 ACCEPTED. Fixture labels are t_1 Window, t_2 Booth, t_3 Terrace.
16. F16 ACCEPTED. Adoption is POST /series with {anchor_reference, count, interval_weeks}; the same-tab test also now uses a feasible closure (t_1 closed, 21:00 series occurrence can move) per interface-builder 5e60f875.
17. F17 ACCEPTED. Maintainability compares against FROZEN_STAGE3 (real Stage 3 path), plus owned stdlib approximation; real radon/lizard numbers are reported from the rerun and the builder's regressions (mean complexity 3.44 vs 3.155, min MI 30.65 vs 31.46, longer max function) are NOT softened.

Rerun on ea57303 (api part) exposed six further defects in my own checks, all corrected without weakening any service expectation:
18. R1 L303 no_feasible: a considered t_2 blocker appears in assignments as unchanged (`changed: false`); expectation now lists it and (moved, unused)=(0,2).
19. R1 L303 half-open: pair t_1+t_2 is feasible, so no 409; a t_1 booking is added so the pair is blocked.
20. R1 L298: oracle now receives already-applied closures.
21. R1 L342: batch-move exceptions are permanent, so flags are [F,T,T,F,T]; only occurrence 0 moves under amend.
22. R1 L339: native p2 plan was infeasible; closes t_1 FRI 00:00-23:59.
23. R1 L342: 70-day repair window triggered planning_limit; window is THU 18:00-23:00.
