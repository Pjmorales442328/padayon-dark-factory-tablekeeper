# Stage 2 R1 closure

Opened: 2026-10-04T07:49:16+08:00 (observed dispatch time; original rounded 07:50 header corrected here).
Closed: 2026-10-04T07:53:34+08:00. Elapsed: 258 seconds.
Owner: tester. Findings source core-builder-findings-stage-2-run-1.md at11997585c60f94b0b060a2879899ff1db7eb84c6.
Correction/findings revision d4ffa21632bd21b6a8e5931b50b9c2b56adbdcba, author tester; handoffs/tester-findings-stage-2-r1.md.

T1 overlapping capacity setup reordered. T2 exactly-one winner now uses distinct bookings; same-reservation serial race invariant separately checked. T3 post-export mutation uses free Friday slot. T4 actual stage1 process exit and port closure required before destination start/import. T5 booking owner determines token. T6 unchanged export re-import before baseline observations. T7 fixed source snapshot/path list in fuzz, destination only restored. I4 supplied-capable interpreter lookup corrected without installs. All re-derived independently from specs.
Exact core11997585 rerun: inherited178 tests, zero unexpected failures/errors/skips, two explicitly superseded frozen shape assertions retained and replaced by passing stage2-specific checks; API/transfer/process89 tests, seven pending delivery/evidence/environment failures, zero errors/skips. All combined-domain/API/atomic race/state-transfer checks pass. Source-stop proof uses actual frozenstage1 process, no mock.
Reviewer independently scoped accepts exact core11997585 at567c3f5eac2610b18dd9085dcacf1943fdd7ffde, including stopped-source container transfer and immutable stage1 create/batch receipts. No full stage2 acceptance.
Pending interface candidate: HTML/assets/browser order/uncertainty/conflict/upgrade,375px/desktop/accessibility,screenshots,integrated harness claimedstage2/final record and refreshed metrics. Kickoff mismatch retained as environment evidence.
