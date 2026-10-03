# Interface Builder — Stage 2 copy-forward baseline

Repository: `C:/Users/Prince/Documents/darkfactory/band-work/result`

Dispatch: `d4a79d8a0f3b90e8c277e191a94aa37c5099727f`

Contract baseline: `fc078b6fbf6ed532bcd08bb6e1f417e9b47c4cca`

Frozen Stage 1: `344e085d8e3d0629dcc17fc95f22a43efe2a85d2`

## Behavior-preserving restructuring

- `75c57fbef13081a52e0167486514d81aa403dd9b` records all 197 ledger lines before changes or checks.
- `f06d952b3c3789631a06b0b3bb92c32c276ff712` changes only Stage 2 run instructions and notes.
- `2781da0c3ca622a20f7a5663f6e986f1f53027fe` commits the copied, exclusively owned `.dockerignore`, `Dockerfile`, `requirements.txt`, and `tablekeeper/server.py`.

The HTTP parser/serializer already calls the separate `tablekeeper.service.Service`; the copied transport did not need a code refactor. `RUN.md` was stage-1-specific, so it now builds `stage-2` and tags/runs `tablekeeper:stage-2`. No UI route, static asset, dependency, or API behavior was added. The copy had no `.git`; its generated `__pycache__` directory was excluded from commits by `.dockerignore`.

The copied `server.py`, `Dockerfile`, `requirements.txt`, and `.dockerignore` matched their frozen Stage 1 files byte-for-byte before the run-doc update. `git diff --quiet 344e085d8e3d0629dcc17fc95f22a43efe2a85d2 -- stage-1` returned success; no Stage 1 file was changed.

## Baseline build and run

- `docker build --no-cache -t tablekeeper:stage-2 .\stage-2`: passed; image tagged successfully.
- Run with `--cpus=2 --memory=2g -e PORT=8080 -p 127.0.0.1:18087:8080`: `/health` returned HTTP 200 `{"status": "ok"}` and `/restaurants` returned HTTP 200 `{"restaurants": []}`. Both responses had `application/json; charset=utf-8`.
- Run with `--network none --cpus=2 --memory=2g`, leaving `PORT` unset: `docker inspect` reported `NetworkMode=none`, `NanoCpus=2000000000`, `Memory=2147483648`; in-container `/health` returned HTTP 200. An external TCP connect probe returned `connect_ex=101` (network unreachable). `docker stats` reported 0.01% CPU and 14.5 MiB / 2 GiB.

These checks prove the copied baseline builds, starts and serves the API without outbound networking within the stated limits. They do not claim Stage 2 UI behavior, which remains gated until both builder baseline reports are accepted by the coordinator.
