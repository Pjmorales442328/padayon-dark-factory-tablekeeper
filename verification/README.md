# Independent black-box checks, stage 1

Run (from the repository root; builders run this before handoff):

    python verification/run_checks.py --out <folder outside the repo>

The runner starts two independent services itself with `python -m tablekeeper.server` in `stage-1`
(PORT chosen per process; override with `SERVICE_CMD` / `SERVICE_CWD`), or tests running ones via
`BASE_URL` and `BASE_URL2` (second is the import target). `-k <text>` selects tests by name.
`python verification/coverage_map.py -v` lists which checks cover each ledger line (test names carry `L###`).
Docker-based checks need a running Docker daemon; they fail (not skip) if it is missing.
Only the standard library is used. Exports (tokens, hashes) are held in memory, never written.
