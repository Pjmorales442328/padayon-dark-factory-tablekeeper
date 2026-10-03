# Core Stage 2 initial implementation checks

Repository: C:/Users/Prince/Documents/darkfactory/band-work/result
Requirements: handoffs/requirements-stage-1.md and requirements-stage-2.md
Feature release: f854261b07c28e247ba7a2bfc6ee74b1af599936
Implementation code revision: 959aed77ac3c829080c382578b023a4cc8f5305b, author core-builder
This record and selection-cardinality precedence fix are committed together. No service acceptance or final integrated handoff claimed.

Implementation is available to the interface: current views use table_ids and singleton-only table_id; available_options covers free declared pairs; member occupancy, no-op pair reversal and batch replacement are atomic; legacy/current snapshots are validated without rewriting successful original JSON receipts; seeded cancelled records do not occupy members. Interface confirmed contract177e213 before features.

Observed commands, supplied interpreter with SERVICE_CMD explicitly pointing to it:
1. verification/stage2/run_stage2.py --part inherited --out C:/Users/Prince/Documents/darkfactory/band-work/checks/core-stage2-inherited-1:178 tests,176 passed,2 explicitly superseded strict Stage1 shape assertions,0 errors/skips. The two changed shapes are independently covered by new Stage2 checks. All inherited behavioral checks passed. Latency0.49s/150 mixed requests;50 logins1.72s;reset302users9.72s/status204;health0.50s,RSS5MiB.
2. verification/stage2/run_stage2.py --part api --out C:/Users/Prince/Documents/darkfactory/band-work/checks/core-stage2-api-1:88 tests,13 failures,1 error,0 skipped; full API group including delivery/evidence checks ran. Logs outside repository under the named folders and their .console.txt files.
3. git diff --exit-code344e085d8e3d0629dcc17fc95f22a43efe2a85d2 -- stage-1:PASS, no frozen source drift.

Core adjustment: cardinality above two now gives combination_not_allowed before checking duplicate members. A selection above two is categorically unsupported by the explicit Stage2 error table; duplicate-member validation remains for supported sizes. Fresh complete reruns required.

Tester-owned requirement/setup findings:
T1. Create.test_L069_L170_summed_capacity books t_1+t_2 at19:00 then expects t_2+t_3 at18:00 to succeed. Absolute90-minute intervals overlap on t_2; choose a nonoverlapping slot for the intended small-party-on-pair case.
T2. Races.test_L181_races_between_create_and_patch_and_move races PATCH and move for the SAME existing reservation. Both can succeed in a valid serial execution because the second amendment replaces its own occupancy. Exactly one conflicting booking must survive, but one successful HTTP response is not required for those two self-amendments. Use distinct existing reservations for an exactly-one-winner test, or assert allowed serial outcomes/invariant.
T3. TestStage2Roundtrip.test_L088_export_snapshot_detached_with_pairs books t_1+t_2 at20:30 after population holds pair19:00 and t_2+t_3 at21:00; new booking overlaps21:00 on t_2. Use an actually free slot/member set for post-export mutation.
T4. TestUpgrade computes source_stopped_before_import immediately after process wait and port check; it was false, while the next no-source-port test passed. Wait for port closure before starting destination/import so the required actual stopped-source proof is reliable.
T5. TestUpgrade.test_L154_L184 chooses Bob token only for dynamic booking D; seeded BOBSEED1 also belongs to Bob, so lookup correctly returned404 when the test used Ada token. Choose token from source owner list, not comparison with one dynamic ID.
T6. TestUpgrade shares a destination across test methods; earlier methods mutate imported occupancy, then L184 compares later availability against original source snapshot. Restore the unchanged export before each observation that requires the baseline.
T7. TestStage2ImportValidation.test_L183_fuzz calls self.setUp after accepted mutation, regenerating self.exp/session-token keys while still iterating paths from original export. Later deletion of an old token key raises KeyError inside the check before service HTTP. Keep a fixed source snapshot/path list and restore destination only, or rebuild paths consistently.

Integration/evidence still pending, not domain defects:
I1. Interface UI/static assets were under construction during API run: delivery GET / returned500 and assets /static/app.js404. Recheck only once interface's full candidate is ready.
I2. Pre-existing kickoff manifest mismatch remains visible (docs/participant-guide.md,harness/cli.py).
I3. HARNESS_OUT was unset because full Stage2 harness awaits complete interface; claim/final-stage-record checks are premature until the integrated run.
I4. Maintainability check invokes bare python outside supplied environment and found no radon. Core will prepend provided .venv/Scripts to process PATH for final invocation without installing anything or changing harness.

Full combined API, transfer and integrated browser/supplied checks must be rerun after tester/setup corrections and interface completion. Core owns no verification or interface files and has not modified either.
