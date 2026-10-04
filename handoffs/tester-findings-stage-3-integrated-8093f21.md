# Tester findings, stage 3, integrated candidate (stage-3 tree of 8093f21)

Tested: stage-3 tree identical at 8093f21 and at HEAD a41b705/97e4185 (git diff for stage-1 vs 344e085, stage-1/2 vs 94e7654 and stage-3 vs 8093f21 empty). Core 445dfb6 + interface 8093f21. Checks: a41b705a2c319a9435e0086d558ae8a20c1d520b (author tester). Supplied harness interpreter, nothing installed, Chromium launched by path.

## Supplied harness (exact command, kickoff cwd): band-work/checks/harness-s3-8093f21 (+ .console.txt)
stage 1 pass, stage 2 pass, stage 3 pass, stage 4 fail (expected extra failure), `highest contiguous stage: 3`, `claimed stage: 3 on the shipped checks`. No skips or deselections. (Same result at the 118bff2 tree: band-work/checks/harness-s3-118bff2.)

## Independent suite: band-work/checks/tester-s3-8093f21 (stage3-checks.log, 40 screenshots in screenshots/)
466 tests (all 292 ledger lines via coverage_map3.py; frozen stage-1 + stage-2 suites against stage 3 plus ~230 stage-3 tests), 6 failed, 0 errors, 0 skipped. NOT clean:
1. test_L112_kickoff_matches_manifest FAILS: pre-run environment evidence (docs/participant-guide.md, harness/cli.py differ from kickoff-manifest.json; mtimes 2026-10-03). The untouched-since-start check passes. Unchanged, not hidden.
2-6. FIVE inherited assertions fail by stage-3 requirements and are listed visibly as SUPERSEDED, each with a passing stage-3 replacement:
   - Availability.test_L057_L058_L059_shape_and_grid (frozen slot key set) -> test_s3_explain_policy Explain.test_L200
   - Create.test_L062_shape (frozen stage-1 reservation key set) and test_s2_api Create.test_L062_L166_shapes (frozen stage-2 key set) -> test_s3_booking_history Terms.test_L062_L230
   - Cancel.test_L075_cancel_frees (cancelled booking equal to the original except status; stage 3 raises revision 1->2) -> Amend.test_L075_L076_L234
   - test_s2_transfer TestUpgrade.test_L154_L184 (imported booking equals source plus table_ids; stage 3 adds revision 1 and policy-0 terms) -> UpgradeBase.test_L261_L282
No service defect remains at this revision; the final-report record check (L292) passes now that the record exists.

## Check defects found by core (F2-F6) and corrected by me (all mine; times are bounds)
- F3 batch series revision (I expected 3; one batch changing two occurrences is one increment: 2). F4 policy bounds (1440/10080) wrongly applied to original fixture fields; now only to policy/terms objects, with a separate stage-1-rules check for fixture fields. F5 adoption of an imported anchor collided with an imported pair booking (correct 409): free anchor used, collision kept as an atomic-rejection check. F6 builder notes with checkbox list syntax: matcher accepts it (still requires all 292 numbers).
  Corrected in 6916e6f at 16:58:40 +08:00. First observed in core's runs (evidence folders created 16:38:38, last modified 16:47:49) and routed in core's findings commit 118bff2 at 16:56:23; I read them after that, so the bound from routing to fix is about 2 min 17 s.
- F2 frozen cancel equality listed as superseded in run_stage3.py: a41b705 at 17:06:58. First seen in my own run tester-s3-118bff2 (16:59:43-17:06:18), core had reported it at 16:56:23: 10 min 35 s.
- F1 (interface, legacy policy route during upgrade) was fixed by 8093f21 at 17:06:27. My run on the 118bff2 tree showed the stage-1-backend upgrade timing out at the grid (16:59:43-17:06:18); after 8093f21 the same inherited check passes. Both upgrade checks pass (stage-1 backend and stage-2 backend, same tab, no reload, real source killed before import).
Limitation: unittest logs have no per-test timestamps; times are run-interval and commit bounds.

## What passed (selection)
- Explain (shape, order, independent rules, both-false, literal true), policies (permissions, 70+ invalid cases, versions, date selection, same-date tie, immutability, idempotency, 20-way concurrency), accepted terms and revisions, old-cutoff first, no-op, cancel, expected_revision precedence and one-winner race, history (seq, fixed field order, pair table_ids, replays), decision/private 404s for guest, anonymous, manager, series (shape, DST gap/fold/local clock, per-occurrence policy, atomic failure, key reuse, adoption race, exceptions, batch increments), 60-request 50-way mixed load serializable.
- Transfer: actual frozen stage-2 and stage-1 processes filled, exported, killed with port closure confirmed, then independent stage-3 import: tokens, logins, single/pair bookings, exact original create and batch receipt JSON, failed keys, adoption of imported anchor; stage-3 round trip with policy/series/batch receipts and counters continuing; import fuzz atomic.
- Browser: inherited stage-2 flows and 375px/1280px visuals (axe, labels, focus, distinct states) against stage 3; policy-driven grid and booking, late search across policy dates; same-tab stage-2 -> stage-3 upgrade (pending lost-response retry recovers the original confirmation, retained reference, sign-in).
## Measurements (host)
- start 0.51 s (docker 0.5 s); RSS 5 MiB; 150 mixed requests max 0.61 s no 5xx; 50 logins 1.71 s; 60 mixed new-path requests 0.11 s; reset 150 users 5.3 s, 302 users 10.2 s on this host.
- radon: stage-2 mean CC 2.81 -> stage-3 3.15, max 9 both, every file MI A (min 31.46 both). lizard Python: stage-2 116 functions/799 NLOC/avg CCN 2.81/max 9; stage-3 174 functions/1298 NLOC/avg CCN 3.16/max 9/max function NLOC 25, 0 warnings. lizard JS: stage-2 46 funcs/353 NLOC/avg 2.70/max 14; stage-3 51 funcs/379 NLOC/avg 2.67/max 14. Duplicate-block metrics unavailable.
