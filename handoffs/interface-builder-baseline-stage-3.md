# Interface Builder Stage 3 Baseline Report

Repository: `C:/Users/Prince/Documents/darkfactory/band-work/result`

Dispatch: `5140d0b4a04e71c478419d9a820ee15854ce778f`

Frozen Stage 2 baseline: `94e7654c4427fa3c087279675edbe1cda4f5a4fc`

Scope: copy-forward and behavior-preserving transport/UI restructuring only. No Stage 3 domain or UI behavior was added.

Baseline evidence recorded: `2026-10-04 08:28:41 UTC` (`16:28:41 +08:00`).

## Restructuring result

The copied transport, web handler, browser assets, template, Dockerfile, requirements, and `.dockerignore` already matched their Stage 2 counterparts byte-for-byte. The HTTP transport and bundled UI were already separated, so no source refactor was needed. I updated only `stage-3/RUN.md` to use the Stage 3 build context, image tag, and container name.

Interface-owned files committed:

- `stage-3/tablekeeper/server.py`
- `stage-3/tablekeeper/web.py`
- `stage-3/static/app.js`
- `stage-3/static/common.js`
- `stage-3/static/grid.js`
- `stage-3/static/site.css`
- `stage-3/templates/index.html`
- `stage-3/Dockerfile`
- `stage-3/RUN.md`
- `stage-3/requirements.txt`
- `stage-3/.dockerignore`
- `handoffs/interface-builder-notes-stage-3.md`
- `handoffs/interface-builder-baseline-stage-3.md`

## Observed checks

| Command or setup | Result |
|---|---|
| `docker build --no-cache --progress=plain -t tablekeeper:stage-3 .\stage-3` | Passed. Log: `C:/Users/Prince/Documents/darkfactory/band-work/checks/stage3-interface-baseline/docker-build.log`. |
| Containers with `--network none --cpus=2 --memory=2g`, first default `PORT=8080`, then custom `PORT=18080` | Both returned `GET /health` 200 `{"status":"ok"}`. Direct routes `/`, `/signup`, `/login`, `/lookup`, `/static/app.js`, and `/static/site.css` returned 200 with HTML, JavaScript, or CSS MIME types. Egress probe to `1.1.1.1:80` returned `connect_ex=101` (blocked). |
| Supplied interpreter and Playwright/Chromium on published port 19381 | Passed login, search, available single-table selection, booking form, booking confirmation, and lookup. Assertions covered `data-available=true`, the human table label and local start, prefilled party size, reference format, confirmed status, and zero page errors. Screenshot: `C:/Users/Prince/Documents/darkfactory/band-work/checks/stage3-interface-baseline/browser-booked.png`. |
| `git diff --quiet 94e7654c4427fa3c087279675edbe1cda4f5a4fc -- stage-2` | Passed; frozen Stage 2 source is unchanged. |
| `git diff --quiet 344e085d8e3d0629dcc17fc95f22a43efe2a85d2 -- stage-1` | Passed; frozen Stage 1 source is unchanged. |

The first browser attempt reached a pre-existing local service on port 18081 and got 404s. I identified the port collision and reran the smoke against the Stage 3 image on port 19381. One later attempt was made after the test container had been stopped and got connection refused; restarting the container and rerunning passed.

## Maintainability

Compared the Stage 3 interface source with the frozen Stage 2 interface source. All owned code files are byte-identical; only the run instructions changed.

- Radon, `server.py` and `web.py`: mean CC 2.64, maximum B (9).
- Lizard Python, `server.py` and `web.py`: 181 NLOC, 20 functions, average CCN 2.6, zero warnings.
- Lizard JavaScript: 359 NLOC, 46 functions, average CCN 2.7, maximum CCN 14, zero warnings.
- No Lizard thresholds were exceeded.

This is a restructuring baseline report, not a Stage 3 feature-completion or acceptance claim. Full Stage 3 checks remain for the integrated candidate after the coordinator releases the gate.
