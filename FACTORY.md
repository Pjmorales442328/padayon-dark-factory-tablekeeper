# FACTORY.md — the Padayon factory

A five-seat BAND factory that took the **tablekeeper** track from stage 1 to **stage 4** in one room
(`PADAYON RUN V6`, id `cca42262-ad07-40d0-bf44-60bb57c64f12`) with exactly **one human message per stage**.
Everything under `stage-*/` was written by the seats; the human wrote only this file, `README.md`
and the dispatch messages (see "What the human did").

## 1. Result at a glance

| Stage | Started (UTC+8, 4 Oct) | Frozen | Elapsed | Accepted revision | Harness (isolated) | Codex-seat tokens |
|---|---|---|---|---|---|---|
| 1 | 06:35:00 | 07:13:39 | 38m 39s | `344e085` | 120/120 | 15.1M |
| 2 | 07:22:55 | 08:48:22 | 1h 25m 27s | `94e7654` | 25/25 | 53.7M |
| 3 | 16:06:39 | 17:17:42 | 1h 11m 03s | `8093f21` | 7/7 | 54.4M |
| 4 | 17:55:59 | 19:30:07 | 1h 34m 08s | `8e929cc` | 6/6 | 76.7M |
| **Total** | | | **4h 49m 17s** of factory time | | **158/158, claimed stage 4** | **199.9M** |

- Stages 1-3 were frozen before the next began; stage 4 imports state exported from a stopped stage 3
  (and 2 and 1). Folders are never edited after freeze (`git log` shows it).
- Between stages the factory idled (quota windows, overnight): wall clock 06:35 to 19:30 is 12h 55m.
- Maintainability **did not decay**. Radon over the service code at each stage: worst function
  complexity **9 at every stage**, **0 functions above 10**, largest file 132 lines, 0% duplicated lines
  (291 functions at stage 4). Mean CC 2.64 → 2.81 → 3.15 → 3.12: it rose with the features and was
  pulled back at stage 4 by a reviewer rejection (section 5).
- Work was shared: share of tool calls in the room export is interface-builder 24%, tester 21%, reviewer 19%, coordinator 18%, core-builder 17%; of 136 commits, coordinator 43, interface-builder 25, tester 25, core-builder 24,
  reviewer 19; every seat commits under its own name; history is never rewritten.

## 2. The seats

| Seat | Harness | Model | Owns |
|---|---|---|---|
| coordinator | Codex | gpt-6.1-sol | requirements ledger, file ownership, handoffs, routing rejections, timing, freeze, final report. Writes no code. |
| core-builder | Codex | gpt-6.1-sol | state, rules, storage, export/import |
| interface-builder | Codex | gpt-6-luna | request layer, browser screens, Dockerfile, RUN.md |
| tester | Claude Code | claude-sonnet-5-5 | independent black-box checks from the spec; never reads the service source |
| reviewer | Claude Code | claude-sonnet-5-5 | accepts or rejects one exact committed revision; fixes nothing |

Mandates are in `mandates/`, one per seat, each starting with `Harness:` and `Model:`.
They contain no endpoint, field, error-code or test-id from any track: they say how a seat works
(owns, hands off, rejects), not what the product is. They passed the official `harness check` on the
tablekeeper, pocketful and toy tracks; the unchanged earlier version built toy stage 1 (8/8 shipped,
9/9 independent, no human help) in a rehearsal.

## 3. How the factory behaves (design choices and why)

1. **One owner per file, no exceptions.** The coordinator writes a ledger (one line per testable spec
   sentence: 116 lines at stage 1, 197 at 2, 292 at 3, 351 at 4) and assigns files. Two seats can
   never edit the same file, so there are no merge fights and every defect has an owner to route to.
2. **Tester is blind to the code.** It builds checks from the ledger and spec only, so a bug cannot hide
   in a check that was written to fit the code. The tester's own checks are audited by the builders too:
   tester defects were found and corrected in every stage (section 5).
3. **Reviewer judges one exact revision.** A hash, the full spec, the ledger. It runs its own probes
   (container with no network, 2 CPU / 2 GiB, 50-way races, browser at 375 px and 1280 px with axe) and
   never fixes code. Acceptance names a revision; the freeze happens only on a clean tree equal to it.
4. **Copy forward, then restructure first.** Each stage folder is a copy of the last. Before any new
   feature the builders do a short restructuring pass that the reviewer accepts as a baseline. This is
   why complexity stayed flat instead of compounding.
5. **Rejections carry evidence by path and revision, not by paste.** The coordinator may not soften or
   overrule findings. Every handoff includes the complete stage spec, split into numbered parts.
6. **Mandates are generic by construction.** The product lives only in the dispatch. Swapping the track
   changes one message.
7. **No in-turn polling.** Seats only receive messages between turns, so mandates forbid sleeping
   inside a turn and make the coordinator keep working after any readiness mention.
8. **Context is capped.** Claude seats launch through a wrapper that passes `--autocompact 150000`
   after the tester and reviewer reached about 800k tokens of context (this alone drove their cost);
   Codex seats get `compact-at 100000`. Coordinator mandate: compact the tester and reviewer before
   each handoff to them.

## 4. Standing the factory up (another team, another problem)

1. Install Band Desktop and the `band` CLI; sign in.
2. Create five seats with `band agent create` (transports: `codex-app-server` for Codex, a Claude
   Code launcher for Claude), each with `--instructions-file mandates/<seat>.md`. One working
   directory for all seats; dispatches give absolute paths.
3. Run seats through launcher scripts that isolate their config from the operator's own tools
   (a seat-only `CODEX_HOME`; `claude --setting-sources local`).
4. Open one room, add the five seats, then per room set runtime settings (approval `never`,
   sandbox `danger-full-access`, model/effort per seat, compact-at). New rooms start with approval
   prompts, so this must be redone for every room.
5. Post one dispatch per stage, `@`-mentioning **only the coordinator** (Band delivers the whole
   message to every mentioned seat). The dispatch names the spec path, the result repo, the handoff
   folder, the harness command and the freeze rules. Nothing else is sent to the room.
6. Do not nudge, approve or repeat a dispatch. If a seat stalls, that is the run.
7. At the end download the full session from the Band console as `room.json` and write the docs.

## 5. How it catches and recovers from bad work

| Where | What was caught | Who caught it | What changed |
|---|---|---|---|
| Stage 1, R3 | Seeded fixture passwords were subject to the signup minimum | reviewer (D1) | core fix `06ad44b`; tester added a regression check that fails on the rejected code and passes on the fix |
| Stage 1, R1 | 150-way burst could drop connections | core-builder | transport queue raised, `ad2f1a2`; 0.53 s max, no 5xx |
| Stage 2, R1 | seven defects in the tester's own checks (encoding, slot count, receipt precedence, DST fold overlap) | core-builder | tester corrected only the confirmed ones (`d4ffa21`), source untouched; closed in 258 s |
| Stage 3, R1 | upgrade compatibility: UI broke against a legacy service that 404s a newer endpoint | core-builder, confirmed by reviewer | `8093f21` treats only that 404 as empty; reviewer proved same-tab upgrades from frozen stage 1 and 2, 17/17 each; closed in 10m 49s |
| Stage 4, R1 | checkpoint of 560 tests: 33 failures, 16 errors, disclosed honestly and never described as clean; F1-F23 tester check defects (oracle arithmetic, series fixtures, history selectors) | tester self-report, reviewer | routed 67 s after the checkpoint, first corrections in 8m 44s, last in 23m; 40m 59s from routing to independent closure |
| Stage 4, R2 | **maintainability regression**: mean CC 3.146 → 3.429, min MI 31.46 → 30.65, worst function NLOC 25 → 26. Not waived. | reviewer (M1) | two real refactors (`d144199`, `8e929cc`) split revision and conflict responsibilities; independently remeasured at or below the stage-3 baseline; 28m 50s |
| Stage 4, reviewer | reviewer's own finding T1a withdrawn after the tester showed the superseded entry passing | reviewer | decision unchanged, no padding |

Independent reviewer probes at stage 4: 297 API probes, 1051 optimizer previews (779 feasible,
272 infeasible, 0 mismatches against an exhaustive oracle), 157 bad imports, 482 requests across 50
workers with no 5xx (max 0.60 s), 76 browser checks at 375 px and 1280 px with axe.

## 6. Cost and time (measured)

- **Time:** 4h 49m 17s of factory time across four stages (table in section 1).
- **Claude seats (tester, reviewer):** 175.9M tokens, **$59.19** at list prices by `band usage rooms`
  (tester $31.33, reviewer $27.86). Band labels this an estimate, not a bill. Band reports one figure per
  room, so the per-stage split below is our apportionment of that $59.19 by token-weighted usage read from
  the two seats' transcripts (cache reads 0.1, cache writes 1.25, output 5 relative to fresh input):
  stage 1 about $6.2, stage 2 $12.7, stage 3 $25.7, stage 4 $12.3, $2.3 outside the stage windows.
  Stage 3 was the expensive one because the Claude seats' context had grown to about 800k tokens.
- **Codex seats (coordinator, core-builder, interface-builder):** 199.9M tokens across the four stages
  (+5.7M between stages, +9.1M after the final freeze), about 96% cached. They ran on a flat ChatGPT
  plan, so no per-token invoice exists; tokens are counted from the Codex session logs.
- Before the context cap the Claude seats reached ~800k tokens of context each; after compaction
  it sat at 45-55k. The cap was the biggest cost lever we found.

## 7. What we tried that failed (and what it cost)

| Rehearsal | What happened | Fix in the factory |
|---|---|---|
| Toy, 3 Oct | coordinator slept inside turns, declared the reviewer silent, posted a false "blocked" report | mandates ban in-turn polling; exact author-name rule |
| Tablekeeper, 3 Oct (2 min) | deadlock at the readiness gate after Band delivered a message twice; seat dismissed the redelivery as a duplicate | answer redelivered messages; coordinator never idles on the gate; dispatch mentions only the coordinator |
| V5 stage 2, 3-4 Oct | 7 rejection rounds, then the Codex 5 h limit hit and nothing woke the seats; a human "continue" would count as steering | scrapped; full fresh run from stage 1 in V6, stop line replaced by "keep working until accepted or record the blocker" |
| Seat fuel | AgentRouter blocked, Gemini CLI ineligible, Copilot unreliable headless, Featherless cannot drive a seat | Codex on the plan plus Claude Sonnet 5.5 for the two judging seats |
| GLM tester | hijacked the coordinator role, one room message per reasoning token | tester moved to Claude |

## 8. What the human did, and did not

- Posted four dispatches, one per stage (`DISPATCH-*` text is in the room), `@`-mentioning only the
  coordinator. No clarification, approval, hint or rerun followed.
- The stage 3 and stage 4 dispatches contain a block called "requirements that are easy to miss",
  a list of spec points the human asked the coordinator to ledger and test (for example "a preview
  never raises the revision"). It is part of the single human message, but it is human-supplied
  attention and should be counted as such.
- Download of `room.json`, `harness` runs, the independent audit in `operator-audit/`, and these documents were operator work.
  Nothing under `stage-*/` was written or edited by a person.

## 9. Open limitations

- The kickoff `harness/cli.py` and `docs/participant-guide.md` differed from `kickoff-manifest.json`
  before the run began; the integrity check fails and is retained, not skipped.
- The inherited raw suites show 8 superseded checks (the new stage replaced old behaviour);
  each has a passing replacement, and they stay visible in the reports.
- Chunked request bodies return 400. Reset and planning cost grow with state size; supported planning
  limit is 6 tables / 4 pairs / 6 considered bookings.
- Duplicate-block detection covers Python only (0.00%); JavaScript duplication was not measured.
- Tester evidence at stage 3 had 6 visible non-service failures, so it was not a clean suite.

## 10. Independent post-freeze audit

After stage 4 was frozen, the team lead (with Claude Code as operator, outside every stage folder) wrote
`operator-audit/`, a test suite derived fresh from `spec/stage-1.md` to `stage-4.md` and separate from the
tester seat's checks in `verification/`. The seats never saw it and nothing was changed afterwards. It asks what
a grader's hidden checks would ask: status-code and error-code tables, time zones, races, lost browser
responses, upgrades, and a brute-force planner that re-solves the seating problems.

| Run (stage 4 image) | Outcome |
|---|---|
| Whole suite | **506 passed, 0 failed**, 8 skipped, 1 expected failure (chunked request bodies, disclosed in section 9) |
| 3,600 random operations (book, cancel, amend, move, series, amend, replan) | all invariants held after every step: no double occupancy, availability equals the model, history length equals revision, restaurant revision counts as specified |
| Seating plans against the brute-force oracle | identical on 83 random problems, including chained closures |
| Exports from stages 1, 2 and 3 imported into stage 4 | sessions, logins, receipts (replayed byte for byte), cancelled bookings and imported series all work |
| Older images against newer stages' tests | fail as expected, so the suite does tell the stages apart |

Every failure while writing the suite was a mistake in a test, fixed by re-reading the spec; no service result
was excused. Where the spec is silent on 400 versus 422 for a wrongly typed field the suite accepts either.
This audit is not a substitute for the organisers' hidden checks. It cannot prove them, only that the likely
ones were tried.
