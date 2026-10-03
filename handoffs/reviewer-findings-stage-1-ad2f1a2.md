# Reviewer findings: Stage 1 candidate ad2f1a2cb3ee213645167a8d384fd393d4d95e3c (interface-builder)

Decision: REJECT (one service defect, listed below). No acceptance. Handoff ac43904 is the dispatch; code between 0130c11 and ad2f1a2 differs only by server.py request_queue_size.
Method: clean `git archive ad2f1a2 stage-1` in %TEMP%\rv\c1; `docker build`; container run with `--network none --cpus=2 --memory=2g -e PORT=8099`; probes (rv/p2.py p3.py p4.py, outputs rv/p2.out p3.out) executed inside the container; harness and tester checks run from the same archive. Outputs kept in %TEMP%\rv (not deleted).

## Checks 1-8
1. Clean build: PASS. docker build ok, health 200 on first poll, network none, 802 MiB of 2 GiB after load.
2. Supplied checks: PASS for stage 1. `harness run --track tablekeeper --stage 1 --mode isolated` on the archive: 120 collected, 120 passed, 0 failed/skipped/deselected (rv/h2/stage-1.counts.json). report.json: stages {1: pass, 2: error, 3: error, 4: error}, highest_contiguous 1, so stage 2 does not pass. The text "claimed stage: 1" was not printed on stdout (rv/h2.log is empty); the claim is only in report.json highest_contiguous. Tester must supply the printed claim (ledger 114).
3. Independent checks: tester commit ac43904 run unmodified against this archive: 186 tests, 7 failures, 2 errors (rv/v.out). L030, L058, L044, L083_L084, L094_L111 are wrong checks (tester R2: the spec/core behaviour is correct; I confirmed each against the spec text). L112, L114, L115 fail only because my copy had no git/kickoff layout (environment). L009 errored on my Windows host (reset of 302 users exceeded its 10 s client timeout); in the container the same reset took 5.6 s. Every ledger line has a check by name; coverage for lines is the tester's to confirm after R2.
4. Version transfer: n/a for stage 1 (no previous stage). Export/import within stage 1 verified: export detached (1 vs 2 reservations after later write), reset then import restored token, login, replay of the original create key (identical body), reimport idempotent, overlapped state / ghost token / wrong track / format_version true / missing state give 422 with state kept, bad JSON 400.
5. Maintainability: `radon cc` 105 blocks, none rank C or worse (max below 11), average A 2.64; largest file server.py 167 lines (all files under 300). No duplicate-block tool is installed in the harness interpreter; none measured.
6. Reading: no order- or timing-dependent behaviour or check-specific cases found. Global RLock serialises everything; atomic receipts built on a copy.
7. Screens: n/a (no UI).
8. Earlier folders: n/a (no earlier stage).

## Defects
D1 [core-builder] Seeded users with short passwords are rejected. `POST /_test/reset` with a user password of "pw" returns 422 validation_failed "Invalid state: Password must have eight characters" (reproduced on 0130c11 and in the ad2f1a2 container, rv/p3.out last line). The 8-character rule in section 6 applies to signup only; section 4 says seeded users must be able to log in with the given password (ledger 21). Cause: accounts.user_record applies `password` rule to fixtures. Fix: validate password as a string only for fixtures, keep >=8 for signup.

## Advisories (not rejections)
A1 [interface-builder] chunked request bodies get 400 (carried over from the transport review).
A2 [core-builder] Reset cost is ~18 ms per user under the global lock: 302 users 5.6 s in the container (limit 10 s), 11.3 s on a Windows host. Larger user fixtures could exceed 10 s.
A3 [core-builder] Availability recomputes timestamps for every table/reservation under the global lock; with 1500 seeded reservations one request took 0.49 s and 50 concurrent took 17 s on the Windows host (old backlog build). With 300 reservations in the container, 50 mixed requests peaked at 1.4 s with no 5xx (3 rounds).
A4 [environment, not a seat defect] Kickoff harness/cli.py is modified (git diff: one-line Windows path fix via as_posix, file time 2026-10-03 08:19 +0800, before this run started). It breaks the ledger 112 "harness unmodified" wording, and the tester's L112 fails (64 files differ by CRLF). Coordinator must record this as a pre-existing environment change, not a builder edit.

## Verified fixed
R1: request_queue_size is now 128 (diff 0130c11..ad2f1a2, server.py +1). In the container, 50 simultaneous mixed requests x3 rounds gave no 5xx and max 1.4 s; 200 simultaneous mixed requests gave no 5xx (max 4.6 s).

## Other verified behaviour in the container
Race: 40 concurrent creates, same table/time, distinct keys: 1x201, 39x409. 40 concurrent identical key: 1x201, 39x200, one booking. Error precedence: 401 before 400 key; used key + invalid body = 409; key >255 = 422; numeric starts_at_local 400; Z/seconds/Feb 30 422; boolean/2.0 party 422; grid/outside/capacity/unknown-table codes right; adjacency 20:30 ok, 20:00 409; same table id in two restaurants ok; other guest and anonymous on an existing reference 404; no-op patch 200; repeat cancel 200; cancelled patch 409; past booking cancel/patch 409 cutoff_passed, past seed accepted. DST Berlin 03-29/10-25 and New York 03-08/11-01: gap hours absent and 422, fold appears once, second occurrence not bookable, ends_at 02:00 for the fold example, offsets right. Moves: swap 201, replay 200, conflicts 409, non-occupancy beats occupancy, duplicates/0/9 items 422, unknown reference 404, used key with invalid body 409. Fixture validation: overlap, duplicate table, bool capacity, 65-char id, duplicate email, negative cutoff, closes<=opens, missing user, lowercase reference all 422; same table id in another restaurant allowed.
