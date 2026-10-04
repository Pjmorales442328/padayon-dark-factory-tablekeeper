# Interface builder — Stage 4 R1 integrated checkpoint

Repository: `C:/Users/Prince/Documents/darkfactory/band-work/result`  
R1 routing: `6160da85da1ee7d23124f545945f710b0b1d375a`  
Core source exercised: `9911384e39df4e3a554f57dfc76b806a976739db`  
Interface change: `bedf7427d4e724f6981f81316ba3576541228cb9`  
Corrected tester checks: `ea57303952ef9394df6d3c3a2978cbabe0c2357b`

This is interface compatibility evidence, not Stage 4 acceptance. Frozen Stage 1–3 source files were not changed.

## Interface behavior

The interface change preserves `Service.dispatch` and the existing screens. Availability and lookup continue to render authoritative server state, including closure exclusions and repaired `table_ids`. After a successful booking response or same-key replay, the browser fetches the current owner-visible reservation before rendering confirmation, so confirmation reflects an applied seating repair while the original successful POST receipt stays immutable. If the follow-up read fails, the confirmed POST response remains the fallback. No new screens, polling, or retry/session semantics were added.

## Browser evidence

Before the tester corrections, the committed browser suite had 6 tests: 3 passed, 3 failed, with 0 errors or skips. Two lookup failures were caused by reversed table-label expectations: fixture table `t_1` is “Window,” while the test expected “Terrace.” The third used an obsolete series-adoption route and received the correct 404. A process-local in-memory route translation was used only as a diagnostic; it was not a committed test change and is not acceptance evidence. That diagnostic exposed another invalid repair fixture: an occupied `t_3` and a series booking on `t_1` leave no feasible assignment for the overlapping `t_2` booking, so `409 no_feasible_plan` was correct.

After tester commit `ea573039`, the **unmodified committed** command `python verification/stage4/run_stage4.py --part browser --out C:/Users/Prince/Documents/darkfactory/band-work/checks/stage4-interface-r1-ea57303/browser` completed 6 tests in 13.834 seconds: 6 passed, 0 failures, 0 errors, 0 skips, 0 superseded. It covered applied-plan lookup at phone and desktop sizes, closure effects on availability and booking, and a real frozen Stage 3 process stopped with its port closed before independent Stage 4 import. The same tab retained its session, booking form, pending body/key, and recovery behavior through lookup and replay. Logs and service logs: `C:/Users/Prince/Documents/darkfactory/band-work/checks/stage4-interface-r1-ea57303/browser`.

Earlier supporting browser checks against the same core candidate:

- Stage 3 browser runner with `S3_DIR=stage-4`: 5/5 passed, no failures/errors/skips/superseded. Logs: `C:/Users/Prince/Documents/darkfactory/band-work/checks/stage4-interface-integrated-9911384/stage3-browser`.
- Inherited Stage 2 suite: 135 run, 0 actual failures, 2 visible superseded assertions, 0 errors/skips. Playwright axe audits ran; 375px and 1280px screenshots are in `C:/Users/Prince/Documents/darkfactory/band-work/checks/stage4-interface-integrated-9911384/stage2-visual/screenshots`.

## Packaging evidence

`docker build --no-cache -t tablekeeper:stage-4-iface-9911384 .\stage-4` passed. The image ran with `--network none --cpus=2 --memory=2g -e PORT=18084`; `/health`, `/`, `/signup`, `/login`, `/lookup`, `/static/app.js`, and `/static/site.css` returned 200 with expected content types. Build log: `C:/Users/Prince/Documents/darkfactory/band-work/checks/stage4-interface-integrated-9911384/docker-build.log`.

Stage 4 acceptance remains open pending the complete independent 351-line suite, exact isolated harness, reviewer findings and coordinator review.
