# Stage 3 final report

Stage 3 accepted and frozen at source revision 8093f21e49c005e03d770751e0f222a060c224ca. Reviewer acceptance: 07d18b04232d66ddc6330cc7f8c092c1804e64bc, handoffs/reviewer-acceptance-stage-3-8093f21.md. Final repository revision is the coordinator commit containing this report; its full hash is posted in the final room report.

Start: 2026-10-04T16:06:39+08:00. End/freeze verification: 2026-10-04T17:17:42+08:00. Elapsed: 1 hour 11 minutes 3 seconds. Restructuring gate released16:31:03. Coordinator verified committed/working Stage3 diff against8093f21 empty, frozenStage1 against344e085 empty, frozenStage2 against94e7654 empty. No service/check changes by coordinator. Untracked caches and mandates were not staged.

Contributions:
- Core-builder: copy-forward domain baseline; policies, explanations, immutable accepted terms/history, optimistic booking revisions, recurring local-calendar series, atomic moves and validated legacy/native transfer; source445dfb6b369e4d7629cbfee25c29a8d76a344ac5, findings118bff234a10e6548283913b9f0cc3188bfc7a25, integrated evidence58c86c3dc0004004579daba405db4aae22c642cc.
- Interface-builder: copied deploy/transport/browser baseline, Stage3 RUN instructions, date-policy capacity/pair presentation and legacy404 fallback; feature dba9bc475bf247f20266c9290ad298e09ba0daed, corrected8093f21; real same-tab upgrade evidenceb976007d594d2bd63fd6fbc4b1a19e40a97c119a.
- Tester: independent292-line coverage, inherited/new API/browser/transfer/visual/accessibility checks, corrected its own checks without editing frozen/supplied checks; final checks a41b705a2c319a9435e0086d558ae8a20c1d520b; complete evidence0c717ab1bd3113dc662f0e06417220a4113ae7a9,40 screenshots.
- Reviewer: baseline and scoped audits, independent175 API checks,52 corrupted imports,76 browser checks375px/1280px, source-stop upgrades, race/load/container proof; audits2bb3584b7e6fa447e5e64b022a304255842efd2a and1c61626b79979929b51742ad69bf8118e5ba7161, exact acceptance07d18b0.
- Coordinator: full specs/292-line ledger, exclusive ownership, committed complete handoffs, gates/correction routing, timing and frozen-source verification.

Stage reached: claimed stage: 3 on the shipped checks. Exact isolated --repo harness used supplied interpreter from read-only kickoff, no installs. Stage1 120/120,Stage2 25/25,Stage3 7/7,zero skipped/deselected; expected extraStage4 failure. Main report C:/Users/Prince/Documents/darkfactory/band-work/checks/harness-s3-8093f21/report.json; console sibling harness-s3-8093f21.console.txt. Core rerun checks/core-s3-integrated-a41b705/harness/report.json; reviewer own Temp/rv/h6/report.json.

Independent suite NOT clean:466 tests,460pass,6 failures,0errors,0skips, all292lines covered. Five visible superseded inherited assertions: slot shape,Stage1 create shape,Stage2 create shape,cancel equality excluding onlystatus,legacy imported current-view equality. Each Stage3 replacement passes. Remaining manifest mismatch predates run (harness/cli.py and docs/participant-guide.md); untouched-since-start passes. Main evidence checks/tester-s3-8093f21/stage3-checks.log and screenshots/. Core rerun agrees466/460/6/0/0; its isolated screenshots directory is empty because helper used temporary directory, so visual artifact provenance comes from tester/reviewer.

Correction/rejection record:
- R1 F1 interface legacy policy route: routed17:00:22, source fix17:06:27, independent reviewer closure17:11:11 (+08:00 Oct4); routing-to-review closure10m49s. Stage3 UI initially failed legacy backend /policies404. Fix interprets only404 as no published policies; other errors stay visible. Both frozenStage1/2 stopped-source same-tab upgrades now pass. No final core-domain rejection.
- F3 wrong expected series revision after two changes in one batch (3->2); F4 published-policy bounds incorrectly imposed on original fixture fields; F5 success-series setup collided with imported pair (use free anchor, retain atomic rejection); F6 checklist matcher failed checkbox numbering. Tester corrections6916e6f80c39934a4c5e3a87fa626b9cc7273768 at16:58:40. Core observation run bounds16:38:38–16:47:49; findings committed16:56:23; finding-commit-to-fix2m17s. These are observation/commit bounds, not measured effort.
- F2 frozen cancel equality superseded visibly with passing revision/cancel replacement in a41b705 at17:06:58. Tester run16:59:43–17:06:18; core finding16:56:23 toclassification10m35s.
- F9 unset HARNESS_OUT in early run corrected for final harness console; F8 coordinator record pending resolved before finalsuite. No service behavior fabricated to satisfy evidence checks.
- F10 higher mean complexity independently assessed advisory, not rejection; max complexity/file size/MI unchanged. Invalid policy/series/import writes, retries and races remain contract-derived.

Maintainability, same suite aggregation:
| Metric | Frozen Stage2 | Stage3 |
|---|---:|---:|
| Radon mean CC |2.81|3.15|
| Max CC |9|9|
| Minimum MI (all files A)|31.46|31.46|
| Largest Python file (lines)|171|171|
| Lizard Python functions|116|174|
| Python NLOC|799|1298|
| Python average CCN|2.81|3.16|
| Python max function NLOC|25|25|
| Lizard warnings|0|0|
| JavaScript functions|46|51|
| JavaScript NLOC|353|379|
| JavaScript average CCN|2.70|2.67|
| JavaScript max CCN|14|14|

Earlier direct physical-NLOC totals893->1440 use different aggregation; not interchangeable with suite799->1298. Duplicate-block metrics unavailable. Reviewer suggests service.route/private and loading.booking_record simplification in futureStage4.

Observed runtime: healthy0.51s (container0.5s), host RSS5MiB, tester150 mixed requests max0.61s/no5xx,50logins1.71s,60 new-path mixedrequests0.11s. Core rerun max0.68s,logins2.21s. Clean image constrained networknone/2CPU/2GiB passes. Real Stage2 and Stage1 services stopped with port closure before independentStage3 imports; sessions, single/pair refs, original create/batch receipts, pending same-tab retries survive. Stage3 roundtrip preserves policies/series/terms/history/revisions/receipts. 375px/1280px no horizontal scroll or serious/critical axe issues.

Open limitations: historical suite failures stay visible; pre-run manifest mismatch; chunked request bodies400; reset/availability cost scales with state. Host302-user reset10.2–13.83s exceeds10s target, contrasted with earlier constrained-container5.6s; host150-user reset5.3–6.47s. Mean Python complexity increased; duplication unavailable. Untracked caches remain excluded from frozen committed tree. Restaurant-revision correctness deferred toStage4 by organiser; no Stage4 features claimed.

Stage3 complete. Frozen folders are never edited again.

