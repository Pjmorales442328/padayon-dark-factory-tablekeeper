# Tester findings, stage 2, integrated candidate 94e7654 (stage-2 tree identical at HEAD)

Tested: stage-2 tree of 94e7654c4427fa3c087279675edbe1cda4f5a4fc (git diff 94e7654..HEAD for stage-1 and stage-2 empty). Checks revision 52dbf4c30006155a20a1bd54d653079bb5da5f89 (author tester), run with the supplied harness interpreter; Chromium 1228 launched by path (Playwright 1.63 expects an uninstalled revision); nothing installed.

## Supplied harness (exact command, kickoff cwd): band-work/checks/harness-s2-94e7654 and harness-s2-94e7654.console.txt
stage 1 pass, stage 2 pass, stage 3 fail (expected extra failure, recorded separately), `highest contiguous stage: 2`, `claimed stage: 2 on the shipped checks`. Nothing skipped or deselected.

## Independent suite: band-work/checks/tester-s2-94e7654-r3 (log stage2-checks.log, 40 screenshots in screenshots/)
326 tests (all 197 ledger lines, coverage_map2.py), 4 failed, 0 errors, 0 skipped. The suite is NOT clean:
1. test_L112_kickoff_matches_manifest FAILS: pre-run environment evidence (docs/participant-guide.md and harness/cli.py differ from kickoff-manifest.json; mtime 2026-10-03, before the first repo commit). test_L112_kickoff_untouched_since_run_started passes. No seat caused it.
2. test_L197_final_report_record_exists FAILS: coordinator-pending (stage-record has no stage 2 report / claimed-stage-2 line yet). Not a service defect.
3-4. Two inherited stage-1 strict-shape assertions are visibly SUPERSEDED by stage-2 requirements: Availability.test_L057_L058_L059_shape_and_grid (slots gain available_options) and Create.test_L062_shape (responses carry table_ids). Replacements test_s2_api Options.test_L058_L161_L162_* and Create.test_L062_L166_shapes pass.
No service defects found at this revision.

## Check corrections made during this run (all defects in my checks, committed before the final run)
- stale-session login wait (ui_login now clears the session first), port-closure wait in the browser upgrade check, capacity expectation (t_1 is too small for a party of 5), a failed-search check that accepted only keyword text (now: server message or alert region visible), and the same-reservation PATCH/move race (party size now valid in every serial order).

## What passed (selection)
- API: options order/capacity/omission, pair rules, nontransitivity, table_id/table_ids validation, summed capacity, any-member 409, PATCH/no-op reorder, cancel, seeds with cancelled status, reset validation of combinable, batch moves with pairs, receipts, races (shared members exactly one winner, disjoint both), serializable mixed load.
- Transfer: actual frozen stage-1 process filled, exported, KILLED with port closure confirmed, then independent stage-2 destination imported: tokens, logins, references, original create and batch receipt JSON exact (no regenerated table_ids), failed keys reusable, singletons gain table_ids; stage-2 round trip; import-validation fuzz atomic.
- Browser (Chromium): late search A after B for singles, other restaurant labels and pairs; 409 refresh with form/inputs preserved (single and one-member pair conflict); lost response before and after commit, same key and body retry, original reference recovered, changed field gets a new key, rejection after loss uses booking-error; combined bookings end to end incl. lookup/cancel; signed-out click; logout; no polling.
- Upgrade in one never-reloaded tab behind a same-origin switch: stage-1 API -> real export -> stage-1 killed -> stage-2 import -> still signed in, form and pending key/body survive, retry returns the original confirmation, retained reference works in lookup, no duplicate booking.
- Visual at 375 px and 1280 px for every route and state: no horizontal scroll, visible labels, keyboard focus, axe serious/critical none, loading/empty/error states, distinct available/unavailable/selected/uncertain/refused/success looks; screenshots inspected (warm cream/forest-green palette, serif headings, labelled combined seating "Together: Window + Booth").
## Measurements (host)
- start to healthy 0.51 s (docker 0.5 s); RSS 5 MiB; 150 mixed requests max 0.50 s, no 5xx; 50 concurrent logins 1.7 s; reset 150 users 4.8 s, 302 users 10.25 s on this host (reviewer measured 5.6 s in container).
- radon: stage-1 mean CC 2.64 max 9 min MI 31.3 (all A); stage-2 mean CC 2.81 max 9 min MI 31.5 (all A). lizard/duplication: not rerun for stage 2; duplicate-block metrics unavailable.
