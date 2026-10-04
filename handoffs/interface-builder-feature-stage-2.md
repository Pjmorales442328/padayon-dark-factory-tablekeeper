# Interface Builder — Stage 2 feature checkpoint

Dispatch: `f854261b07c28e247ba7a2bfc6ee74b1af599936`  
Feature contract: `fc078b6fbf6ed532bcd08bb6e1f417e9b47c4cca`  
Frozen Stage 1: `344e085d8e3d0629dcc17fc95f22a43efe2a85d2`  
Accepted interface source: `94e7654c4427fa3c087279675edbe1cda4f5a4fc`. Follow-up edit commit `9dffff30915a1ed1ccf62ac3a6cccffce2cb30c8` was restored by `365940a0e1a91b574a719ae9549aa1d10d91651f`; the current `stage-2/` tree is byte-identical to the accepted candidate.

## Files

- `stage-2/tablekeeper/server.py`
- `stage-2/tablekeeper/web.py`
- `stage-2/static/app.js`
- `stage-2/static/common.js`
- `stage-2/static/grid.js`
- `stage-2/static/site.css`
- `stage-2/templates/index.html`
- `stage-2/Dockerfile`
- `stage-2/RUN.md`
- `handoffs/interface-builder-notes-stage-2.md`

The browser provides the required search, single/pair seating choices, signup/login/logout, lookup and cancellation routes. It stores the active identity and pending booking body/key in session storage, ignores stale search responses, preserves form state after a `table_unavailable` response, and retries uncertain booking outcomes using the same request identity. The HTTP handler serves the HTML screens and bundled static assets before delegating API calls to `Service.dispatch`. Stage 1 remains byte-identical to the frozen revision.

## Commands and observed results

- `node --check stage-2/static/app.js`, `node --check stage-2/static/common.js`, `node --check stage-2/static/grid.js`: passed.
- `python -m py_compile stage-2/tablekeeper/server.py stage-2/tablekeeper/web.py`: passed.
- `git diff --check`: passed.
- `git diff --quiet 344e085d8e3d0629dcc17fc95f22a43efe2a85d2 -- stage-1`: passed; no Stage 1 changes.
- `docker build --no-cache -t tablekeeper:stage-2 .\stage-2`: passed after the final interface changes.
- Started the image with `--network none --cpus=2 --memory=2g -e PORT=8080`: health returned 200 in 0.84 seconds; all four HTML routes returned 200; CSS and JavaScript assets returned 200 with their expected MIME types; `/health` and `/restaurants` returned 200 JSON. `Europe/Berlin` and `America/New_York` loaded from bundled runtime tzdata. An outbound TCP probe returned `connect_ex=101` (network unreachable). Docker reported `none|2000000000|2147483648` and approximately 14.87 MiB RSS. The container was stopped after checks.
- Used the supplied interpreter and installed Chromium through `CHROMIUM_PATH`; no harness packages were installed. Tester-owned browser checks passed for screen routes (5), auth flow (1), mobile/desktop route visual and accessibility audit (2), keyboard focus (2), consistent visual system (2), search/no-slots (1), human labels (1), available-cell selection (1), signed-out selection (1), unavailable-cell no-op (1), and lookup/cancel (1). These targeted runs had zero failures, errors, or skips.
- Additional real-browser checks at 375px and 1280px found no horizontal overflow. The legacy single-table flow rendered a successful Stage 1-style receipt that only included `table_id`. No browser JavaScript errors were observed in these flows.
- After core revision `959aed77ac3c829080c382578b023a4cc8f5305b` landed, `verification/stage2/run_stage2.py --part browser` ran 59 tests with zero failures, errors, skips, or deselections. This includes the complete responsive/visual and real Stage 1-to-Stage 2 browser-upgrade test, which stopped the source service before importing its export.
- My initial API group ran 89 tests: 85 passed and 4 failed, with zero errors/skips. The failures were the self-amendment race setup (`[422, 201]`), the pre-existing kickoff manifest mismatch, `HARNESS_OUT` being absent because this group ran before the supplied harness, and the coordinator stage record not yet containing the final claimed-stage-2 entry. Tester evidence `786bddb` later corrected the check/evidence issues; no interface defect was reported.
- The supplied isolated harness ran from the read-only kickoff directory with `HARNESS_OUT` set. Report `C:/Users/Prince/Documents/darkfactory/band-work/checks/harness-stage2-interface-r2/report.json` claims stage 2: Stage 1 passed 120/120 (zero skipped/deselected), Stage 2 passed 25/25 (zero skipped/deselected); the expected Stage 3 failure is the unimplemented `/restaurants/r_anker/policies` endpoint.
- The harness-run API check measured Stage 2 maintainability at max CC 9, mean CC 2.81, minimum MI 31.46; Stage 1 baseline was max CC 9, mean CC 2.64, minimum MI 31.28. The full API group's separate maintenance check gave the same ranks. The numbers are recorded for the team review, not as acceptance.
- A complete browser rerun initially exposed missing explanatory copy after an availability failure. A temporary interface edit changed the text to “We couldn't load availability. Please try again.” The targeted desktop/mobile search-error check passed 2/2, and the complete browser group passed 59/59 afterwards. Coordinator's R2 freeze condition then required retaining the exact reviewer-accepted source; that text edit was removed from `stage-2/static/app.js` in commit `365940a0e1a91b574a719ae9549aa1d10d91651f`. No extra behavior remains in the accepted tree.

Browser logs/screenshots are under `C:/Users/Prince/Documents/darkfactory/band-work/checks/stage2-interface-preliminary/`, `.../checks/stage2-interface-smoke/`, and `.../checks/stage2-interface-integrated-final/`, outside the source tree. The isolated harness logs and report are under `C:/Users/Prince/Documents/darkfactory/band-work/checks/harness-stage2-interface-r2/`.

## Integrated status

The reviewer accepted exact source revision `94e7654c4427fa3c087279675edbe1cda4f5a4fc` in `reviewer-acceptance-stage-2-94e7654.md`; the interface-owned `stage-2/` tree now matches it exactly after R2 cleanup. Tester evidence `tester-final-evidence-stage-2-94e7654.md` records its 326-test run (four historical failures, zero errors/skips) and focused rerun: the claimed-stage check passed, leaving the pre-run kickoff manifest mismatch and two explicitly superseded inherited shape assertions. Final freeze bookkeeping is coordinator-owned. This report records observed interface runs and does not supersede the reviewer decision or coordinator stage record.
