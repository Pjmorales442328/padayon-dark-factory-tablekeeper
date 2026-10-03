# Reviewer findings: Stage 2 baseline gate, core checkpoint 51ff2cba48f15d65ad9177fc84afbebbf18c8d34 (report 177e213b66d344c2571236f2da2e2d4fc8415dac)

Decision: SCOPED BASELINE ACCEPTANCE of the core restructuring. Not a stage-2 acceptance; new stage-2 behaviour (ledger lines 22 partly, 58, 62, 69, 78, 81, 105, 118-116 UI items, 152-197) is pending. No defects found.
Examined tree: git archive 528e317 stage-2 vs git archive 344e085 stage-1 (rv/s1, rv/s2).

Evidence:
1. Frozen stage 1 unchanged: `git diff --stat 344e085 528e317 -- stage-1` empty.
2. Restructuring diff (`diff -r s1/stage-1 s2/stage-2`): only RUN.md titles/tags, new identifiers.py (`unused(existing, generate)`), and 4 call sites replacing identical collision loops (accounts token and user id, bookings reference and reservation id). Generation formats unchanged. Dockerfile, requirements.txt, .dockerignore, server.py, all other modules byte-identical to stage 1. No __pycache__ tracked.
3. Container built from 528e317 stage-2 (network none, 2 CPUs, 2 GiB): my stage-1 probe script gives output identical to frozen stage 1 (only random ids differ); 50-way mixed load x3 rounds with 0 and 300 reservations: no 5xx, max 1.4 s.
4. Supplied harness stage 1 against stage-2: 120/120, 0 skipped/deselected (rv/h4/stage-1.counts.json).
5. Maintainability (radon cc): average A 2.64 (stage 1) -> 2.59 (stage 2); max rank B (7) both; no function worse than before; files unchanged in size except identifiers.py (8 lines).
6. Reading: no order, timing or check-specific logic added.

Pending, not defects: the interface-builder baseline (stage-2 server.py/Dockerfile restructuring is not yet reported, files are still copies); chunked-body 400, reset latency per user and availability scan cost from stage 1 remain open advisories; kickoff manifest mismatch (harness/cli.py, docs/participant-guide.md) predates the run.
