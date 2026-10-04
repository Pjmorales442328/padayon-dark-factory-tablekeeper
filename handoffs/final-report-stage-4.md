# Stage 4 final report

ACCEPTED and frozen source: 8e929cc6112064969df170d443ecf2cdcd90c7f0. Reviewer decision c4edac4efc4be78891ea6a83b4b7e734eb6e4362, handoffs/reviewer-findings-stage-4-r2-8e929cc.md. Final repository revision is the coordinator commit containing this report, posted in the room.

Start2026-10-04T17:55:59+08:00; end/freeze2026-10-04T19:30:07+08:00; elapsed1h34m08s. Baselinegate18:12:24. Coordinator verified working/committed stage-4 equals8e929cc and stages1/2/3 equal344e085/94e7654/8093f21. Frozenfolders neveredited. Only coordinator-owned documentation staged; untracked caches, mandates and unfinished core report excluded.

Contributions:
- Core-builder: copied domain baseline88686a81 and behavior-preserving import separation; policies remain inherited, added closure occupancy, optimal seating preview/apply, once-per-request restaurant revisions, reassigned history, original-date recurring amendments, serializable operations and validated native/legacy transfer; initialfeatures1e37df2, helper/budgetsplitb6c47cd, bounded independent-salt two-worker reset hashing9911384; meaningful M1 refactorsd144199 and8e929cc (state revision responsibilities and shared conflicts/table-set rules).
- Interface-builder: copied offline deployment/browser baseline8e4e161, Stage4RUN commands; bedf742 current server GET reservation view after confirmed successful create/replay, fallback to successful receipt on read failure; preserves retry/session/uncertainty behavior and reflects repairs. Integrated evidencea6a6d71; exactfinalbrowser/source-stop evidenceb01852eb7921e85a4d5e8a0f6255ea1edd01b7e8,6/6.
- Tester: contract-derived351-line coverage/759checks, independent small exhaustive planningoracle, inherited/API/browser/legacy/native/corrupt-state/series/races proof; initialchecks321a666, corrected ea57303952ef9394df6d3c3a2978cbabe0c2357b, finalchecks fbe5efcd87db9ae2ef4c87a459c6d3b1f64d157c. Report73b776323ed88b325121f94821e1897bfd0e152b, handoffs/tester-report-stage-4-r2.md and tester-findings-stage-4.md.
- Reviewer: exactbaselinegatea398254; R1behavior/oracle/state/browser audit0638b7dc with unwaived M1; finalc4edac4 remeasuredandclosedM1 aftersourceinspection, no metricpadding/check-specificlogic. Independently297APIprobes,1051optimizerpreviews (779feasible/272infeasible,0mismatches),157badimports and9historymutations,482requests50workers0five-hundreds/max0.60s/nooverlaps,76browserchecks375/1280/axe and17/17same-tabupgrade.
- Coordinator: complete4specs/351ledger,exclusiveownership,allfullcommittedhandoffs,baselinegate,findingsrouting/timing,acceptedsourcefreeze andfinalreport. No service/check edits.

Stage reached: claimed stage: 4. Exact supplied isolated --repo harness from read-only kickoff passesStage1 120/120,Stage2 25/25,Stage3 7/7,Stage4 6/6 (158total),zero skipped/deselected. Main tester evidence C:/Users/Prince/Documents/darkfactory/band-work/checks/r2-8e929cc/; reviewer report C:/Users/Prince/Documents/darkfactory/band-work/checks/reviewer-s4-8e929cc/report.json; core earlier committed9911384 report checks/core-s4-9911384-harness/report.json. Stage5 absent, no extra-next-stage assertion possible.

Independent final parts (not a clean raw inherited suite): API97 nofail/error/skip,browser6/6,inherited1 178 with3visible superseded,inherited2 135 with2visible superseded,inherited3 153 with1realmanifestfailure+3visible superseded. Total569executed across theseparts,8superseded and1environmentnonpass; everyreplacementpasses, no suppliedskip/deselection/edit. One superseded inherited history selector throws KeyError revision due to newrestaurant_events; this remains visible rather than hidden. Reviewer initially raisedT1asomitted, then WITHDREW it in room messageb5769502-b519-47f6-aecd-85ed1afd30ce aftertester showedentry8SUPERSEDED andpassing adapter. Decision unchanged; no newsource/checkchange required.

Rejections/corrections:
- R1initialcheckpoint53acf09 at18:46:57 disclosed560run511pass33fail16errors0skips, initialuncommittedfeatures; neverdescribedclean. FindingsF1–F17 routed6160da85 at18:48:04. Testerresolved itscheck/setup defects ine a57303 at18:56:48 (routing->initialfix8m44s). FinalF18–F23 correctedfbe5efc at19:11:02; completeevidence73b77619:22:06; independentreviewclosurec4edac4 at19:29:03. R1routing-to-finalreviewclosure40m59s.
- F1oldRUN/claimshape assertions retainedvisibly/replaced; F2manifestenvironment unchanged; F3historyselector adapted; F4resetstaletokens/F5read-onlytokenproperty corrected; F6keypathscope; F7owncapacity/objective arithmetic/F9allconsideredseriesoracle; F8outsidehours; F10timearithmetic/F11validadoptionbeforecutoff; F12overlappingfixtures; F13skipsexceptions; F14legacymanager/privateendpoint assumptions; F15labels/F16POSTseries andfeasiblerepair; F17actualfrozenmetricpath.
- F18–F23 additionaltesterdefects: unchangedconsideredassignment included; no-feasiblepairfixture fixed; oraclepriorclosures; permanentbatchexceptions; feasible pendingplan fixture; repairinterval narrowed tostaywithinplanninglimits. Contractexpectations retained.
- D1coreZexplicit-zero-offsetparse andD2strongerstate/receipt/history validation fixedbefore1e37df2; D3maxcomplexityfunctionsplitbeforeb6c47cd. Laterreset302userlatency addressed9911384. Actualper-failureobservation timestamps unavailable; initialfullrun461.437s finishedbefore18:34, checkpointassembly18:39–18:44. Thesebounds not effortmeasurements.
- R2M1 reviewermaintainabilityrejection0638b7dc: meanCC/minMI/maxfunction worse, NOTwaived. Routinga9b070f6 at19:00:13; refactorsd14419919:08:11 and8e929cc19:09:43; independentlyclosedc4edac4 at19:29:03. Routing-to-reviewclosure28m50s. Extracted meaningfulsnapshot/revisionresponsibilities/sharedconflict/table-setrules, no artificialpadding.

Maintainability same tools vs frozenStage3:
|Metric|Stage3|Stage4|
|---|---:|---:|
|Radon meanCC|3.146|3.116|
|MinimumMI (allA)|31.458|31.458|
|MaximumCC|9|9|
|LargestPythonfile(lines)|171|171|
|LizardmeanCCN|3.155|3.122|
|MaxfunctionNLOC|25|25|
|Warnings|0|0|
Reviewer duplication: supplied interpreter's lizard over frozen Stage3 (8093f21) and accepted Stage4 (8e929cc) tablekeeper Python files with -l python -Eduplicate reported0.00%both. This detector finds exact token-sequence repeats only; near-duplicates are not measured. JavaScript duplication was not measured. Earlierreports toolunavailable remainhistorical; reviewer suppliedobservedtoolmethod. FinalJS remainsinterface-owned, revieweravgCCN2.7/0warnings; initialStage4JS390NLOC/52functions reported. AllM1figures correctedatorbetterbaseline.

Evidence: offlinecleanarchive2CPU2GiBcontainerhealthy~3s; allassetsbundled/PORTcorrect. Testertiminghealthy0.51s,150requests50waymax0.79s,50logins2.09s,302-userreset6.79s (earlier10.13s beforeboundedhashing). Actual frozenStage3 stoppedandportclosedbefore independentStage4import; oldcreate/move/seriesreceipts exact,history/session/reference retained,legacyrestaurantrevision0. Same-tabpendingkey/bodyrecoveryworks. Legacy1/2/nativeunapplied/appliedplan/closures/seriesreceiptsroundtrip validated. Screens375px/1280px axe/nooverflow,appliedplan/currentview/recovery pass.

Openlimitations: pre-run kickoffmanifest mismatch harness/cli.py/docs/participant-guide.md remainsvisible; rawinheritedsuite has supersededfailure/erroroutputs; chunkedrequestbodies400; state-size-dependentreset/availability/planningcost, explicitplanninglimit supported6tables/4pairs/6considered; empiricaltimingsnotarbitrary-statebounds. NoStage5 exists. Untrackedcachesandunfinishedownersevidenceexcludedfromfrozencommittedsource. AllStage4requiredrevision/closure/series semanticsaccepted; no humanquestions/approval or sourcechangesafterfreeze.
