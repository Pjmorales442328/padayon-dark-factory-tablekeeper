# Core Stage 1 initial checks and required follow-ups

Repository: C:/Users/Prince/Documents/darkfactory/band-work/result
Requirement text: handoffs/requirements-stage-1.md
Independent check revision: 3c3fea3 (tester)
Core implementation is committed with this findings record; no acceptance claimed.

Observed commands:
- docker build -t tablekeeper-core-stage1 stage-1: pass (early build).
- Harness interpreter -m harness run --track tablekeeper --build C:/Users/Prince/Documents/darkfactory/band-work/result/stage-1 --stage 1 --mode isolated --out C:/Users/Prince/Documents/darkfactory/core-harness-1: Stage 1 119 passed, 1 failed, 0 skipped/deselected; harness still checking extra stages at this checkpoint.
- Harness interpreter -m unittest discover -s verification -v, SERVICE_CMD set to unquoted absolute interpreter plus -m tablekeeper.server: 186 tests, 8 failures, 2 errors, 0 skipped. Full log outside repository at C:/Users/Prince/Documents/darkfactory/core-independent-2.log.

Core fixes applied in this commit:
1. Unknown routes now return 404 before authentication. Anonymous access to existing references remains 404; anonymous unknown references use general 401 authentication rule (supplied harness failed expecting 401 for nonexistent ABC123).
2. Reset 302 users exceeded 10 seconds with serial PBKDF2 hashing. Password storage now uses independently salted scrypt (N=8192,r=8,p=1,32-byte output), with strict loading validation of algorithm/parameters/salt/hash. Passwords remain hash-only. Full rerun required.
3. Signup now explicitly guards generated user-ID collisions.

Tester-owned findings (requirements must remain authoritative):
1. test_L030 sends an Arabic digit unescaped in the HTTP URL; http.client raises UnicodeEncodeError before any service request. Encode the query value.
2. test_L058 expects 10 Friday slots from 18:00 through 22:00 in 30-minute steps: there are 9 inclusive slots.
3. test_L044 Bob first succeeds using key same with table t_2, then changes body to t_1 using his already completed key same. Requirement 47 requires idempotency_key_reuse before occupancy; test expects table_unavailable.
4. test_L083_L084 books t_2 at first-fold 01:30 for 90 absolute minutes, then tries first-fold 02:30 on the same table. These intervals overlap; the second booking must fail or use a free table.
5. test_L094_L111 moves the original booking to 21:00, then expects its old 19:00 slot to remain occupied. It must check the current booking slot.
6. test_L112 reports all 64 tracked kickoff files modified against manifest hashes. Core never wrote kickoff. Likely Windows newline bytes differ; verify original checkout and report observed normalized comparison without modifying kickoff.
7. test_L114 needs HARNESS_OUT set to completed harness evidence. This is invocation configuration, not service failure.
8. Default test launcher quotes the executable while shlex.split(posix=False) retains quotes, causing Windows FileNotFoundError. SERVICE_CMD override avoids this; tester should fix default launcher.

Interface-owned finding:
1. Fifty mixed in-flight requests yielded ConnectionResetError 10054 under Python 3.12. Increase ThreadingHTTPServer.request_queue_size to support 50 pending connections; inspect transport logs. No domain 5xx observed. Full rerun required.

All independent failures are listed above; no supplied checks edited or skipped.
