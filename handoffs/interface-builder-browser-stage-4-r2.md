# Interface builder — Stage 4 R2 browser compatibility result

Repository: `C:/Users/Prince/Documents/darkfactory/band-work/result`  
R2 maintainability routing: `a9b070f6c610a52535b0009b4ce6862605ffaaff`  
Core candidate tested: `8e929cc6112064969df170d443ecf2cdcd90c7f0`  
Tester check commit: `73b776323ed88b325121f94821e1897bfd0e152b`  
Interface compatibility source: `bedf7427d4e724f6981f81316ba3576541228cb9`

No interface code or test files changed for this rerun. The core R2 candidate is an ancestor of the tester checks commit, and `git diff --stat 8e929cc6112064969df170d443ecf2cdcd90c7f0 HEAD -- stage-4` was empty, confirming the Stage 4 service files under test matched that exact candidate.

## Run and result

From `verification/stage4`, using the supplied harness interpreter, with `REPO` and `S4_DIR` set to the Stage 4 checkout:

```text
run_stage4.py --part browser --out C:/Users/Prince/Documents/darkfactory/band-work/checks/r2-8e929cc-interface/browser
```

The committed browser suite ran 6 tests in 17.931 seconds: 6 passed, 0 failures, 0 errors, 0 skips, 0 superseded. The log names five applied-plan checks across desktop and phone sizes, including closed-table refusal and booking at an open table. It also records a pass for `test_L344_L343_L341_browser_survives_real_stage3_to_stage4_upgrade`, the stopped-source Stage 3 to Stage 4 browser upgrade scenario.

Runner output, screenshots and per-process service logs are in `C:/Users/Prince/Documents/darkfactory/band-work/checks/r2-8e929cc-interface/browser`, outside the repository.

This evidence covers interface compatibility for the R2 candidate. Stage 4 acceptance remains open pending full review and the coordinator's decision.
