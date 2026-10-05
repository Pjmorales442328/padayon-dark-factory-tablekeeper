# EVIDENCE.md: where to verify each claim

Message ids are from `room.json` (room `cca42262-ad07-40d0-bf44-60bb57c64f12`, 6,570 events, unedited full-session export).
Times are UTC. Manila time is UTC+8.

## Room messages

| What | Message id | Time (UTC) |
|---|---|---|
| Stage 1 dispatch (human) | `5199d6b9-9738-4e97-8457-15d6a3ceff54` | 2026-10-03 22:35:12Z |
| Stage 1 rejection of candidate ad2f1a2 (reviewer) | `33f59079-2e48-47cd-af82-38ae5341337a` | 2026-10-03 23:05:25Z |
| Stage 1 ACCEPT 344e085 (reviewer) | `80bdbd04-3598-489c-bb39-e08e4170e878` | 2026-10-03 23:13:19Z |
| Stage 2 dispatch (human) | `662eb735-7ee2-449d-b51a-abdddb20e42b` | 2026-10-03 23:22:32Z |
| Stage 2 ACCEPT 94e7654 (reviewer) | `ec93bfc8-1222-48b2-ac8d-729ed2fe69e3` | 2026-10-04 00:39:12Z |
| Stage 3 dispatch (human) | `cd5fbc94-a396-404b-9f6e-d70b32907047` | 2026-10-04 08:06:07Z |
| Stage 3 ACCEPT 8093f21 (reviewer) | `780f1bd3-91df-4a3c-87ee-5115932c2588` | 2026-10-04 09:17:30Z |
| Stage 3 final report (coordinator) | `7256c2e0-62c3-47a5-90ee-739a9c87f53b` | 2026-10-04 09:19:33Z |
| Stage 4 dispatch (human) | `6c3dee4d-1767-4309-af8b-b7795910da7d` | 2026-10-04 09:55:42Z |
| Stage 4 R1 audit: NOT ACCEPTED, M1 maintainability (reviewer) | `308028d3-93b9-429f-83cc-f31bb7cc6ec4` | 2026-10-04 10:59:38Z |
| Stage 4 R2 ACCEPT 8e929cc (reviewer) | `c5ae7655-6851-4d50-a2d9-e70228d42cc6` | 2026-10-04 11:29:29Z |
| Stage 4 final report (coordinator) | `5d91f723-c3b6-487a-9133-13070bbcadd6` | 2026-10-04 11:32:37Z |

## Claims and where they are

| Claim | Evidence |
|---|---|
| Exactly one human message per stage | the four `(human)` rows above; the only `User` messages in `room.json` |
| Two seats address each other by @handle, both directions | 19 directed pairs; run `python -m harness check` and `tools/audit.py` (G2 PASS) |
| Every stage reached from a clean container | `FACTORY.md` section 1; isolated run reports 120/120, 25/25, 7/7, 6/6, `claimed stage: 4` |
| Code came out of the room, nothing hand-written | `git log --format='%an' -- stage-*`: only `core-builder` and `interface-builder` |
| A rejection changed the work (stage 1) | rejection message above, fix commit `06ad44b`, tester regression `344e085`, accept message above |
| A rejection changed the work (stage 4, maintainability) | R1 audit message above; refactor commits `d144199`, `8e929cc`; reviewer close `c4edac4`; `handoffs/reviewer-findings-stage-4-r2-8e929cc.md` |
| Complexity did not decay | `FACTORY.md` section 1; `handoffs/final-report-stage-4.md` metrics table; worst function CC 9 at every stage |
| Every stage commit hash is posted in the room | audit T7: 25 of 25 |
| Per-stage time, tokens, dollars | `FACTORY.md` section 6; `handoffs/stage-*-record.md` |
| Failures disclosed rather than hidden | `FACTORY.md` sections 7 and 9; `handoffs/final-report-stage-4.md` "Open limitations" |
