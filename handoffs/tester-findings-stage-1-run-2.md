# Tester findings, stage 1, rejection R2 (checks corrected and rerun)

Tested repository revision: e9e2610 (stage-1 code last changed at ad2f1a2; core 0130c11 + interface fix ad2f1a2).
Checks revision: be7e57c (author tester). Logs outside repo: band-work/checks/{tester-run3,tester-run4.txt,harness-r2,harness-r2.console.txt,tools}.

## Core findings that were tester-owned: resolution (each verified against the spec)
1. L030 raw non-ASCII digit URL: check defect (client could not encode). Fixed: percent-encoded. Service now answers 422.
2. L058 Friday slots: check defect. 18:00..22:00 inclusive at 30 min = 9 (22:00+90 = 23:30). Fixed to 9.
3. L044 Bob reused his completed key with a changed body: check defect (spec 47 requires 409 idempotency_key_reuse). Reordered: other user, same key, same body first (409 table_unavailable, not a replay), then Bob's own use.
4. L083/L084 first-fold 01:30 and 02:30 on one table overlap by 30 absolute minutes: check defect. Reset between bookings.
5. L094 old slot vs current slot after moves: check defect. Now blocks the current slot (t_2 21:00).
6. L112 kickoff hashes: all 64 differ by CRLF only (normalised comparison now accepted). Two files still differ after normalising, both predate the run (mtime 2026-10-03): harness/cli.py (one-line Windows path fix, `.as_posix()`, shown in `git diff`) and docs/participant-guide.md. Not changed by any seat; test_L112_kickoff_matches_manifest keeps failing and is reported, not weakened. A new check, test_L112_kickoff_untouched_since_run_started, passes (no kickoff file newer than first repo commit).
7. L114: HARNESS_OUT now points at harness output; passes with evidence `claimed stage: 1 on the shipped checks`.
8. Default launcher quoting on Windows: check defect, fixed (argv list, no quoted exe).
9. Reset load test: the 302-user figure was my own stress size, the spec gives no fixture size. Asserted now at 150 users (<10 s); 302 recorded as measurement. Measured 10.1 to 10.9 s for 302 users (just over 10 s): reported to core as a risk, not a failure.

## Results at e9e2610 / be7e57c
- Independent suite: 187 tests, 1 failure (L112 manifest), 0 errors, 0 skipped. Ledger coverage 116/116 (coverage_map.py).
- Docker build + run with limits (and --network none) pass.
- Supplied harness, exact isolated command from kickoff cwd: stage 1 pass, stage 2 fail (expected), `claimed stage: 1`.
## Measurements
- start to healthy 0.51 s; RSS after 5x50 write bursts 30 MiB.
- 50-way mixed bursts: no 5xx, max latency 0.56 to 0.62 s; 50 concurrent logins 1.7 s.
- reset: 150 users 5.1 to 5.6 s; 302 users 10.1 to 10.9 s; 10 users 0.5 s.
- radon: average CC A (2.64) over 105 blocks, no block above B(7); MI A for every file (31.3 to 100; lowest loading.py 31.28, server.py 31.89).
- lizard: 747 NLOC, 101 functions, avg CCN 2.6, no threshold warnings, max file 128 NLOC.
