# Interface Builder — Stage 2 feature checkpoint

Dispatch: `f854261b07c28e247ba7a2bfc6ee74b1af599936`  
Feature contract: `fc078b6fbf6ed532bcd08bb6e1f417e9b47c4cca`  
Frozen Stage 1: `344e085d8e3d0629dcc17fc95f22a43efe2a85d2`  
Interface source revision: `a1ea8b3c88f1810dbcbec78d9e36941406ac2378` plus the follow-up recorded in this update.

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
- The API group ran 89 tests: 85 passed and 4 failed, with zero errors/skips. The failures were the core-owned self-amendment race assertion (`[422, 201]`), the pre-existing kickoff manifest mismatch, a missing `HARNESS_OUT` because this group ran before the supplied harness, and the coordinator stage record not yet containing the final Stage 2 harness claim. These are not interface failures; the harness evidence was collected afterwards.
- The supplied isolated harness ran from the read-only kickoff directory with `HARNESS_OUT` set. Report `C:/Users/Prince/Documents/darkfactory/band-work/checks/harness-stage2-interface-r2/report.json` claims stage 2: Stage 1 passed 120/120 (zero skipped/deselected), Stage 2 passed 25/25 (zero skipped/deselected); the expected Stage 3 failure is the unimplemented `/restaurants/r_anker/policies` endpoint.
- The harness-run API check measured Stage 2 maintainability at max CC 9, mean CC 2.81, minimum MI 31.46; Stage 1 baseline was max CC 9, mean CC 2.64, minimum MI 31.28. The full API group's separate maintenance check gave the same ranks. The numbers are recorded for the team review, not as acceptance.
- A complete browser rerun initially exposed missing explanatory copy after an availability failure. The interface now says “We couldn't load availability. Please try again.” The targeted desktop/mobile search-error check passed 2/2, and the complete browser group passed 59/59 afterwards.

Browser logs/screenshots are under `C:/Users/Prince/Documents/darkfactory/band-work/checks/stage2-interface-preliminary/`, `.../checks/stage2-interface-smoke/`, and `.../checks/stage2-interface-integrated-final/`, outside the source tree. The isolated harness logs and report are under `C:/Users/Prince/Documents/darkfactory/band-work/checks/harness-stage2-interface-r2/`.

## Remaining integration work

The browser interface integration and isolated supplied harness are now verified. The independent API group remains open because of the three non-interface items above (the HARNESS_OUT evidence is now available, and the coordinator final record still needs the eventual Stage 2 claim). The complete independent suite and inherited suite have not yet passed together. This remains a verification checkpoint, not a Stage 2 acceptance claim; keep the assignment in progress until the remaining independent setup/core findings are resolved and final review is complete.
