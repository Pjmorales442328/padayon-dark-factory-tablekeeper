# Tester notes, stage 1

Inputs: handoffs/dispatch-tester-stage-1.md (rev 32628cd), handoffs/requirements-stage-1.md, handoffs/ledger-stage-1.md.
Own: verification/**, handoffs/tester-*.md.

## Task list
1. [x] Write verification/ black-box suite (stdlib unittest, HTTP only); each test name carries the ledger numbers it covers (L###).
2. [x] Coverage script verification/coverage_map.py proves every ledger line 1..116 has >=1 check.
3. [x] Edge areas: error ordering, boundaries, wrong types, races, replays, access by other/anonymous, DST, uneven totals.
4. [x] Stage-transfer: export from service A, import into independent service B (separate process/port) and re-check tokens, receipts, replays.
5. [x] Runner verification/run_checks.py (starts service itself or uses BASE_URL / BASE_URL2).
6. [ ] Commit, post revision + command to coordinator and reviewer.
7. [ ] Once builders ready: run suite, run supplied harness isolated (claimed stage: 1), measure radon/lizard, resources; commit findings file; report.

Ambiguities recorded (test the supported reading):
- Reset/import with wrong-typed fixture fields: 422 validation_failed expected (binding clarification "bad import 422 atomically"), although §5 says wrong type = 400 for requests.
- Invalid reset fixture: assumed 422 validation_failed and state unchanged.

## Status
Checks committed (186 tests, 116/116 ledger lines per coverage_map.py). Not yet run: stage-1 folder did not exist at commit time.
Run: `python verification/run_checks.py --out <outside-repo folder>`.
