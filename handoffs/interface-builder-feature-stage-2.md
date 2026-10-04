# Interface Builder — Stage 2 feature checkpoint

Dispatch: `f854261b07c28e247ba7a2bfc6ee74b1af599936`  
Feature contract: `fc078b6fbf6ed532bcd08bb6e1f417e9b47c4cca`  
Frozen Stage 1: `344e085d8e3d0629dcc17fc95f22a43efe2a85d2`  
Interface source revision: `a1ea8b3c88f1810dbcbec78d9e36941406ac2378`

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

Browser logs/screenshots are under `C:/Users/Prince/Documents/darkfactory/band-work/checks/stage2-interface-preliminary/` and `.../checks/stage2-interface-smoke/`, outside the source tree.

## Remaining integration work

At report time, core's Stage 2 feature modules were not yet present in the shared worktree; `git log` ended at this interface commit and the Stage 2 core module paths had no unstaged changes. Therefore the combined-table API integration, uncertainty/409 recovery against the completed domain implementation, stopped-Stage-1 export/import continuity, inherited Stage 1 suite against Stage 2, full Stage 2 suite, and isolated supplied harness have not been claimed as complete. This is an implementation checkpoint, not a Stage 2 acceptance claim. Run those checks against the integrated candidate when the core revision lands, then update this report with final results and any fixes.
