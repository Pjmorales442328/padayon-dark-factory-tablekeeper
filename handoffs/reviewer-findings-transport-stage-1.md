# Reviewer findings: transport checkpoint d9f70db6623672f53e664795257dccedf732cb9d

Scope: interface-builder files server.py, Dockerfile, RUN.md, requirements.txt, .dockerignore. Core service.py was absent at the checkpoint, so Docker build and integration were not run (pending, not a rejection).
Method: ran server.py from a clean `git archive` of d9f70db against a stub Service (outside the repo, in %TEMP%\rv) using the harness interpreter; script t.py, output out.txt.

Result: scoped ACCEPTANCE of the transport files, with 2 advisories. No defect found.

Verified (observed):
- Invalid JSON, empty body, array body, NaN, 100000-deep nesting, 6000-digit int, bad UTF-8, BOM: all 400 malformed_request, application/json; charset=utf-8, rejected before dispatch (so 400 precedes auth, matching spec 7 "after parsed as JSON object and authenticated").
- Empty PATCH body -> 400; POST .../cancel with empty body reaches dispatch with body None.
- Query: first value kept, blank kept, unknown params passed through; path unquoted.
- Dispatch exception -> 400 JSON, logged, no 5xx; 5xx status from Service is mapped to 400.
- 200 concurrent requests against a 0.3s handler: all 200, max latency 0.81s (Windows host, not Linux container).
- Dockerfile/RUN.md/requirements.txt (comment-only, pip accepts)/.dockerignore read: PORT default 8080, 0.0.0.0, tzdata installed, no runtime network use.

Advisories (not rejections):
1. A1: Transfer-Encoding: chunked request bodies get 400 (server reads only Content-Length). Valid JSON sent chunked is wrongly rejected. Fix in server.py if the harness client can chunk; low risk.
2. A2: request_queue_size is the socketserver default 5; 50 simultaneous connects on Linux may see SYN retransmit delays. Re-measure in the container at full review.

Pending at full review: container build with network blocked and limits, health within 60 s, all ledger lines C, supplied and tester checks, version transfer, maintainability, screens (no UI, so n/a if none), frozen folders.
