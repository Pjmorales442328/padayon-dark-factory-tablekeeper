# Interface Builder — rejection R1 resolution evidence

Repository: `C:/Users/Prince/Documents/darkfactory/band-work/result`

R1 opened: 2026-10-04T06:55:12+08:00

Target findings revision: `0130c11b286f8b71671e0cdf44e00bd215c365e4`

Fix revision: `ad2f1a2cb3ee213645167a8d384fd393d4d95e3c` (`interface-builder`)

Changed transport: `stage-1/tablekeeper/server.py` sets
`ThreadingHTTPServer.request_queue_size = 128`, increasing the default accept
backlog so 50 simultaneous connections are not reset. Requirement/checklist and
observed R1 evidence are in `handoffs/interface-builder-stage-1-notes.md`.

## Observed checks

The service image was built from `stage-1/` after the queue fix:

```text
docker build -t tablekeeper-interface-stage1 .\stage-1
PASS — image built and tagged tablekeeper-interface-stage1:latest.
```

A port-published container used the documented `PORT=8080` setting and the stated
resource limits. The host health request returned:

```text
HTTP 200
{"status": "ok"}
```

A separate network-isolated container was run with `--network none`, `--cpus=2`,
`--memory=2g`, and `PORT=8080`. Health was checked through loopback inside the
container because a `none` network has no host-published port:

```text
docker inspect: network=none, NanoCpus=2000000000, Memory=2147483648
inside-container GET /health: HTTP 200 {"status": "ok"}
ZoneInfo("America/New_York"): loaded successfully from bundled IANA tzdata
TCP connect probe to 1.1.1.1:443: connect_ex=101 (network unreachable)
docker stats: 0.01% CPU, 14.48 MiB / 2 GiB memory
```

The committed black-box concurrency check was run from `verification/` using the
supplied interpreter and `SERVICE_CMD` set to that interpreter plus
`-m tablekeeper.server`:

```text
python -m unittest test_f_process.Load.test_L008_L009_L032_fifty_in_flight_no_5xx_and_latency
Ran 1 test — OK
50-way bursts: max latency 0.53 s, n=150
```

The full independent suite and supplied harness are separate outstanding Stage 1
acceptance work; this focused report claims only the transport finding and checks
listed above.
