# Stage record

Stage 1 start: 2026-10-04T06:35:00+08:00 (dispatch processing began).
Stage 1 end: 2026-10-04T07:13:39+08:00. Elapsed 38m39s.
Seats confirmed serving: core-builder, interface-builder, tester, reviewer.
R1: opened 2026-10-04T06:55:12+08:00; closed 2026-10-04T06:58:47+08:00; elapsed 3m35s. Evidence core-builder-findings-stage-1-run-1.md at 0130c11b286f8b71671e0cdf44e00bd215c365e4. Fix ad2f1a2cb3ee213645167a8d384fd393d4d95e3c raises transport request_queue_size to 128. Interface observed 150 concurrent-check requests, maximum 0.53 seconds, no 5xx; Docker build and health with 2 CPUs/2 GiB passed. Full independent rerun and reviewer remain pending.
R2: opened 2026-10-04T06:55:12+08:00; closed 2026-10-04T07:06:00+08:00; elapsed 10m48s. Tester fixed URL encoding, inclusive slot count, receipt precedence check, fold overlap setup, current-slot assertion and Windows launcher at be7e57cc32a72b6fbb52eff41dd17a917579516e. Evidence 2d3f448b441ac5735b7a1eadf6fcb4522cc60a3b: 187 tests, 1 remaining manifest failure, zero errors/skips, 116/116 ledger coverage; supplied harness claims stage 1. Remaining manifest failure is environmental, retained without skipping/weakening: harness/cli.py and docs/participant-guide.md differ from manifest with timestamps predating run. Reviewer independently confirms pre-run harness path change. Container reset 302 users 5.6s; Windows host 10.1-11.3s recorded separately.
R3: opened 2026-10-04T07:06:00+08:00; closed 2026-10-04T07:13:39+08:00; elapsed 7m39s. Reviewer D1 evidence at 59166376aaaeaad5b96a53f7d9a2a21e9dda9993 in reviewer-findings-stage-1-ad2f1a2.md: fixture passwords incorrectly subject to signup minimum. Core fix 06ad44bfd1cd38747701d97792dff10699eecea6 accepts seeded string passwords while signup retains minimum eight. Tester regression 344e085d8e3d0629dcc17fc95f22a43efe2a85d2 fails on rejected code and passes on fix. Reviewer independently confirms container reset/login/export/import and signup behavior.
Stage freeze: exact accepted revision 344e085d8e3d0629dcc17fc95f22a43efe2a85d2; decision revision 996cc7a839cbf9e8627f7f9dacfd3c60258183fd. Current stage-1 committed tree is identical. No further stage-1 edits. Untracked generated pyc files removed individually after confirming absolute parent and no tracked cache files; recursive cleanup was rejected by automatic policy review.

## Final outcome

Core-builder: Python domain, auth/password hashing, validated fixtures/state, DST, scoped occupancy, retries, cancellation/amendment, atomic moves, export/import; initial route/auth, hashing latency, ID collision fixes and reviewer D1 fix.
Interface-builder: HTTP transport, Dockerfile/RUN.md/runtime assets and dependencies; backlog correction; clean image build and no-network/resource evidence.
Tester: independent checks for all 116 ledger lines, own check corrections, sensitive D1 regression, isolated harness and maintainability measurements.
Reviewer: exact revision audits, D1 rejection, constrained container/race/concurrency/DST/state probes, final acceptance.
Coordinator: complete contract/ledger/ownership, committed full handoffs, routed findings, timing, freeze and final report.

Harness: C:/Users/Prince/Documents/darkfactory/band-work/checks/harness-r3/report.json at exact revision 344e085. Stage 1 120/120 pass, zero skipped/deselected; harness-r3.console.txt prints claimed stage: 1; expected extra stage 2 failure.
Independent run: 189 tests, 188 pass, one retained pre-run kickoff-manifest failure, zero errors/skips. Evidence tester-findings-stage-1-run-3.md at 062664099dd65017c67736d50a13515fb46cc9d5.
Maintainability: radon average CC A 2.64 over 105 blocks, maximum B(7), all files MI A (minimum 31.28). Lizard 747 NLOC, 101 functions, average CCN 2.6, zero warnings. Largest file 167 lines; duplicate-block tooling unavailable.
Runtime measurements: health 0.51s; RSS 29MiB host; 50-way no 5xx, maximum 0.52s host/1.8s reviewer container; 302-user reset 6.1s container/9.55s final host. Clean image runs within 2 CPUs/2GiB with no network.
Open limitations: kickoff harness/cli.py and docs/participant-guide.md differ from manifest before run, retained failing integrity check; chunked request bodies return 400; large seeded state increases reset/availability latency. No later stage or UI.
