# Stage record

Stage 1 start: 2026-10-04T06:35:00+08:00 (dispatch processing began).
Stage 1 end: pending.
Seats confirmed serving: core-builder, interface-builder, tester, reviewer.
R1: opened 2026-10-04T06:55:12+08:00; closed 2026-10-04T06:58:47+08:00; elapsed 3m35s. Evidence core-builder-findings-stage-1-run-1.md at 0130c11b286f8b71671e0cdf44e00bd215c365e4. Fix ad2f1a2cb3ee213645167a8d384fd393d4d95e3c raises transport request_queue_size to 128. Interface observed 150 concurrent-check requests, maximum 0.53 seconds, no 5xx; Docker build and health with 2 CPUs/2 GiB passed. Full independent rerun and reviewer remain pending.
R2: opened 2026-10-04T06:55:12+08:00; closed 2026-10-04T07:06:00+08:00; elapsed 10m48s. Tester fixed URL encoding, inclusive slot count, receipt precedence check, fold overlap setup, current-slot assertion and Windows launcher at be7e57cc32a72b6fbb52eff41dd17a917579516e. Evidence 2d3f448b441ac5735b7a1eadf6fcb4522cc60a3b: 187 tests, 1 remaining manifest failure, zero errors/skips, 116/116 ledger coverage; supplied harness claims stage 1. Remaining manifest failure is environmental, retained without skipping/weakening: harness/cli.py and docs/participant-guide.md differ from manifest with timestamps predating run. Reviewer independently confirms pre-run harness path change. Container reset 302 users 5.6s; Windows host 10.1-11.3s recorded separately.
R3 opened 2026-10-04T07:06:00+08:00, owner core-builder. Reviewer D1 at 59166376aaaeaad5b96a53f7d9a2a21e9dda9993 in reviewer-findings-stage-1-ad2f1a2.md rejects candidate ad2f1a2: fixture passwords shorter than eight rejected although signup minimum does not apply to fixtures. Closure pending.
Stage freeze: pending reviewer acceptance of exact revision and harness claim.
