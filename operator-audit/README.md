# operator-audit: an independent, spec-derived test suite

Written by the team lead (with Claude Code as operator) **after all four stages were frozen**. The seats never
saw it, no file under `stage-*/` was touched, and nothing here fed back into the code. Its job is to answer one
question: if the organisers' hidden checks are the spec's checks, does what the band built hold?

It is separate from the tester seat's own checks in `verification/`: different author, written fresh from
`spec/stage-1.md` to `spec/stage-4.md`, and aimed at the places a grader is likely to probe beyond the
shipped samples.

## What it covers

| Area | Files | How |
|---|---|---|
| Stage 1 contract, auth, errors | `test_s1_auth`, `test_s1_fuzz` | every status and `error.code` in the spec tables, junk bodies and odd URLs never produce a 5xx |
| Availability, booking, amend, cancel | `test_s1_availability`, `test_s1_create`, `test_s1_manage` | slot grid maths, half-open occupancy, cutoff boundary measured against the clock, atomic failed amendments |
| Idempotency | `test_s1_idem` | replay, key scope, key reuse with an invalid body, failed-then-reused keys, 12-way identical race |
| Time zones and DST | `test_s1_time` | Berlin and New York, spring-forward gaps, fall-back first occurrence, absolute-duration `ends_at` |
| Concurrency and limits | `test_s1_conc`, `test_s1_limits` | 50 racers, racing amendments, racing signups, reset under traffic, 300 users, 1,500 seeded reservations |
| Export and import | `test_s1_state` | tokens, hashed logins, receipts, batch receipts, failed keys, atomic invalid imports |
| Atomic moves | `test_s1_moves` | swaps, rollback, input-order error precedence, replay |
| Combined tables | `test_s2_tables` | option order, capacity sums, non-transitive pairs, pair races |
| Browser | `test_s2_ui_*` | testids, 375 px and 1280 px, axe, focus, out-of-order searches, lost responses (committed and uncommitted), conflict handling, upgrade mid-retry |
| Explanations and history | `test_s3_explain`, `test_s3_history` | rule order, `seq`, `revision`, no-op rules, `expected_revision`, owner-only 404s |
| Policies and series | `test_s3_policies`, `test_s3_series`, `test_s3_moves` | 24 invalid policies, effective-date selection, atomic adoption, per-occurrence policy, DST in series |
| Seating changes | `test_s4_replan`, `test_s4_replan_oracle` | a brute-force planner re-solves 83 random seating problems (70 single closures, 13 chained closures) and the service must return the identical plan |
| Recurring amendments | `test_s4_series_amend` | validation matrix, precedence, atomic rollback, replay, 12-way race |
| Restaurant revision | `test_s4_revision` | every counting rule |
| Randomised operations | `test_model_based` | random book/cancel/amend/move/series/amend/replan sequences, with no-double-occupancy, availability, history and revision invariants checked after every step |
| Upgrades | `test_transfer` | exports from stages 1, 2 and 3 imported into stage 4, receipts replayed byte for byte |
| Edge cases | `test_extra_edges` | per-weekday hours, late-evening local dates, 64-character ids, huge party sizes, UI under 5xx |

## Run it

```sh
export KICKOFF=<path to the organisers' kickoff package>      # harness plugin + fixtures
docker build -t tk-s4 ./stage-4 && docker run -d --rm -p 29104:8080 -e PORT=8080 tk-s4
./run.sh 29104 tests                                          # everything, against stage 4
./run.sh 29104 tests -m "s1 and not s2"                       # one stage's requirements
AUDIT_SEEDS=60 AUDIT_STEPS=60 ./run.sh 29104 tests/test_model_based.py
AUDIT_SOURCES="1=http://localhost:29101,2=http://localhost:29102,3=http://localhost:29103" AUDIT_TARGET=4 ./run.sh 29104 tests/test_transfer.py
```

The browser tests use Microsoft Edge through Playwright (`channel="msedge"`); change it in `conftest.py` if needed.

## Results (stage 4 image, run 5 Oct 2026)

| Run | Outcome |
|---|---|
| everything against stage 4 (`results/final-stage4.txt`) | **506 passed, 0 failed**, 8 skipped (5 random scenarios with no first plan, 3 upgrade cases that do not apply), 1 expected failure (chunked bodies, a limitation `FACTORY.md` already discloses) |
| 3,600 random operations (`results/model-based-long.txt`) | 60 seeds x 60 steps, every invariant held after every step |
| stage 1, 2, 3 images against their own stage's requirements | 183, 230 and 315 passed, 0 failed |
| stage 1 and 3 images against later stages' tests | fail, as they should: the suite tells the stages apart |

Every failure seen while writing the suite was a mistake in the test (a misread spec sentence, an overlapping fixture,
an off-by-one in an expected offset), found by re-reading the spec, and fixed there. No service result was ever
excused. Where the spec is silent on 400 versus 422 for a wrongly typed field, the suite accepts either.
