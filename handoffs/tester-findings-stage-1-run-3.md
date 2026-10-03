# Tester findings, stage 1, R3 regression (reviewer D1: short seeded passwords)

Regression checks committed first at 344e085d8e3d0629dcc17fc95f22a43efe2a85d2 (author tester):
- test_a_basics Auth.test_L021_L035_fixture_short_passwords_log_in_signup_keeps_minimum (reset with "abc", "x", 7-char and 1-char unicode passwords; immediate login; wrong short passwords 401; signup 3 and 7 chars 422, 8 chars 201).
- test_e_transfer Transfer.test_L021_L093_short_password_accounts_survive_export_import (login on independent destination, old token valid, no plaintext in export, second hop back).

Sensitivity: against rejected candidate ad2f1a2 (git archive copy, evidence band-work/checks/tester-r3-old) both fail: reset returns 422 "Password must have eight characters". Against fix 06ad44b both pass.

## Run on tested revision 344e085 (service code last changed at 06ad44b)
- Independent suite: 189 tests, 1 failure, 0 errors, 0 skipped (band-work/checks/tester-run5*).
- Remaining failure: test_L112_kickoff_matches_manifest. Pre-run environment evidence, kept visible: after CRLF normalisation harness/cli.py (one-line .as_posix() change) and docs/participant-guide.md differ from kickoff-manifest.json; both mtimes 2026-10-03, before the first repo commit. test_L112_kickoff_untouched_since_run_started passes.
- Supplied isolated harness, exact command from kickoff cwd, fresh folder band-work/checks/harness-r3 (console harness-r3.console.txt): stage 1 pass, stage 2 fail (expected, recorded separately), `claimed stage: 1 on the shipped checks`. Nothing skipped or deselected.
## Measurements (host)
- start to healthy 0.51 s; RSS 29 MiB after 5x50 write bursts; 50-way bursts no 5xx, max 0.52 s; 50 concurrent logins 1.6 s.
- reset 150 users 4.8 s; 302 users 9.55 s on this host (reviewer measured 5.6 s in container).
- radon: avg CC A (2.64); MI A all files (lowest loading.py 31.28, server.py 31.89). lizard: 747 NLOC, 101 functions, avg CCN 2.6, 0 warnings. Unchanged from R2.
