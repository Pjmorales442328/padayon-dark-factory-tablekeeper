# Reviewer notes: Stage 4 (contract revision f609d522c75cceea0b91cecbe568b14b162074f3)

Sources on disk (read these, not memory):
- handoffs/dispatch-stage-4-initial.md, handoffs/ledger-stage-4.md (ledger lines 1-351), handoffs/requirements-stage-4.md, handoffs/ownership-stage-4.md
- handoffs/requirements-stage-1.md, requirements-stage-2.md, requirements-stage-3.md
Frozen: stage-1 344e085, stage-2 94e7654, stage-3 8093f21 (source). Reviewer owns handoffs/reviewer-*-stage-4*.md only.
Rule: no Stage 4 acceptance from a baseline. Full candidate review starts only on a coordinator handoff naming an exact revision.

## Standing tasks
- [x] 1. Confirm serving Stage 4 to the coordinator (message d5e8d3a5).
- [x] 2. Receive dispatch parts 1-8 and confirm the committed file exists at f609d52 (all 8 parts settled).
- [x] 3. (ACCEPTED as baseline, a398254) Baseline review of core-builder restructure when the coordinator hands it over (behaviour-preserving, no features, metrics vs frozen Stage 3, frozen folders unchanged).
- [x] 4. (ACCEPTED as baseline, a398254) Baseline review of interface-builder restructure/no-op justification, same method.
- [ ] 5. Review the tester's check design against ledger lines 1-351 when handed over (name any ledger line with no passing check).
- [ ] 6. Full candidate review at the exact revision named by the coordinator: the eight checks below.

## Eight checks for a candidate
- [ ] 7. Clean build from `git archive <rev> stage-4`, `--network none --cpus=2 --memory=2g`, healthy within 60 s.
- [ ] 8. Exact supplied harness: `python -m harness run --track tablekeeper --repo C:/Users/Prince/Documents/darkfactory/band-work/result --stage 4 --mode isolated --out C:/Users/Prince/Documents/darkfactory/band-work/checks/<fresh>`; claim must read "claimed stage: 4"; stages 1-3 pass, zero skips; stage 5 (if any) fails as expected.
- [ ] 9. Tester independent checks all run; ledger line coverage named.
- [ ] 10. Version transfer: actual frozen Stage 3 container stopped and port closed before Stage 4 import; also Stage 1 and 2 exports; same-tab upgrade; old receipts replay exactly.
- [ ] 11. Maintainability vs frozen Stage 3 (radon mean 3.15, max 9, files MI A min 31.46, largest 171 lines; lizard; JS avg CCN 2.7).
- [ ] 12. Reading: input-order, timing, check-specific logic.
- [ ] 13. Screens: axe at 375 px and 1280 px, no horizontal scroll, applied plan reflected in availability/confirmation/lookup.
- [ ] 14. Frozen stage-1, stage-2, stage-3 byte-identical (`git diff --stat` against the frozen revisions).

## Stage 4 specific audit items (ledger 293-351 and requirements-stage-4.md)
- [ ] 15. Replan preview: auth 401/403/404, key rules, interval validation (offsets, from<to), unknown table 404, limits 6 tables / 4 pairs / 6 bookings with 422 planning_limit, 409 no_feasible_plan consumes no key, preview changes nothing (occupancy, history, revisions, restaurant revision).
- [ ] 16. Optimality oracle (independent brute force): minimize changed table-set count, then total unused seats, then rank vector in reference order; ranks singles in fixture order then pairs in declared order; own accepted-terms capacities; cutoffs ignored; fixed bookings, earlier closures and the proposed closure avoided.
- [ ] 17. Apply: manager/key/body {}; 404 unknown/other restaurant; 409 stale_plan after any restaurant revision change, none for another restaurant's write; 409 plan_already_applied with a different key; same-key replay 200 exact; atomic; moved booking +1 revision with one `reassigned` history entry (table_ids before/after, plan_id); unmoved untouched; restaurant revision +1 once, including a zero-move plan; closure excludes singles and pairs in availability, create/amend 409, explain no_overlap false independent of capacity; half-open adjacency; races (one winner).
- [ ] 18. Restaurant revision: starts 0; +1 once for new booking, real PATCH, first cancel, policy publication, series adoption, real batch, plan apply, real series amend; no change for no-op, failure, preview, replay, read; legacy import default well defined.
- [ ] 19. Series amend: auth/owner/key; validation (expected_revision, from_index 0..count-1, local_time HH:MM); stale_revision first; eligible = index >= from_index, not cancelled, not exception; original scheduled date + new clock; no-op retains terms; cutoff then policy; DST gap/fold; error precedence in index order over occupancy; failure atomic; success 201 current series; series +1 and restaurant +1 once; no exception flags changed; replay 200; concurrent same expected_revision one winner; moved occurrence keeps original scheduled date.
- [ ] 20. Repair preserves series exception flags, scheduled dates, identities, terms; affected series +1 once per application.
- [ ] 21. Reset clears closures, plans, applied flags, receipts, restaurant revision; export/import preserves them natively; bad import states 422 with no change, never 5xx; Stage 1-3 exports import with sensible defaults.
- [ ] 22. 50 mixed concurrent reads/writes/reset/export/import/preview/apply/series-amend: no 5xx.
- [ ] 23. Restaurant-revision correctness is mandatory from Stage 4 (organiser binding).

## Known carried advisories
Chunked bodies 400; reset and availability cost scale with state size; duplicate-block metrics unavailable; kickoff manifest mismatch (harness/cli.py, docs/participant-guide.md) predates the run; untracked __pycache__ must never be staged; F10 mean-CC growth (service.route/private, loading.booking_record to simplify).

## R1 audit progress (exact 9911384; findings in reviewer-findings-stage-4-r1-9911384.md)
- [x] 7 clean build PASS; [x] 8 harness PASS (claimed stage 4); [x] 10 transfer PASS (stage-3 source stopped); [x] 11 maintainability FAIL (M1); [x] 12 reading; [x] 13 screens 76/76; [x] 14 frozen folders unchanged.
- [x] 15-21 API probes (297 pass) and optimiser oracle (~1050 random cases, 0 mismatches); [x] 21 157 bad-import mutations, no 5xx.
- [ ] 9 / 5 tester ea57303 coverage review; [ ] 22 50-way mixed load; [ ] final acceptance (blocked by M1 and the above).
