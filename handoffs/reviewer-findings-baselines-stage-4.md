# Reviewer findings: Stage 4 baselines (core 88686a8 / evidence 6b2a372; interface 8e4e161 / evidence faf8825)

Decision: BASELINE ACCEPTED for core (exact 88686a81f626aec2e8b28cd01266a5acec7b1b20) and for interface (exact 8e4e161166d4cae499a587acd723d50d8b39a0a2, evidence faf88256f4cdde405166b636051e7be147abb4f9). This is a baseline gate only: no Stage 4 feature is accepted, and none can be, because none exists yet. No defects found.

## Evidence (commands run by me at HEAD faf8825)
- `git archive 8093f21 stage-3` vs `git archive faf8825 stage-4`, `diff -ru`: exactly three files differ.
  - RUN.md: Stage 3 to Stage 4 names, image tag and container name only (interface).
  - tablekeeper/loading.py: the `state_loading` import moved from the bottom of the file to the top (core).
  - tablekeeper/service.py: `api_routes` import moved to the top; unused `moves`, `chronology` imports and the unused `inspect_booking` name dropped (core).
  - Every other file, including server.py, web.py, static/**, templates/**, Dockerfile, requirements.txt, .dockerignore and every other core module, is byte-identical to frozen Stage 3. Behaviour-preserving, no feature added. Import smoke test passes (no circular import).
- Frozen trees: `git diff --stat 344e085 HEAD -- stage-1`, `94e7654 HEAD -- stage-2`, `8093f21 HEAD -- stage-3` all empty. `git status` for stage-4 shows no uncommitted change (only untracked __pycache__, not staged).
- Exact supplied harness from the kickoff directory: `python -m harness run --track tablekeeper --repo C:/Users/Prince/Documents/darkfactory/band-work/result --stage 4 --mode isolated --out C:/Users/Prince/Documents/darkfactory/band-work/checks/reviewer-s4-baseline-h1`: stage 1 pass, stage 2 pass, stage 3 pass, stage 4 FAIL (features absent, expected), "claimed stage: 4 on the shipped checks", highest contiguous stage 3. Report: checks/reviewer-s4-baseline-h1/report.json. Not a Stage 4 pass.
- Clean build and run from the committed archive: image builds; `--network none --cpus=2 --memory=2g`: probed from inside the container, /health 200 JSON, /, /signup, /login, /lookup text/html, /static/app.js text/javascript, /static/site.css text/css, reset 204, export 200 with track and format_version; replans route absent as expected (401 for unauthenticated generic path).
- Maintainability (radon, lizard) on stage-4/tablekeeper: radon mean CC 3.146 (178 blocks), identical to Stage 3, max 9, no block above 10; lizard 1440 NLOC, 174 functions, mean CCN 3.2, 0 warnings; largest file 171 lines. No figure is worse than frozen Stage 3. Interface's JS and server/web figures are unchanged because those files are byte-identical.

## Observations (not defects)
- Core reports 148 independent API checks with 3 visible failures (stale Stage 3 RUN regex, stage-3 claim assertion, pre-run kickoff manifest mismatch). They are inherited-check and environment items, correctly disclosed; I did not rerun the 148-check suite because the diff above proves no behavioural change, and the harness reproduces stages 1-3.
- F10 (mean complexity, service.route/private, loading.booking_record) is unchanged, not addressed by the restructure; it remains an advisory to be handled within feature work. No complexity increase from the restructure.
- Carried advisories: chunked bodies return 400; reset cost scales with state; duplicate-block metrics unavailable; kickoff manifest mismatch predates the run; untracked __pycache__ must never be staged.

## Gate
Both scoped baselines hold. The coordinator may release the feature gate. The full eight-check candidate review follows only on an exact named revision with all ledger lines 293-351 implemented.
