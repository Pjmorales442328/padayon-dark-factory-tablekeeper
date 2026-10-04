# Stage4 baseline review handoff
Repository C:/Users/Prince/Documents/darkfactory/band-work/result.
Reviewer: review exact core restructuring88686a81f626aec2e8b28cd01266a5acec7b1b20, committed evidence6b2a3721debb5a4fcb6df67326b2fd4006302a0f at handoffs/core-builder-baseline-stage-4.md. Interface copied-source commit8e4e161166d4cae499a587acd723d50d8b39a0a2 is present, but a separate committed baseline evidence report has not yet been located; review core now, hold interface decision until its evidence arrives. No interface report is claimed here. Verify scoped behavior-preserving changes, inherited behavior and frozenStages1–3 before baselineacceptance; noStage4featureacceptance from absentfeatures. Coreimportboundaries movedtop-level only; report explicitly3baselineevidencefailures and absentStage4features rather than cleanfullsuite. Confirm no genuine regression/complexityincrease from restructure. Complete351ledger/fullfourcontracts below. Return separate exact baseline decisions and committedfindings. Coordinatorfeaturegate remainsclosed untilbothscopedacceptances.

# Stage4 initial dispatch and restructuring gate
Repository C:/Users/Prince/Documents/darkfactory/band-work/result.
Requirements handoffs/requirements-stage-1.md,requirements-stage-2.md,requirements-stage-3.md,requirements-stage-4.md;ledger handoffs/ledger-stage-4.md (351lines).
Core/interface: onlycopiedexclusiveStage4baseline/restructure beforefeaturegate. Readfullcontracts,writeallnumberednotesbeforeedits/checks,commitowncopiedfiles/notes/evidence. Frozenfoldersunchanged.
Tester: independentlydesign 351linechecksfromcontractonly, notimplementation; commitnotes/checks beforecandidateexecution. Newverification/stage4 only;run inherited1–3visiblesupersededassertions withpassingreplacementswhereStage4changes;never suppliedskip/deselect. DesignactualStage3stop+closedport beforeindependentStage4import,same-tabupgrade,legacyStage1/2imports,nativeplans/closures/series/replayroundtrip,independentoptimalplanningoracle,revisions/races/atomicloading. Fullruns await exactfeaturecandidate,notbaselinegate.
Reviewer: contract/ledgeravailable;reviewbuilderscommittedbaselineuponcoordinatorhandoff;noStage4acceptancefrombaseline. Fullcandidate mustcoveralllines,optimalplanning/revisions/repairhistory/seriesdates/statevalidation,constrainedDocker/browser375/1280/axe andsource-stopupgrade.
Exactharness suppliedpython -m harness run --track tablekeeper --repo C:/Users/Prince/Documents/darkfactory/band-work/result --stage 4 --mode isolated --out C:/Users/Prince/Documents/darkfactory/band-work/checks/<fresh>;kickoffcwd,claimstage4mandatory.
Stage4start2026-10-04T17:55:59+08:00. Bindingorganiser:restaurantrevision correctness requiredFROMStage4. Noquestionshuman/approval;resolvechoicescontract/evidence,reporttrueblocker.

# Stage4 ownership and contract
Repo C:/Users/Prince/Documents/darkfactory/band-work/result. FrozenStage3 source8093f21e49c005e03d770751e0f222a060c224ca; Stage2 94e7654c4427fa3c087279675edbe1cda4f5a4fc;Stage1 344e085d8e3d0629dcc17fc95f22a43efe2a85d2.
Core-builder exclusivelyowns stage-4/tablekeeper/*.py EXCEPTserver.py/web.py, includingnewplanning/closure/seriesamend/revision/loading modules.
Interface-builder exclusivelyowns stage-4/tablekeeper/server.py,web.py,static/**,templates/**,Dockerfile,RUN.md,requirements.txt,.dockerignore.
Tester exclusivelyowns verification/stage4/** andhandoffs/tester-*-stage-4*.md;no frozen/suppliedcheckedits.
Reviewer owns handoffs/reviewer-*-stage-4*.md;builders respectivehandoffs/<seat>-*-stage-4*.md;coordinatorotherhandoffrecords.
Service.dispatch contract remains unchanged;corealoneAPI/domain/state;interfaceHTML/static/browser/packaging. Availability authoritative;newrepairhistory/series fieldsandlegacyreceiptshapes toleratedbyUI. Nonewscreensrequired, avoidadditionalproductscope.
Beforefeatures eachbuildernotes allledgerlines,commitscopiedownedfiles andSHORTbehavior-preservingrestructure orjustifiedno-op,thenreportexactrevision/baseline/inheritedbehavior/metrics. Coreconsider service.route/private/loading boundaries reviewer suggested;no newfeatures beforegate. Interface mayjustifyalreadyseparateUI/transportandupdateStage4RUNonly.
Eachfileoneowner;stageexplicitownedpaths;exactseatauthor/localemailpercommit,no sharedgitsettings/amend/rebase/squash. Never rootREADME/FACTORY. No caches/nestedgit. Use suppliedinterpreter,noinstalls.

# Current-stage override
Stage4 only,stage-4 copiedfromfrozenstage-3; inherited lines mentioning currentstage3/delivery/harness/timing now targetStage4. Frozenstages1/2/3 neveredited. Newlinesoverride earlierconflicting behavior; restaurantrevision correctness nowmandatory. All original292behaviorlinesremain covered whereunchanged.

# Stage 4 requirement ledger

Every numbered line requires an independent check. Lines1–197 inherit stages1/2 with stage3 changes below. Complete specs requirements-stage-1.md,requirements-stage-2.md,requirements-stage-3.md. Stage3 controls changed behavior. Python required.

1. Implement stage3 only, with inherited stages1/2 API/browser and policies/history/recurrence additions; no existing-product source/docs/schemas.
2. Complete buildable stage-3 copied from frozenstage-2 contains Dockerfile,RUN.md,every asset;no nested.git/generatedcache committed.
3. Python implementation builds from clean checkout and starts with documented command without manual setup.
4. Listen on 0.0.0.0, PORT environment variable, default 8080.
5. Runtime has no outbound network and requires no external service or Compose.
6. Operate within 2 CPUs and 2 GiB.
7. Health becomes 200 {status:ok} within 60 seconds when store is usable.
8. Support 50 in-flight requests without 5xx.
9. Requests finish within 5 seconds; reset and test control calls within 10 seconds.
10. State may be ephemeral across container restart.
11. JSON responses use application/json; charset=utf-8; timestamps are RFC3339 with explicit offset.
12. Unknown body fields and query parameters are ignored.
13. Every identifier is an opaque string at most 64 characters, including fixture IDs.
14. Reset is unauthenticated, enabled, returns 204 and atomically replaces all state.
15. Repeated reset removes prior accounts, sessions, reservations, receipts and imported state.
16. Restaurant and table configuration comes only from reset; no creation APIs required.
17. Restaurant timezone is valid IANA zone; slot and duration minutes are positive integers; cutoff is nonnegative integer.
18. Opening weekdays are mon through sun; missing weekday is closed.
19. Opening times are valid HH:MM with closes later on same day; no overnight opening.
20. Table capacities are positive integers; booleans never count as integers.
21. Seed users log in immediately with supplied password.
22. Seed reservations accept table_id or table_ids and default confirmed unless explicit cancelled; preserve validation and supplied identities.
23. Past booking dates alone never cause rejection; cutoff still applies.
24. Every error uses {error:{code,message}} with specified status/code and human readable message.
25. Unparseable JSON, empty request body, non-object request body and ordinary wrong body field types give 400 malformed_request.
26. Numeric starts_at_local gives 400 malformed_request.
27. Missing required fields and valid-type invalid formats/ranges give 422 validation_failed unless specific code applies.
28. Invalid party_size including string, boolean, fraction, zero and negative gives 422 validation_failed.
29. starts_at_local strings must be bare YYYY-MM-DDTHH:MM; offsets, Z, seconds and invalid dates give 422 validation_failed.
30. Integer query parameters accept plain decimal digits only; 1e9, 4.0 and +4 give 422 validation_failed.
31. Required absent/empty idempotency header gives 400 missing_idempotency_key; length over 255 gives 422 validation_failed.
32. No request produces a 5xx, including malformed input and concurrent load.
33. Signup returns 201 user_id, display_name and token.
34. Signup duplicate email gives 409 email_taken.
35. Signup password under eight characters and email outside local@domain give 422 validation_failed; fixture passwords are strings without signup minimum.
36. Login returns 200 user_id, display_name, token; wrong password/unknown email gives 401 unauthenticated.
37. Passwords stored only as password-function hashes, never plaintext.
38. Missing/malformed/unknown bearer token gives 401 unauthenticated except booking visibility exception below.
39. Tokens never expire and multiple tokens/concurrent sessions remain valid.
40. Health, reset, signup, login, restaurant list/detail, availability, export and import are public.
41. Other endpoints require bearer authentication; permitted-resource restrictions use specified 403/404 codes.
42. Another guest and anonymous caller receive 404 not_found for someone else's booking; do not expose existence.
43. Idempotency applies to reservations,reservation-moves,restaurant policy publication and series creation.
44. Receipt identity scopes user, method, path and key; different users do not interfere.
45. Same key/body on another path is independent and succeeds normally.
46. Resolve receipts after JSON-object parsing and authentication, before field/current-resource validation.
47. Used key with different JSON body gives 409 idempotency_key_reuse even if new body invalid.
48. First successful request returns 201; replay returns 200 identical original JSON response.
49. JSON body comparison ignores whitespace and key order and preserves JSON value types.
50. Failed 4xx requests do not consume keys; reuse is first use.
51. Concurrent identical unused-key writes return exactly one 201 and others 200 identical bodies with one operation.
52. Replay after amendment/cancellation returns original response without state changes.
53. Restaurant list returns restaurants with id,name,timezone in fixture order.
54. Restaurant detail returns full fixture-shaped configuration; unknown gives 404 not_found.
55. Availability requires restaurant_id,date,party_size; missing gives 422 validation_failed.
56. Availability date is valid local calendar date and party_size is positive integer query.
57. Availability response includes restaurant_id,date,timezone and slots.
58. Slots step from opening by slot_minutes and fit absolute duration within closing; include single-table availability and available_options.
59. Each slot has starts_at_local, offset starts_at, available_table_ids in fixture order.
60. Available tables have capacity >= party_size and no overlapping confirmed reservation.
61. Fully occupied slots still appear with empty table list; closed day returns empty slots.
62. Create supports table_id/table_ids and returns stage2shape plus revision1 and entire selected accepted_terms snapshot; old receipt replays stay original.
63. Unknown restaurant/table or table outside restaurant gives 404 not_found.
64. Occupancy uses restaurant plus table ID; table IDs may repeat in different restaurants.
65. Confirmed occupancy is half-open absolute [start,start+duration); adjacent bookings do not overlap.
66. Overlap gives 409 table_unavailable; two racing same-table/time requests have exactly one winner.
67. Off-grid start gives 422 not_on_slot_grid measured from opening.
68. Outside opening or ending after closing gives 422 outside_opening_hours.
69. Party exceeding sum of selected tables' capacities gives 422 party_exceeds_capacity.
70. Nonexistent local time gives 422 invalid_local_time.
71. Reference is globally unique, 6..12 A-Z0-9 characters, immutable across changes.
72. Reservation ID is globally unique, immutable across changes; owner,restaurant and created_at preserved.
73. Reservation list includes only caller's confirmed/cancelled bookings, starts_at descending, exact create shapes; empty list supported.
74. Reference lookup returns own booking or 404 for absent/invisible booking.
75. First cancel returns200 cancelledstate, increments booking revision once, adds one cancelled history entry with emptychanges, frees all occupancy.
76. Repeat cancel returns same currentstate200 and changes no booking/series/history counters,even aftercutoff.
77. Cancel at/within accepted_terms cutoff or after currentstart409 cutoff_passed.
78. PATCH accepts table_id or table_ids,starts_at_local,party_size; omitted fields retained; both table selectors invalid; no key required.
79. PATCH checks optional expected_revision stale/type/range first,then current old acceptedcutoff and confirmedstatus,then full resultingfields under resultingdate policy.
80. Successful PATCH releases/reserves together; failure preserves booking/occupancy.
81. No-op amendment including reversedpair returns200 retaining terms,end,booking+series revisions and history;still confirmed/editable required.
82. Spring-gap times absent in availability and rejected on create/amend.
83. Fall-fold times resolve first occurrence only, appear once, second occurrence not bookable.
84. Duration arithmetic is absolute time; ends_at follows resulting local offset, including fold example.
85. Berlin 2026-03-29 and 2026-10-25 transitions handled with IANA offsets.
86. New York 2026-03-08 and 2026-11-01 transitions handled with IANA offsets.
87. Export returns200 tracktablekeeper,format_version1,stateobject;preserves new policies/terms/history/revisions/series and original receipts.
88. Export is atomic read-only detached snapshot unaffected by later source writes.
89. Import accepts unchanged service export across independent process/port/files/network; returns 204 atomically.
90. Import replaces rather than merges and repeated import does not duplicate data.
91. Invalid JSON import uses malformed_request; missing fields, wrong track/version or invalid state give 422 validation_failed without any changes.
92. Another track export gives 422 validation_failed and preserves destination state.
93. Import preserves accounts/password hashes, token validity, configuration, reservation identities/statuses/timestamps/references.
94. Import preserves completed request bodies and original responses for create and moves; failed keys stay reusable.
95. Import deletes all previous destination accounts/tokens/data; reset clears imported state.
96. Reset fixtures and imported state validate all types, IDs, relations and booking rules, including confirmed overlaps.
97. User IDs scope globally; emails uniquely identify accounts; loading validates unique IDs/emails and account field types.
98. Restaurant IDs scope globally; loading validates uniqueness, timezone, policy and hours types/ranges.
99. Table IDs scope within restaurant only; loading validates uniqueness within restaurant and capacity types/ranges.
100. Reservations refer to existing user,restaurant and restaurant-local table; loading validates IDs/references uniqueness and temporal consistency.
101. Tokens scope globally, map to existing user; loading validates token types/uniqueness/ownership and preserves multiple sessions.
102. Receipts scope user/method/path/key, refer to existing user and valid immutable response snapshots; loading validates bodies/responses and key constraints without requiring equality to subsequently changed bookings.
103. Batch moves requires auth/key; moves is 1..8 objects with distinct string references; invalid shape/duplicates give 422 validation_failed.
104. Every batch booking belongs to caller and same restaurant; unknown/other owner gives 404; different restaurants gives 422 validation_failed.
105. Batch accepts PATCHfields/table_ids/expected_revision;preserves identity/owner/createdtime;changeditems adopt resultingpolicy and increment bookingrevision/history once.
106. Cancelled batch booking gives 409 reservation_cancelled; existing cutoff applies per booking.
107. Batch non-occupancy errors precede any occupancy conflict, in input order; cutoff precedes other changes for that booking.
108. Resulting bookings overlapping each other or unlisted confirmed bookings give 409 table_unavailable; unchanged items retain occupancy.
109. Batch commits all records/occupancy/receipt together or none; swaps supported.
110. Successbatch201 ininputorder includes unchangeditems;no-op retains every value/revision/history;affected series increment once each for batch.
111. Batch replay gives 200 original response after changes/cancellation; exported/imported receipts preserve behavior.
112. Kickoff package, supplied tests and harness remain unmodified; install nothing into harness interpreter.
113. Independent checks cover every ledger line and full supplied harness without skips or deselection.
114. Exact --repo stage3 isolated harness prints claimed stage: 3; expectedextra stage4 failure recorded separately.
115. Each seat commits explicit owned files with exact seat author and local non-personal email without shared git setting changes or history rewriting.
116. Coordinator never edits servicecode/checks/rootREADME/FACTORY;recordstage/rejectiontimes/metrics;frozenstage1+stage2 unchanged.


## Stage 2 additions and transfer invariants

117. Beforefeatures,each builder commits SHORT behavior-preserving restructuring on copiedownedstage3 files;stage1 unchanged344e085 andstage2 unchanged94e7654.
118. Browser routes /, /signup, /login, /lookup return HTML, reachable directly by URL; API remains JSON and all other required screens reachable through UI.
119. Browser supports searching, booking and managing reservations, including approved two-table combinations.
120. If search A starts before B but completes later, grid, table labels and booking form remain B; stale responses never restore A.
121. If another client takes selection after form opens, 409 table_unavailable shows booking-error, refreshes availability, preserves selected form/inputs and shows no confirmation for attempt.
122. Lost booking response before/after commit shows nonempty booking-uncertain, no booking-error or new confirmation, retaining unchanged form.
123. Unchanged uncertain booking retry sends same body and key; success clears uncertainty/error and displays original reference; confirmed rejection uses booking-error.
124. Out-of-order and uncertain-result rules apply to combined bookings too; server remains authoritative and browser never invents cached success.
125. No background polling/live updates/cross-tab sync/reload recovery is required.
126. Presentation-ready coherent restaurant product uses warm hospitality character with clear search/availability/booking hierarchy.
127. Dates, times, party size and seating choices are scannable; combined tables read as intentional seating choices with human labels.
128. Consistent typography, spacing, colors, controls and feedback; primary actions obvious.
129. Available,unavailable,selected,loading,success,refusal and uncertainty states visually distinct.
130. Human-readable restaurant/table labels prominent; technical identifiers shown only when useful.
131. 375 CSS-pixel mobile and conventional desktop layouts remain usable without horizontal page scroll.
132. Visible input labels, apparent keyboard focus and sufficient text/control contrast throughout.
133. Considered empty/loading/error states and consistent navigation across required routes; no custom asset required.
134. Signup inputs expose signup-email,signup-password,signup-display-name and signup-submit button.
135. Login inputs/button expose login-email,login-password,login-submit.
136. auth-error exists only when auth error present; current-user appears every signed-in screen and contains display name; logout-button provided.
137. Logout removes active browser auth and all routes reflect signed-out state; account/token server rules remain inherited.
138. restaurant-select option values are restaurant IDs; date-input YYYY-MM-DD; party-size-input number; search-button runs search.
139. availability-grid holds results; no-slots is shown instead of grid when day has no slots.
140. Single cells have slot-{table_id}-{HH:MM} testids and data-available=true exactly when table_id in searched slot available_table_ids; false otherwise.
141. Click available single cell opens correct table/time booking form; unavailable click does nothing.
142. Signed-out available-cell click produces auth-error or navigates /login; authenticated booking requires server auth.
143. booking-form, booking-summary, booking-party-size and booking-submit testids present; summary includes all selected table labels/local start.
144. booking-party-size numeric input prefilled with searched party size; booking-error present only on confirmed refusal.
145. Keep form after successful booking; unchanged submit repeats original reference with no error/second booking.
146. Changing a field creates a new booking request/retry identity; unchanged requests reuse same body/key.
147. confirmation and confirmation-reference appear after successful server booking; reference text exactly reference only.
148. confirmation-details includes restaurant name,table label(s),local start; confirmation-tables includes every reservation table label.
149. Lookup has lookup-reference-input,lookup-submit; found reservation-detail and reservation-status exactly confirmed/cancelled.
150. reservation-cancel-button cancels and is absent after cancellation; reservation-error shown for not found/cancel refused.
151. reservation-tables on lookup names every selected table; single confirmation/lookup behavior unchanged.
152. Stage3 accepts own stage1 andstage2exports,source stopped before import;no process/files/port/networkdependency.
153. Pre-upgrade signed-in browser remains signed in after between-request import, without reload/new screen.
154. Retained pre-upgrade booking reference works in lookup after import.
155. Response-lost pre-upgrade booking retries after import with same body/key and original confirmation; form and pending retry identity survive.
156. Restaurant combinable field is ordered list of unordered pairs of that restaurant's table IDs; pair member order preserved for option output/testids.
157. Only declared pairs bookable; never triples; combination relation nontransitive.
158. Combination capacity equals sum of two distinct member capacities.
159. Confirmed combination occupies each member for entire half-open absolute duration, scoped restaurant+table.
160. Seed reservations may use table_id or table_ids and status cancelled; confirmed default; cancelled seeds occupy no tables.
161. Availability available_table_ids remains singles-only behavior; slots gain available_options.
162. available_options lists all eligible free singles first in fixture order, then eligible free pairs in combinable order.
163. Pair option table_ids keeps combinable order; capacity sum; every member must be free and capacity>=party size.
164. Combination overlapping any occupied member omitted from available_options even if other member free; cross-restaurant identical table IDs independent.
165. Create legacy table_id means singleton; table_ids supports singleton or declared pair; sending both gives422 validation_failed.
166. Reservation responses always contain table_ids; table_id present exactly for singleton and absent for pair.
167. Unlisted pair or more than two tables gives422 combination_not_allowed.
168. Duplicate selected table ID gives422 validation_failed; empty selection invalid with422 validation_failed; wrong JSON types follow inherited precedence unless overridden.
169. Unknown member or restaurant-local mismatch gives inherited404 not_found; IDs remain string max64.
170. Any member occupancy overlap gives409 table_unavailable; party above summed capacity gives422 party_exceeds_capacity.
171. PATCH accepts table_ids same rules, atomically releases old members/reserves new members; failure changes none.
172. Cancellation frees all members immediately; repeated cancellation identical state200.
173. No-op pair order reversal returns200 without changing identities,timestamps,table selection values or occupancy.
174. Combination UI cells use slot-{t_a}+{t_b}-{HH:MM} in combinable order and data-available consistent with eligible option.
175. Combination cells shown when declared pair available for searched party size; all names use table labels.
176. Single cell testids, confirmations and lookup remain compatible with stage1 singles.
177. Atomic moves accept table_ids per item with inherited validation/cutoff/order/retry behavior; resulting booking sets cannot overlap any member.
178. Batch swap between singles/pairs commits all or nothing; non-occupancy errors precede occupancy; unchanged pair permutations no-op.
179. Combination receipt retries preserve original response after amendment/cancel and export/import; body comparison remains JSON-value based.
180. Concurrent bookings/amendments/moves/read/reset/export/import are serializable: every read sees consistent before/after state, never partial occupancy.
181. Race for any shared member table/time gives exactly one winner; disjoint member sets may both succeed.
182. Reset validates combinable shape, distinct member strings, known local tables and duplicate unordered declarations; invalid fixture replacement changes nothing.
183. Import validates stage2 combination config/selection/relations/status/type/overlap as create; another track/invalid state422 atomically without5xx.
184. Stage1 imported configs without combinable behave as no pairs; imported singleton bookings gain stage2 table_ids while preserving legacy table_id.
185. Stage1 successful receipt snapshots retain original JSON responses exactly, even if missing stage2 table_ids; retries remain valid without regenerated identities.
186. Loading/transferring user IDs/emails,tokens,restaurant IDs/table-local IDs,reservation IDs/global references and receipt scope retain inherited invariants.
187. Pair declaration identifier is unordered restaurant-local member set, not globally scoped table IDs; stored order remains presentation order.
188. Confirmed occupancy invariant applies to every member across all reservations; cancelled bookings/receipts cannot create occupancy.
189. Import/reset validates reservation owner/configuration/member relationships, unique references/IDs, temporal consistency and receipt-token ownership; validates legacy and new versions before replacement.
190. Browser session storage contains token/display identity and pending request key/body; successful stage1 token import remains valid; browser state never substitutes for server response.
191. Use supplied interpreter/playwright Chromium/axe tools for browser checks; install nothing into harness interpreter.
192. Independent browser checks exercise late searches,409 refresh preserving form,lost responses before/after commit,same-key retry,changed form key,combination equivalents and between-request upgrade.
193. Independent checks cover responsive375px/desktop,no horizontal scroll,labels/focus/contrast,distinct states and complete required flows; retain screenshots outside frozen source as reviewable evidence.
194. Stop actual frozenstage2 source before independentstage3 importproof;verifyaccounts,tokens,single/pairbookings/references/create+batchreceipts,browser pending recovery.
195. Run inheritedstage1/2 behavioral suites againststage3,newstage3 APIchecks and inheritedbrowser,fullisolatedharness withoutsuppliedskips/deselection/editing.
196. Measuremaintainability vsfrozenstage2 baseline(rad on/lizard/JS/limits);recordduplicationlimitations.
197. Finalstage3report includesaccepted/finalrevision,eachseatcontributions,harnessclaim/report,allrejections/changes,times/metrics/limitations.


## Stage3 additions and cross-record invariants

198. Availability capacity and no_overlap rules are independent; available iff both true; available_table_ids retains meaning and stage2 available_options remains inherited.
199. explain query optional; accepts only literal true; false,1,empty,True or other values422 validation_failed.
200. Without explain,no explanationfields in slots; inherited single/pair slotshape remains except policy-determinedvalues.
201. With explain,every slot has full table explanation exactlyonce per restauranttable infixtureorder.
202. Each table explanation contains table_id,policy_version,available and rules capacity then no_overlap in fixedorder.
203. Both rules always reported independently including bothfalse; availabletrue IDs exactlymatch available_table_ids in sameorder.
204. Closed day slots[]; fully unavailable slots remain with complete explanations for everytable.
205. Availability/publishedpolicy decisions use selecteddate policygrid,duration,hours,capacities not originalrestaurantdetail.
206. GET /reservations/{reference}/history owneronly;unknown,anotherguest,anonymous404;cancelledhistory still readable.
207. History entries oldestfirst in seqorder and atorder;seq starts1 increments exactly1 even same-secondwrites.
208. History created names tables,starttime,partysize fromnull in fixedorder.
209. Single creation/table single-to-singlechanges use table_id historyfield;paircreation uses table_ids fromnull todeclaredorderpair.
210. Anychange involving pair uses complete table_ids before/after,declaredcombinationorder;tablesfield precedes starts_at_local then party_size.
211. Changedhistory includes ONLY fieldsactuallychanged;one changedentry per realamendment;no-op nohistory.
212. Cancelledhistory event has changes[];nothing follows cancellation.
213. Idempotentreplay create/batch/series/policy adds nohistory/revisions/termschanges.
214. Every historyentry carries resultingbookingrevision and COMPLETE accepted_terms fromthat event;oldentries never acquirelaterterms.
215. No new screens required for history/explain/policy/series;existingstage2 browsergrid follows sameauthoritative rules.
216. Restaurantfixture manager_user_ids defaults[];onlylistedusers publishpolicy;managerrole neverpermits otherdinerprivatebooking/history/decision/series.
217. Policy publication POST /restaurants/{id}/policies requiresauth andkey;unknownrestaurant404,authenticatednonmanager403,no token401.
218. Policy publication completebody required effective_from,slot_minutes,reservation_duration_minutes,cancellation_cutoff_minutes,opening_hours,capacities;not patch.
219. Policy effective_from validactualYYYY-MM-DD;grid,duration integers1..1440;cutoffinteger0..10080;boolneverinteger.
220. Policy openinghours validstage1format,no duplicateweekday.
221. Policy capacities names EXACT restaurant-localtableIDs with integer1..100;missing/extra/unknownkeyinvalid.
222. Every invalidpolicy422 validation_failed,no versionallocation or any statechange;unknownfieldsignored.
223. Policy cannot altertableIDs/labels/timezone/declaredcombinations;unknown unrelatedfieldsignored.
224. Successfulpublication201 suppliedrecognizedpolicy pluspolicy_version;versionperrestaurant begins1 increments1onlysuccess;replay200original/noallocation.
225. Policy0 originalfixture rules appliesbeforepublishedpolicy;immutable originalconfiguration.
226. Select policyby bookingLOCALstartdate:greatest effective_from<=date,tiestakegreatestpolicy_version;publicationordercan differ dateorder.
227. Effective dates may be past;new samedatepolicy supersedes futuredecisions only;publication never retroactively editsacceptedbooking/end/history/revisions.
228. GET /restaurants/{id}/policies public,policieslist publicationorder,omitpolicy0;unknownrestaurant404.
229. Ordinaryrestaurantdetail stays originalfixtureconfiguration includingtablecapacities,hours;availability/decisions selectedpolicy.
230. EveryNEW reservationcurrentresponse gains revisioninteger1 atcreation andaccepted_terms entireselectedpolicy excluding effective_from.
231. accepted_terms includespolicy_version,grid,duration,cutoff,openinghours,completecapacities;immutable copies,not sharedmutablepolicyrefs.
232. Seedbookings revision1 underpolicy0;seedhistory createdor supported consistent default;types/cancelledstates valid.
233. Old idempotencyresponses remain EXACT originalJSON including absentnewfields/originalrevision+terms,not currentviews.
234. Cancel usesacceptedoldcutoff/currentstart;firstcancel incrementsbookingrevision1;repeatcancel nochange.
235. Realamendment checksoldacceptedcutoff first then validates ALL resultingfields under resultingdatepolicy,evenunchangedfields.
236. Realamendment atomically replacesacceptedterms/endtime,revision+1,changedhistory+1,occupancy;failedchangesnone.
237. No-op retainsacceptedterms,endtime,revision/historyevenifnewpublishedpolicyapplies;stillconfirmed/editablerequired.
238. PATCH expected_revision optional;integer>=1 mismatched409 stale_revision BEFOREcutoff/validation;invalidtype/range422.
239. Two concurrent realchanges using sameexpected_revision have exactlyonewinner;no-opserialsemantics preservecounter.
240. UnrelatedunknownPATCHfields ignored;expected_revision wrongbool/fraction/string/zero/negative422.
241. GET /reservations/{reference}/decision returnsreference,currentrevision,accepted_termsincludingcancelled;owneronly404evenanonymous.
242. History/decision authvisibility exception resolved404foranonymous;privateexistenceneverleaks.
243. POST /series adopts existinganchor occurrence0;requiresauth/key,anchor_reference,count,interval_weeks;unknownfieldsignored.
244. Series anchorowned,confirmed,editableunderacceptedcutoff;unknown/otherowner404,cancelled409reservation_cancelled,alreadyadopted409already_in_series.
245. Series countinteger2..12 inclanchor,interval_weeksinteger1..4;bool/wrongtype/range422;no token401.
246. Occurrence0 isanchor unchangedreference,identity,revision,terms,history,timestamps,originalbookingreceipt.
247. Occurrence i localcalendaranchor date+i*interval_weeks*7days,samelocalclock acrossDST;not absoluteweeklyseconds.
248. Each generatedoccurrence chooses owndatepolicy,includinggrid/duration/capacity/cutoff/hours;sametable selection/partysizeasanchor.
249. Generatedgaplocaltime invalid_local_time rejectsWHOLEadoption;foldresolvesfirstonly.
250. Ordinarybookingslot/opening/capacity/occupancyrulesapplyeachgeneratedoccurrence;firstfailingindex determinesordinarycode.
251. Failedseries leavesno partialseries,reservations,histories,counters,anchormembership orkeyclaim;samekeymaylater succeed.
252. Series success201 series_id,revision1,interval_weeks,occurrences orderedindex0..count-1 eachreference/exceptionfalse/reservationordinaryshape.
253. Occurrence references globallydistinct,indicesstable and identities immutablewhenlaterdates/tableschange.
254. Occurrences appearordinaryreservationlists,occupytables,own ordinaryhistories.
255. GET /series/{series_id} returnscurrentstateshape;owneronly;otherguest/anonymous/unknown404.
256. RealindividualPATCH permanentlysetsoccurrenceexceptiontrue andincrementsseriesrevisiononce;no-op/failure leavesunchanged.
257. Firstoccurrencecancel incrementsseriesrevisiononce withoutnewexceptionflag;repeatcancelnothing;cancelledretainedoccurrence.
258. Cancellinganchor nevercancelsiblings;ordinarycutoff/expectedrevision checksapply.
259. Seriesadoption restaurantrevisionchanges deferred correctnessuntilstage4 perorganiser;notstage3acceptanceblocker.
260. Series replay200 originalseriesresponse evenafteramend/cancel;changesnocounters/exceptions/history.
261. Stage3 accepts ownstage1+stage2exports;importedbookings revision1/policy0terms withhistoryEMPTYoronecreatedentry perorganiser.
262. Imported legacyanchor canbeadopted;confirmationlinks/sessions/originalbookingretry remainvalid.
263. Stage2 combinedacceptedterms useSUMSELECTEDpolicycapacities,notfixturecapacities.
264. Reversedinputpair sameunorderedset no-op;declaredorder histories/responsesnormalizedwithoutnewrevision.
265. Batch permoveexpected_revision optional followsPATCHvalidation/stale-before-cutoff;realchange adopts resultingdatepolicy;no-op retainterms/history.
266. Batchvalidatesallamendmentrules before occupancy,nonoccupancyerrors precedenceininputorder;failureallrecord/occupancy/terms/history/revision/seriesflags/receipt unchanged.
267. Batch everychangedbooking +1revision/+1changedhistory;unchanged nohistory/revision.
268. Batch eachAFFECTEDseries+1 revisionTOTALevenmultiplechangedoccurrences;eachchangedoccurrenceexception permanentlytrue.
269. Batchfailure/replay no revisions/history/exceptionflags;successful originalbatchreceipt survives laterchanges/import.
270. Sharedanchor concurrentseriesadoptions exactlyonewinner;unusedidenticalkeyreplaysone201others200sameoriginalseriesresponse.
271. Policyversionidentifier scopedrestaurant;policymappingversion/effectivedate consistent,immutable,currentselectiondeterministic.
272. Bookingrevision scopedreservation,integer>=1;historyseqscopedreference,strictsequential/monotonictimestamps/revision/event/changes/termsconsistent.
273. Acceptedterms snapshot references validoriginalorselectedimmutablepolicy,fullrestauranttablescapacities,positiveintegerfields and validhours;loading verifiesnot currentpolicyreplacement.
274. SeriesID globallyuniqueopaque<=64;ownerexistinguser,occurrenceanchor/reservationownership/restaurantcompatible,count/intervalbounds,indexsequence,distinctrefs and onemembershipperreservation.
275. Seriesrevision scopedseries integer>=1,perchange/cancel/batchsemantics;exceptionboolperoccurrence andpermanentafterrealchange.
276. Seriesmembership links existingreservations bidirectionally,stableindex/reference;noorphan/doubleadoption;loading/reset/transfer validatesrelationships.
277. New policy/series idempotencyrecords scopeduser/method/path/key with parsedbody/originalresponse;invalidrequestsconsumenothing;transferpreservesoriginalresponsesandowners.
278. Reset validatesmanager_user_ids array ofdistinctknownuserIDs,restaurantpolicyrules/IDscopes/types includingboolintegerrefusal.
279. Resetall newstate policyversions/series/history/receipts cleared;repeatedreset atomic and oldtokensinvalid.
280. Import newstate includesimmutablepolicies,acceptedterms,booking/history/seriesrevisions,exceptionflags,membership and everynewpathreceipt;validate beforeatomicreplace.
281. Badnewstate (invalidboolintegers,policyversion/date/managerrelations,historyseq/events/terms,seriesownership/index/membership/overlap)422withoutstatechange/no5xx.
282. Legacyimport validbookingfields/overlap/type/relationschecked unchanged;conversiondefaultspolicy0/revision1/historyemptyorcreated withoutregeneratingexistingIDs/timestamps/receipts.
283. Exportatomicsnapshot read-only detached acrosspolicies/bookinghistory/series/receipts;sourcewritesafterexportdon'tmutateit.
284. Failedrequestkeys remain reusable acrossseries/policyfailure andtransfer;resetclearsimportedstate.
285. API old/new policies/history/series/receipts concurrency serializable underup-to50load,consistentreads;nopartialcounter/history/terms/membership observed.
286. Stoppedstage2->stage3 actualprocess/container proof beforedestinationimport includesoldsessions,single/pairbookings,originalcreate/movereceipts,browserpendingretry;alsoownstage1export accepted.
287. Roundtripstage3->independentstage3 carriespolicies,series,history,acceptedterms,currentrevisions andallreplayresponses exactly.
288. Independentchecks testpolicyinvalidwritesnoversion,publicationdateorder/samedatetie,perdateacceptanceandimmutability,cutoffoldterms,no-op/historyfixedorder,cancelrepeat.
289. Independentchecks testexpectedrevisiontypes/staleerrorprecedence/concurrentwinner,private404guest/anonymousforallnewprivatepaths,explainliteraltrue/allrulesbothfalse.
290. Independentchecks testseriesDSTgap/fold/localclock/peroccurrencepolicy/atomicfailurekeyreuse/anchoradoptionrace/occurrenceexceptions/onebatchseriesincrement/transferreceipts.
291. Browserallinheritedflows retainnewresponsefields andselectedpolicyavailabilitywithoutnewrequiredscreens;375px/1280px,label/focus/contrast/recoverystates/axe/upgradevisualevidence.
292. Record exactstage/rejection start/end,fullcandidate/reviewrevision,harnessclaimedstage3,newfolderreport,perseatresults,maintainabilityvsstage2/openlimits.




## Stage 4 additions

293. Preview manager/auth/key permissions and receipt precedence inherited; unknownrestaurant404,nonmanager403,noauth401.
294. Requiredtable_id/from/to explicitoffsetinstants from<to; invalidinterval422 validation_failed,unknownlocaltable404.
295. Closurehalfopenabsolute restaurant+table scope; considerALLconfirmedrestaurantbookings overlapping interval, othersfixed.
296. Support6tables,4declaredpairs,6consideredbookings; larger may422 planning_limit.
297. Eachassignment single/declaredpair capacity under ownacceptedterms, retains reference/owner/party/start/end/terms; repairignorescutoff.
298. Avoidfixedbookings,otherassignments,appliedclosures,proposedclosure per member forfullbookinginterval.
299. Lexicographicallyminimize changedTABLESETcount,totalunusedseats,rankvector inascendingreferenceorder.
300. Optionranks0-based singlesfixtureorder then declaredpairorder; reversedpairs sameSET; unusedseats allconsideredcapacity-minusparty.
301. Preview201 plan_id,restaurant_revision,closure,allassignments referenceorder/changedbool,moved_count,unused_seats.
302. Preview storesONLYplan; no closure/occupancy/history/booking/series/restaurantrevision changes.
303. No feasibleplan409 no_feasible_plan changesnothing/consumesnokey.
304. Restaurantrevision scope restaurant,integer>=0,boolinvalid; starts0afterreset.
305. Newbooking,realPATCH,firstcancel,successfulpolicypublication incrementrestaurantrevision ONCE perrequest.
306. Seriesadoption and realatomicbatch eachincrementONCE; all-noopbatch none.
307. Failure/noop/preview/replay/read neverincrement; otherrestaurantwrite doesnot stale targetplan.
308. Applymanager/auth/key POST replanapply body{}; unknownplan/wrongrestaurant404.
309. Interveningtargetrestaurantrevision409 stale_plan atomicallyunchanged.
310. Alreadyapplieddifferentkey409 plan_already_applied; successfulsamekeyreplay200 EXACToriginalevenafterchanges.
311. Apply201 plan_id,restaurant_revision,reservationsALLconsideredreferenceorder.
312. Applyatomicclosure+assignments; everyread before/after,no partialoccupancy.
313. Movedbookingrevision+1,reassignedhistory table_ids completebefore/after andplan_id; even singletonrepair uses table_ids.
314. Unmovedbooking nohistory/revision; movedterms/times/party/owner/identity preserved.
315. Wholeplan restaurantrevision+1 includingzero-moveclosure.
316. Closures exclude singles/pairs availability andrealcreates/amends409 table_unavailable; explainno_overlapfalse independentlycapacity.
317. Halfopenclosureadjacency/nonlocalrestaurantunaffected; serialapplicationrace exactlyonewinner/newkeys,samekeyone201others200.
318. Seriesamend owner/auth/key;unknown/otherowner404,noauth401.
319. Requiredexpected_revision integer>=1,from_indexinteger0..count-1,local_time exactHH:MM00:00..23:59;bool/fraction/stringinvalid422.
320. Mismatchedseriesrevision409 stale_revision beforeoccurrencecutoff/bookingvalidation;unknownfieldsignored.
321. Eligibleindices>=from_index skipscancelled/exceptions,retainothersunchanged.
322. UseORIGINALscheduledlocaldate/newclock,currenttables/reference/owner/party; movedindividualdate mustnotbecomeschedule.
323. No-op retains terms/end/history/allrevisions; realchangeoldacceptedcutoffthenallresultfieldsselecteddatepolicy.
324. DSTgaprejectwhole,foldfirst,absolute duration inherited; nonoccupancyerror indexorder outranks ANYoccupancy.
325. Avoidunchangedoccurrences/otherbookings/closures;conflict409 table_unavailable.
326. Failureallrecords/terms/history/revisions/flags/receipts unchanged;samekeyreusable.
327. Success201 currentseriesorderedstableindices;eachrealchangebookingrevision+1/ordinarychangedhistory.
328. Series+restaurantrevision each+1TOTALifanychange;all-noop/emptyeligible succeeds201 unchanged.
329. Seriesamend nevermarks/clearsexceptions;replay200originalafterlaterchanges/import.
330. Repairpreserves seriesexceptionflags/scheduleddates/terms/identity;eachaffectedseries+1onceifmembersmoved.
331. SameexpectedseriesrevisionconcurrentREALchanges exactlyonewins;identicalsamekeyone201others200.
332. Resetclearsclosures/plans/appliedflags/newreceipts/restrevision0 andallinheritedstateatomically.
333. Closure records validate offsetinterval/localtable/restaurantrelations andconflictconsistency onload/import.
334. PlanID globallyuniqueopaque<=64,existingrestaurant,capturedrevisioninteger>=0,detachedsnapshot.
335. Planassignments uniqueknownreferences/referenceorder/memberrelations/owntermscapacity/changedflags/objective totals valid.
336. Validatehistoric/appliedplan snapshots withoutrequiringequalitywith laterchangedbookings;appliedmarker preventsdoubleapplyaftertransfer.
337. Seriesoriginalscheduleddate/index/anchorcalendarrelationships stablethroughmoves/repairs/amend,loadingchecksconsistency.
338. Reassignedhistory validplan_id/table_ids/revision/terms;newreceiptuser/method/path/keyscopes andimmutableoriginalresponses validated.
339. Nativeexport preserves closures/plans/status/restrevision/scheduleddates/series/history/terms/ALLnewpathreceipts; detachedatomicread.
340. Nativeimportallnewtypes/boolintegers/IDs/owners/relations/intervals/snapshots/counters validatedbeforeatomicreplace;bad422unchanged/no5xx,malformedJSON400.
341. AcceptownStage1–3exports,preserveoldtokens/refs/revisions/terms/history/receipts;legacyrestaurantrevisiondefaultwell-definedcorrectFROMStage4.
342. Importedseriesincludingmoved/cancelled/exceptions supportsamend/repair andoriginalscheduleddates.
343. ActualfrozenStage3source stopped/portclosed BEFOREindependentStage4import,no sourcefiles/volume/networkdependence.
344. Same-tabStage3->4auth/form/pendingbody/key/originalretry/lookup surviveswithoutreload.
345. Existing375px/desktopUIreflectsappliedplanauthoritativeavailability/confirmation/lookup;nonewscreensrequired.
346. NativeStage4roundtrip preservesunappliedplanstaleness/applicability,appliederrors,closures,series/history/replayresponses exactly.
347. 50mixedconcurrentreads/writes/reset/export/import/preview/apply/seriesamend serializable,no5xx.
348. Independentplanningoracle proves everyobjective priority/ownterms/mixedpairs/fixedbookings/closures/adjacency/limits.
349. Independentchecks everyrestaurantrevisionwritepath/noop/failure/replay/preview/localstaleness andplan/series/anchor races.
350. Exactisolated --repo --stage4harness claimedstage4,allshippedinherited/newchecks no skips/deselection/edits.
351. MeasurePythonradon/lizard/JS/duplicationlimitsagainst frozenStage3;recordstages/rejectionsstart/end/finalacceptedrevisions/contributions/claimpath/openlimits.
# Tablekeeper — Stage 4: seating changes and recurring amendments

Extends all earlier stages, including stage-1 atomic reservation moves, stage-2 table
combinations and stage-3 policies and recurring agreements. All earlier requirements apply.

## Seating changes after a table closure

When a table becomes unavailable, a manager can review a proposed seating arrangement
before applying it. Customers must keep their booking times, party sizes and accepted terms.
No new screens are required. Existing availability, confirmation and lookup screens must
reflect an applied plan.

`POST /restaurants/{id}/replans` requires a manager and an idempotency key. Body:

```json
{"table_id": "t_2", "from": "2026-09-28T18:00:00+02:00",
 "to": "2026-09-28T23:00:00+02:00"}
```

The instants have explicit offsets and `from < to`; invalid interval is 422
`validation_failed`, unknown table 404. The proposed closure is the half-open interval
`[from,to)`. Consider every confirmed booking at this restaurant overlapping that interval.
Other bookings retain their assignments.
Planning must support up to 6 tables, 4 declared pairs and 6 considered bookings; larger
inputs may return 422 `planning_limit`. Each considered booking must retain its reference,
owner, party size, start, end and accepted terms. Assign it a single or a declared pair with
enough capacity under **its own accepted terms**, without conflicts with fixed bookings,
other assignments, previously applied closures or the proposed closure. Diners' cancellation
cutoffs do not prevent an operator repair. No booking may disappear or be cancelled.

Among feasible plans minimize, in order:

1. Number of bookings whose table set changes.
2. Total unused seats across all considered bookings (capacity minus party size).
3. The vector of option ranks in ascending reservation-reference order. Singles are ranked
   first in fixture order, then pairs in declared order, starting at 0.

Returns 201:

```json
{"plan_id": "opaque", "restaurant_revision": 4,
 "closure": {"table_id": "t_2", "from": "...", "to": "..."},
 "assignments": [{"reference": "ABC12345", "table_ids": ["t_1"], "changed": true}],
 "moved_count": 1, "unused_seats": 0}
```

Assignments include every considered booking in reference order. A restaurant revision starts
at 0 after reset and increments once for each successful new booking, real amendment,
cancellation, policy publication or plan application. No-op writes, failures, previews and
replays do not increment it. Preview stores only a plan: no closure, occupancy, reservation
revision or history changes. No feasible plan gives 409 `no_feasible_plan`, changing nothing.

`POST /restaurants/{id}/replans/{plan_id}/apply`, body `{}`, requires a manager and an
idempotency key. Return 201 with `{"plan_id": "...", "restaurant_revision": 5,
"reservations": [...]}`; reservations include every considered booking in reference order.
Unknown plan or one from another restaurant is 404. Any intervening restaurant revision
invalidates the plan: 409 `stale_plan`, changing nothing. A plan already applied under a
different key gives 409 `plan_already_applied`; replay of the successful key returns the
original response with 200, even after later changes. Application is atomic.

Application records the closure and all assignments together. Each moved booking increments
its revision once and gains one `reassigned` history entry with a `table_ids` change and
`plan_id`; accepted terms and times remain identical. Unmoved bookings gain nothing. The
restaurant revision increments once for the **whole plan**. Closures thereafter exclude
singles and pairs from availability and reject creates/amendments with 409 `table_unavailable`.
In explanations, `no_overlap` is false for a closure as for a conflicting booking.

Concurrent applications must not leave partially moved bookings. A closure at another
restaurant does not invalidate this plan.

## Amend recurring reservations

`POST /series/{series_id}/amend` is an owner-only idempotent write. Unknown or another owner's
series is 404; no token is 401. Body:

```json
{"expected_revision": 3, "from_index": 2, "local_time": "20:00"}
```

Revision must be a positive integer; from_index an integer in 0..count-1; local_time exactly
HH:MM in 00:00..23:59. Booleans are invalid integers. Invalid input gives 422
`validation_failed`; a mismatched series revision gives 409 `stale_revision` before any
occurrence's cutoff or booking validation. Unknown fields are ignored.

Consider indices at or after from_index, excluding cancelled occurrences and those marked
exception. Change their clock time on their original scheduled local dates, retaining each
reference, owner, party size and current table selection. A change with identical
resulting fields is a no-op and retains its terms. Each real change checks its old accepted
cutoff, then adopts the policy for its resulting start date, just like an individual PATCH.

The resulting occurrences must not conflict with unchanged occurrences, other bookings
or applied closures. On failure, histories, idempotency records and all revisions remain
unchanged. Non-occupancy errors take precedence in occurrence-index order; otherwise an
occupancy conflict returns `table_unavailable`.

On success return 201 with the current series response. Each changed occurrence gains one
ordinary changed history entry and one reservation revision. The series and restaurant
revisions each increase once for the entire operation if anything changed. Series amendments
do not mark exceptions. All-no-op or empty eligible sets succeed without changing revisions.
Replay returns the original response with 200 even after further edits or cancellations.

Seating repairs may move series occurrences. They preserve their exception flags, scheduled
dates, identities and accepted terms. Each affected series revision increases once per plan
application if at least one member moved.
Concurrent amendments from the same expected revision may not both make a real change.

A stage-4 service must accept exports produced by the same team's stages 1–3. These
operations must support imported series, including moved and cancelled occurrences.
Earlier booking and series receipts, histories and retries remain valid.


# Tablekeeper — Stage 3: booking policies, history and recurring reservations

The requirements from stages 1 and 2 continue to apply, with the additions below.
Numbered section references such as §5 and §7 refer to `stage-1.md`.

Restaurants can publish dated booking policies. Diners can see why a table is unavailable,
view their reservation history and arrange recurring bookings.

## Availability explanations

Whether a table is available for a slot is decided by two rules, each independent of the other:

| Rule | Holds when |
|---|---|
| `capacity` | `party_size` is at most the table's `capacity` |
| `no_overlap` | no confirmed reservation on that table overlaps the slot's interval |

A table is available exactly when both hold. `available_table_ids` is unchanged in meaning.

```http
GET /availability?restaurant_id=r_anker&date=2026-09-24&party_size=4&explain=true
```

`explain` is optional. Its only accepted value is `true`; any other value, including `false`,
`1` and the empty string, is 422 `validation_failed`. **Without it the response keeps stage
1's shape** — no explanation fields appear. Published policies can change the slot values.

With it, every slot carries one further field:

```json
{ "starts_at_local": "2026-09-24T18:00",
  "starts_at": "2026-09-24T18:00:00+02:00",
  "available_table_ids": ["t_2"],
  "explain": [
    { "table_id": "t_1", "policy_version": 0, "available": false,
      "rules": [ { "rule": "capacity", "holds": false },
                 { "rule": "no_overlap", "holds": true } ] },
    { "table_id": "t_2", "policy_version": 0, "available": true,
      "rules": [ { "rule": "capacity", "holds": true },
                 { "rule": "no_overlap", "holds": true } ] }
  ] }
```

1. **Every table of the restaurant appears exactly once**, available or not, in fixture order —
   the same order `available_table_ids` uses.
2. **Both rules are reported for every table**, in the order above. A rule that holds is
   reported holding; a table excluded by both reports both false. No rule may be omitted.
3. **`available` is true exactly when both rules hold**, and the `table_id`s whose `available`
   is true are exactly `available_table_ids`, in the same order.
4. A closed day still returns `"slots": []`, and a slot with no available table still appears —
   now with a full `explain` for every table.

## Reservation history

```http
GET /reservations/{reference}/history
```

The reservation's own record, oldest first. Only its owner may read it; anyone else, signed in
or not, gets the same 404 `not_found` that §8 gives for a reservation that is not theirs. A
cancelled reservation still has its history.

The example below shows the event fields; every entry also carries `revision` and
`accepted_terms` as specified under “Policies and accepted terms”.

```json
{ "reference": "ABC12345",
  "entries": [
    { "seq": 1, "at": "2026-09-17T12:00:00+02:00", "event": "created",
      "changes": [ { "field": "table_id", "from": null, "to": "t_2" },
                   { "field": "starts_at_local", "from": null, "to": "2026-09-24T19:00" },
                   { "field": "party_size", "from": null, "to": 4 } ] },
    { "seq": 2, "at": "2026-09-17T12:05:00+02:00", "event": "changed",
      "changes": [ { "field": "table_id", "from": "t_2", "to": "t_3" } ] },
    { "seq": 3, "at": "2026-09-17T12:09:00+02:00", "event": "cancelled", "changes": [] } ]
}
```

1. **`seq` starts at 1 and increases by exactly 1**, so the order is total even when two writes
   land in the same second. Entries are returned in `seq` order, which is also `at` order.
2. **`created` names all three fields**, each with `"from": null`.
3. **`changed` names only the fields that actually changed**, in the order `table_id`,
   `starts_at_local`, `party_size`. A `PATCH` that sets a field to the value it already has
   changed nothing: it still succeeds, and it records **no entry at all**.
4. **`cancelled` carries an empty `changes`**, and nothing follows it.
5. Replaying an idempotent `POST /reservations` records nothing — a replay returns the original
   response and does not re-run the operation (§7).

## Existing screens

No new screens are required for explanations or history. The availability grid continues
to follow the stage-2 rules.

## Policies and accepted terms

Restaurants may now declare `manager_user_ids` in their reset fixture (default `[]`). Only
these users may publish policies. Unknown restaurant is 404;
an authenticated non-manager is 403 `forbidden`; no token is 401. This extends stage 1's
minimal permissions; managers do not gain access to other diners' private lookup/history.

`POST /restaurants/{id}/policies` requires an idempotency key, with stage 1's replay rules.
It accepts a **complete policy**, not a patch:

```json
{
  "effective_from": "2026-09-28",
  "slot_minutes": 30,
  "reservation_duration_minutes": 120,
  "cancellation_cutoff_minutes": 60,
  "opening_hours": [{"weekday": "mon", "opens": "18:00", "closes": "23:00"}],
  "capacities": {"t_1": 2, "t_2": 4, "t_3": 6}
}
```

Returns 201 with the supplied policy plus `policy_version`, an integer starting at 1 and
increasing by one per restaurant. Failed writes and replays allocate no version. Policy 0
is the original fixture's rules and applies before any published policy. Policies are
immutable. Publication order may differ from effective-date order. For a booking's **local
start date**, choose the greatest `effective_from` not later than that date; ties choose
the greatest `policy_version`. A new same-date policy supersedes the old one for future
decisions, without changing any accepted reservation. Effective dates may be in the past;
publication never retroactively edits a booking.

All fields above are required. `effective_from` is an actual `YYYY-MM-DD` date; grid and
duration are integers 1..1440; cutoff is an integer 0..10080; booleans are not integers.
Opening hours follow stage 1 and contain no duplicate weekdays. `capacities` names **exactly**
the restaurant's table ids with integer capacities 1..100. Invalid policy is 422
`validation_failed`, with no version or state change. Table ids, labels, timezone and
declared combinations cannot be changed by a policy. Unknown fields are ignored.

`GET /restaurants/{id}/policies` is public and returns `{"policies": [...]}` in publication
order, omitting policy 0. The ordinary restaurant detail still returns its original fixture
configuration. Availability and booking decisions use the selected policy, not that detail.
With `explain=true`, each table explanation additionally identifies its `policy_version`.

Every reservation response gains `revision` (1 at creation) and `accepted_terms`:

```json
{"policy_version": 0, "slot_minutes": 30,
 "reservation_duration_minutes": 90, "cancellation_cutoff_minutes": 120,
 "opening_hours": [{"weekday": "mon", "opens": "18:00", "closes": "23:00"}],
 "capacities": {"t_1": 2, "t_2": 4, "t_3": 6}}
```

These are a snapshot of the entire selected policy, excluding `effective_from`. Seeded
bookings start at revision 1 under policy 0. Responses to old idempotency keys remain the
original response, including the original revision and terms.

- A policy publication does not change existing bookings, their end times, or their history.
- Cancel checks the accepted cutoff, against the current start.
- A real diner amendment (time, tables or party size) checks the old accepted cutoff first,
  then validates **all** resulting fields against the policy applicable to the resulting start
  date. It atomically replaces accepted terms and end time and increments revision once.
- A no-op amendment retains terms, end time and revision and records no history. It still
  requires a confirmed, editable booking.
- Failed amendments change nothing. Cancel increments revision once; repeated cancel does not.
- `PATCH` optionally accepts `expected_revision`. A positive integer differing from the current
  revision gives 409 `stale_revision` before cutoff/validation; invalid type/range gives 422.
  Omission retains stage 1 semantics. Two concurrent amendments using one revision: at most one
  real change succeeds. Unrelated unknown fields remain ignored.

Each history entry additionally carries the reservation's resulting `revision` and complete
`accepted_terms`. Old entries never acquire newer terms. `GET /reservations/{reference}/decision`
returns `{"reference": "...", "revision": 1, "accepted_terms": {...}}` for the current booking,
including after cancellation, with history's owner-only 404 rule. History and decision return
404 even without authentication, resolving the exception to stage 1's general 401 rule.

## Recurring reservations

`POST /series` adopts an existing reservation as occurrence zero of a recurring agreement.
An idempotency key is required. Body:

```json
{"anchor_reference": "ABC12345", "count": 8, "interval_weeks": 1}
```

The anchor must belong to the caller, be confirmed and satisfy its accepted cancellation
cutoff. Unknown or another owner's anchor gives 404 `not_found`; cancelled gives 409
`reservation_cancelled`; already adopted gives 409 `already_in_series`. `count` is an integer
2..12 including the anchor; `interval_weeks` is an integer 1..4. Invalid values, including
booleans, give 422 `validation_failed`. No token gives 401.

Occurrence zero is the anchor itself: its reference, identity, revision, terms, history,
timestamps and original idempotent response remain unchanged. Occurrence i starts on the
anchor's local calendar date plus i × interval_weeks × 7 days, at the same local clock time.
Each generated occurrence independently selects its date's policy, including duration and
capacity, and obeys ordinary opening, DST and occupancy rules. A nonexistent local time
rejects the entire adoption with `invalid_local_time`; repeated times use stage 1's first
occurrence rule. Generated occurrences use the anchor's party size and table selection.
No partial series, reservations, histories, counters or idempotency claim survive failure.
The first failing occurrence in index order determines the ordinary booking error.

Return 201:

```json
{"series_id": "opaque", "revision": 1, "interval_weeks": 1,
 "occurrences": [{"index": 0, "reference": "ABC12345", "exception": false,
                  "reservation": {"...": "ordinary reservation response"}}]}
```

The array includes all count occurrences in index order. Each has a distinct ordinary
reservation reference; references and indices never change when dates or tables change.
Occurrences appear in ordinary reservation lists, occupy tables, and have ordinary histories.
`GET /series/{series_id}` returns this shape with current reservation states. Only the owner
may read it: another user or no token gives 404 `not_found`.

A real individual PATCH permanently marks that occurrence as `exception: true` and increments
the series revision once; a no-op or failure changes neither. Cancellation increments the
series revision once, retaining the cancelled occurrence, but does not mark it as an
exception; repeated cancel does nothing.
Cancelling the anchor does not cancel its siblings. Ordinary cutoff and revision checks still
apply. Adoption increments the restaurant revision once for the whole operation. Replays
return the original series response, even after later changes, and change no counter.
Series creation adds one idempotent write path. Unknown fields are ignored.

A stage-3 service must accept exports produced by the same team's stage-1 or stage-2
service. Adoption must work on reservations imported this way. Existing confirmation links,
sessions and original booking retries remain valid.

## Combined-table history

Stage 3's accepted terms apply to combinations too; capacity is the sum of the **selected
policy's** capacities. In history, retain stage-3 fields for single-to-single operations.
For a creation of a pair, replace the `table_id` change by `table_ids` (from null to the pair).
For a change involving a pair, use `table_ids` (complete before/after lists) instead of
`table_id`. Table-set order is the declared combination order. A reversed input pair names
the same set and is not an amendment on its own. Policy selection, revision and replay rules
are unchanged.

## Collective moves under policies and agreements

Each real change in `POST /reservation-moves` uses individual PATCH semantics: check the
old accepted cutoff, then adopt the resulting date's policy. Per-move `expected_revision`
is optional and follows PATCH validation and stale-revision rules. A no-op retains its
terms and history. All resulting bookings must satisfy amendment and occupancy rules;
failure leaves every booking unchanged. Every changed booking gains one revision and
changed history entry; the restaurant revision increases once for the whole batch.
Each affected series revision increases once,
and each changed series occurrence becomes a permanent diner exception. A
failed batch or replay changes no revisions, histories or exception flags.




# Tablekeeper — Stage 2: online booking and combined tables

The stage-1 requirements continue to apply, with the additions below. Numbered section
references such as §5 and §7 refer to `stage-1.md`.

Diners can search, book and manage reservations in a browser. Restaurants can offer
approved pairs of tables for larger parties.

The following screens must be reachable by URL. Other screens must be reachable through
the UI. Server-side and client-side rendering are both permitted.

| Route | Screen |
|---|---|
| `/` | Search and availability grid |
| `/signup` | Signup |
| `/login` | Login |
| `/lookup` | Look up a reservation by reference |

A screen route returns HTML; §3.4's `application/json` convention is about the API, and does
not govern the routes in the table above.

## Competing clients and uncertain outcomes

The UI must handle responses arriving out of order and connections failing after submission.

- If search A starts before search B but finishes after it, the grid, table labels and
  booking form must describe B. A late response must not restore A's results.
- If another client takes a table after the form opens, a `409 table_unavailable` response
  shows `booking-error` and refreshes availability. Preserve the selected form and its
  inputs so the diner can change their choice. Do not show a confirmation for that attempt.
- If a booking response is lost, including after the booking commits, show nonempty
  `booking-uncertain` text, without `booking-error` or a new confirmation. The unchanged
  form must retry with the same idempotency key and body. A successful retry removes the
  uncertainty/error elements and shows the original reference. A confirmed rejection
  uses `booking-error`.

These rules apply to combination bookings too. No background polling, live updates,
cross-tab storage synchronization, or recovery across a page reload is required. The server
remains authoritative; the browser must not manufacture a successful result from cached data.

The UI must expose the `data-testid` attributes listed below for integration testing.
Additional elements are permitted, and the visual implementation is the team's choice subject
to the product-quality requirements below.

## Product and visual direction

The browser experience must feel like a coherent, presentation-ready restaurant product, not a
test harness with controls attached. Aim for a warm, confident hospitality character. The search,
availability and booking flow should have an obvious visual hierarchy; a diner should be able to
scan dates, times, party size and table choices without having to interpret raw API data. Combined
tables should read as intentional seating options, not as concatenated technical identifiers.

Use a consistent visual system for typography, spacing, colour, controls and feedback. Primary
actions must be easy to identify. Available, unavailable, selected, loading, successful, refused
and uncertain states must be visually distinct as well as satisfying the behavioural requirements
below. Use human-readable restaurant and table labels prominently; expose technical identifiers
only where they help the user.

The required flows must remain clear and usable at a 375 CSS-pixel viewport and at conventional
desktop widths, without horizontal page scrolling. Inputs need visible labels, keyboard focus must
be apparent, and text and controls need sufficient contrast. Provide considered empty, loading and
error states, and keep navigation consistent across the required routes. A custom illustration,
brand asset or exact visual match to a reference is not required.

## Signup and login

| `data-testid` | Element |
|---|---|
| `signup-email`, `signup-password`, `signup-display-name` | Inputs |
| `signup-submit` | Button |
| `login-email`, `login-password`, `login-submit` | Inputs and button |
| `auth-error` | Error message. Present only when there is one |
| `current-user` | Visible on every screen when signed in. Text contains the display name |
| `logout-button` | Button |

## Search and availability grid — `/`

| `data-testid` | Element |
|---|---|
| `restaurant-select` | Selects a restaurant. Option values are restaurant ids |
| `date-input` | Date, value `YYYY-MM-DD` |
| `party-size-input` | Number |
| `search-button` | Runs the search |
| `availability-grid` | Container for the results |
| `slot-{table_id}-{HH:MM}` | One cell per table per slot, e.g. `slot-t_2-19:00` |
| `no-slots` | Shown instead of the grid when the day has no slots |

Each cell carries `data-available="true"` or `data-available="false"`. A cell is `true` exactly
when its `table_id` is in that slot's `available_table_ids` from `GET /availability` for the party
size that was searched, and `false` otherwise. Clicking an available cell
opens the booking form for that table and slot. Clicking an unavailable cell does nothing.
Booking requires a signed-in user: clicking an available cell while signed out shows `auth-error`
or navigates to `/login`, your choice.

## Booking form

| `data-testid` | Element |
|---|---|
| `booking-form` | Container |
| `booking-summary` | Text contains the table label and the local start time |
| `booking-party-size` | Number input, pre-filled from the search |
| `booking-submit` | Button |
| `booking-error` | Error message, when the booking fails |

Keep the booking form on screen after success. Submitting it again without changing a
field must return the same `confirmation-reference`, without `booking-error` or another
booking. Changing a field makes the next submission a new booking request. Retries follow §7.

## Confirmation

Shown after a successful booking.

| `data-testid` | Element |
|---|---|
| `confirmation` | Container |
| `confirmation-reference` | Text is exactly the reference, no surrounding words |
| `confirmation-details` | Text contains the restaurant name, table label and local start time |

## Lookup — `/lookup`

| `data-testid` | Element |
|---|---|
| `lookup-reference-input`, `lookup-submit` | Input and button |
| `reservation-detail` | Container, shown when found |
| `reservation-status` | Text is exactly `confirmed` or `cancelled` |
| `reservation-cancel-button` | Cancels. Absent once cancelled |
| `reservation-error` | Shown when not found, or when a cancel is refused |

## Existing clients after an upgrade

A stage-2 service must accept an export produced by the same team's stage-1 service. A
browser signed in before that export/import upgrade must remain signed in afterwards.
A retained booking reference still works through the lookup screen. A booking whose response
was lost before export remains retryable after import with the same body and key; the UI
must recover the original confirmation. These requirements apply when import completes
between browser requests; migration during an in-flight request is not required. No page
reload or new screen is required. The form and pending retry identity must survive the upgrade.

## Combined tables

A party may book two tables that the restaurant has declared combinable. The booking
occupies both tables for its full duration.
Existing single-table request formats remain supported.

## Model

The restaurant fixture gains one field:

```json
{
  "id": "r_anker",
  "combinable": [ ["t_1", "t_2"], ["t_2", "t_3"] ],
  ...
}
```

Each entry is an unordered pair of table ids in that restaurant. **Pairs only** — never three or
more. A pair not listed cannot be combined, whatever the table sizes are. Combining is not
transitive: `[t_1,t_2]` and `[t_2,t_3]` do not make `{t_1,t_3}` bookable.

A combination's capacity is the sum of its tables' capacities.

Seeded `reservations` are `confirmed` unless they carry a `status` of `cancelled`, and may hold
either `table_id` or `table_ids`.

## API

### `GET /availability`

Slots gain `available_options`. `available_table_ids` stays exactly as it was — single tables
only.

```json
{
  "slots": [
    {
      "starts_at_local": "2026-09-24T19:00",
      "starts_at": "2026-09-24T19:00:00+02:00",
      "available_table_ids": ["t_3"],
      "available_options": [
        { "table_ids": ["t_3"], "capacity": 4 },
        { "table_ids": ["t_1", "t_2"], "capacity": 6 }
      ]
    }
  ]
}
```

`available_options` lists every single table and every declared pair with
`capacity >= party_size` and no overlapping confirmed reservation on any member. Singles first in
fixture order, then pairs in `combinable` order. `table_ids` within a pair is in `combinable`
order.

### `POST /reservations`

The body takes `table_ids` instead of `table_id`:

```json
{ "restaurant_id": "r_anker", "table_ids": ["t_1", "t_2"],
  "starts_at_local": "2026-09-24T19:00", "party_size": 6 }
```

`table_id` is still accepted and means a set of one. Sending both is 422 `validation_failed`.

Responses always carry `table_ids`. They also carry `table_id` **when the set has exactly one
member**, and omit it otherwise.

| Case | Response |
|---|---|
| The pair is not in `combinable` | 422 `combination_not_allowed` |
| More than two tables | 422 `combination_not_allowed` |
| Any table in the set is taken for an overlapping interval | 409 `table_unavailable` |
| `party_size` exceeds the combination's summed capacity | 422 `party_exceeds_capacity` |
| Duplicate table id in the set | 422 `validation_failed` |

`PATCH /reservations/{reference}` accepts `table_ids` under the same rules. Cancelling frees every
table in the set.

## UI

The availability grid gains combination cells, shown when a declared pair is available for the
searched party size:

| `data-testid` | Element |
|---|---|
| `slot-{t_a}+{t_b}-{HH:MM}` | A combination cell, e.g. `slot-t_1+t_2-19:00`. Ids in `combinable` order. Carries `data-available` like a single cell |
| `confirmation-tables` | Text contains every table label in the reservation |
| `reservation-tables` | On the lookup screen. Same |

`booking-summary` must name every table in the selection. A single-table booking's cell testid,
confirmation and lookup are unchanged.

Atomic reservation moves from stage 1 also accept `table_ids` per move. No table may
belong to overlapping resulting bookings. The existing browser recovery and original-receipt
requirements also apply to combined-table bookings.

## Concurrent bookings and amendments

Concurrent requests must produce the same results as executing them one at a time in some
order, and the requirements above hold at every read.




# Tablekeeper — Stage 1: reservations

This stage defines the initial service and its API.

Build from the supplied requirements. Source code, API documentation and schemas from
existing products in this domain must not be used.

## 1. Scope

Diners can search restaurant availability, book a table and receive a confirmation
reference. They can cancel or amend their bookings, including changing several bookings
together. Each restaurant has its own table capacities, opening hours and cancellation policy.
Only the HTTP API is required.

Two `confirmed` reservations must never occupy the same table at overlapping times,
including during concurrent requests. Occupancy is the half-open interval
`[starts_at, starts_at + reservation_duration)`. A 90-minute booking at 19:00 therefore
does not overlap a booking starting at 20:30. Retries and rejected requests must not
create duplicate or partial bookings.

## 2. Delivery and deployment

Deliver an HTTP service, a `Dockerfile` and a `RUN.md` with a command that builds and
starts the service without manual setup. Language, framework and storage are unrestricted.
A `docker-compose.yml` is optional.

The submission is a containerized HTTP service, not a Python package. Python is not
required in the implementation. TypeScript/JavaScript, Go, Rust, Java, Python and any
other language are equally valid. The harness builds the submitted `Dockerfile`, starts
the resulting image and tests only its HTTP behavior; it does not import or execute the
submission's source files on the judge host.

The image must run on its own with `-e PORT=<port>` and a port mapping. Runtime networking
has no outbound access. All runtime dependencies, initialization and seed data must work
within that single container. Compose configuration is not used to start the service.

### Resource limits

The service must operate within these limits:

| Limit | Value |
|---|---|
| CPU | 2 vCPU |
| Memory | 2 GiB |
| Start to first healthy response | 60 s |
| Concurrent requests | up to 50 in flight |
| Per-request timeout | 5 s (10 s for `POST /_test/reset`) |
| Outbound network | available during `docker build`, **none at run time** |
| Disk | ephemeral; state need not survive a container restart |

Runtime assets and dependencies must be included in the image. This includes fonts,
scripts and stylesheets; external services are unavailable at runtime.

## 3. Runtime contract

### 3.1 Listening

Listen on `0.0.0.0` using the `PORT` environment variable, default `8080`.

### 3.2 Health

```http
GET /health  ->  200  {"status": "ok"}
```

Return 200 once the service and its data store can serve requests, within 60 seconds
of container start. Non-200 responses are permitted before the service is ready.

### 3.3 Reset and seed

```http
POST /_test/reset
Content-Type: application/json

{ ...fixture... }

->  204 No Content
```

Replace all service state with the fixture in the request body (§4). When reset returns
204, subsequent requests must see only that fixture. Repeated resets are supported.
This test endpoint must be enabled in the delivered image and requires no authentication.

### 3.4 Conventions

- Requests and responses are `application/json; charset=utf-8`.
- Timestamps in responses are RFC 3339 with an explicit offset, e.g. `2026-09-24T19:00:00+02:00`.
- Unknown fields in a request body are ignored, never an error.
- Unknown query parameters are ignored.
- IDs are opaque strings of at most 64 characters. Their format is yours. This limit
  also applies to IDs supplied in reset fixtures.

## 4. Model

Restaurants and tables are supplied through `POST /_test/reset` only. Restaurant and
table creation endpoints are out of scope.

| Field | On | Meaning |
|---|---|---|
| `timezone` | Restaurant | IANA zone name, e.g. `Europe/Berlin`. All of the restaurant's times are local to this |
| `slot_minutes` | Restaurant | Bookings start on a grid of this many minutes from opening time |
| `reservation_duration_minutes` | Restaurant | How long every reservation occupies its table |
| `cancellation_cutoff_minutes` | Restaurant | A booking cannot be cancelled or changed within this many minutes of its start |
| `opening_hours` | Restaurant | Per weekday. A day with no entry is closed |
| `capacity` | Table | Maximum party size |

### Fixture format

```json
{
  "users": [
    { "id": "u_ada", "email": "ada@example.com",
      "password": "correct horse", "display_name": "Ada" }
  ],
  "restaurants": [
    {
      "id": "r_anker",
      "name": "Zum Anker",
      "timezone": "Europe/Berlin",
      "slot_minutes": 30,
      "reservation_duration_minutes": 90,
      "cancellation_cutoff_minutes": 120,
      "opening_hours": [
        { "weekday": "thu", "opens": "18:00", "closes": "23:00" },
        { "weekday": "fri", "opens": "18:00", "closes": "23:30" }
      ],
      "tables": [
        { "id": "t_1", "label": "1", "capacity": 2 },
        { "id": "t_2", "label": "2", "capacity": 4 }
      ]
    }
  ],
  "reservations": []
}
```

- `weekday` is one of `mon tue wed thu fri sat sun`.
- `opens` and `closes` are local `HH:MM`, 24-hour. `closes` is always later than `opens` on the
  same local day — opening hours never cross midnight.
- Seeded users must be able to log in with the given password immediately.
- `reservations` may seed confirmed bookings, with the same fields as a `POST /reservations`
  body plus `id`, `reference` and `user_id`.

Fixtures may use any calendar date. A booking must not be rejected solely because its
start is in the past; the cancellation and amendment cutoff rules still apply.

## 5. Errors

Every 4xx and 5xx response carries this body:

```json
{ "error": { "code": "table_unavailable", "message": "human readable, any wording" } }
```

Use the specified HTTP status and `code`. The human-readable `message` may use any wording.
Endpoint-specific errors are listed with each endpoint.

| Status | `code` | When |
|---|---|---|
| 400 | `malformed_request` | Unparseable body, or a field of the wrong JSON type |
| 400 | `missing_idempotency_key` | Required `Idempotency-Key` header absent or empty |
| 401 | `unauthenticated` | Missing, malformed or unknown bearer token |
| 403 | `forbidden` | Authenticated, but not permitted to touch this resource |
| 404 | `not_found` | No such resource, or not visible to this caller |
| 409 | `idempotency_key_reuse` | Key already used by this caller with a different request body |
| 422 | `validation_failed` | A required field or query parameter is missing, or a stated rule is violated with no more specific code |

A field of the correct JSON type with an invalid format or out-of-range value gives
422 `validation_failed`, unless an endpoint specifies a different error. This includes
invalid dates, negative counts and values exceeding a stated maximum or length. In addition:

- Endpoint-specific field rules take precedence: invalid `party_size` values (including strings
  and booleans) and `starts_at_local` strings that are not a bare local `YYYY-MM-DDTHH:MM` are
  422 `validation_failed`. Other wrong JSON types follow the rule below.
- An integer-valued **query parameter** is written as plain decimal digits: `1e9`, `4.0` and `+4`
  are 422 `validation_failed` whatever their numeric value.
- Reserve 400 `malformed_request` for a body that does not parse or a field of the wrong type.

Shared ranges, enforced on every endpoint that takes them:

| Field | Valid | Otherwise |
|---|---|---|
| `Idempotency-Key` | 1 to 255 characters | 422 `validation_failed` |

Requests must not produce 5xx responses, including under concurrent load.

## 6. Authentication

Authentication supports signup and login. Email verification, password reset, refresh
tokens and role-management endpoints are out of scope. Permissions specified elsewhere
in these requirements still apply.

```http
POST /auth/signup
{ "email": "a@example.com", "password": "correct horse", "display_name": "Ada" }

->  201  { "user_id": "u_1", "display_name": "Ada", "token": "..." }
```

```http
POST /auth/login
{ "email": "a@example.com", "password": "correct horse" }

->  200  { "user_id": "u_1", "display_name": "Ada", "token": "..." }
```

| Case | Response |
|---|---|
| Email already registered | 409 `email_taken` |
| Password shorter than 8 characters | 422 `validation_failed` |
| `email` not of the form `local@domain` | 422 `validation_failed` |
| Wrong password or unknown email on login | 401 `unauthenticated` |

Every other endpoint requires a bearer token, except `/health`, `/_test/reset`, the two above, and
the three public endpoints named at the top of §8 — `GET /restaurants`, `GET /restaurants/{id}` and
`GET /availability`:

```http
Authorization: Bearer <token>
```

Tokens do not expire. An account may have multiple valid tokens and concurrent sessions.

Passwords must be stored using a password-hashing function such as bcrypt, scrypt or
Argon2, or an equivalent. Plaintext password storage is not permitted.

## 7. Idempotency

Two write paths require an idempotency key: **`POST /reservations`** (§8) and
**`POST /reservation-moves`** (§11).

```http
Idempotency-Key: <client-chosen string, 1..255 characters>
```

The key is scoped to **the authenticated user**. Two different users may use the same key string
with no interaction between them.

A replay means the same user sending the **same method, the same path and the same body**. The
same key with the same body on a different path is a different request, not a replay, and must
succeed normally.

After the body has been parsed as a JSON object and the caller authenticated, idempotency
is resolved before endpoint-specific field validation or current-resource checks. Thus a
used key with a different JSON body returns `409 idempotency_key_reuse` even when that new
body would otherwise be invalid.

| Situation | Response |
|---|---|
| Header absent or empty | 400 `missing_idempotency_key` |
| First use of the key | The normal response, **201** |
| Replay: same key, same body | **200**, body identical to the original response as a JSON value |
| Same key, different body | 409 `idempotency_key_reuse` |
| Key reused after the original request failed with 4xx | Treated as a first use |

"Same body" means the same JSON value after parsing — key order and whitespace do not matter.

For concurrent identical requests with an unused key, exactly one returns 201.
The others return 200 with the same body. The operation takes effect only once.

A successful replay returns the original response, even after the resource changes or
is cancelled. It makes no further state changes.

## 8. API

`GET /restaurants`, `GET /restaurants/{id}` and `GET /availability` are **public** — no bearer
token. Everything else needs one. Diners browse before they sign in.

### `GET /restaurants`

```json
{ "restaurants": [ { "id": "r_anker", "name": "Zum Anker", "timezone": "Europe/Berlin" } ] }
```

### `GET /restaurants/{id}`

The restaurant with its `slot_minutes`, `reservation_duration_minutes`,
`cancellation_cutoff_minutes`, `opening_hours` and `tables`, in the fixture's shape. 404 if
unknown.

### `GET /availability`

```http
GET /availability?restaurant_id=r_anker&date=2026-09-24&party_size=4
```

All three parameters are required; a missing one is 422 `validation_failed`. `date` is a local
calendar date at the restaurant.

```json
{
  "restaurant_id": "r_anker",
  "date": "2026-09-24",
  "timezone": "Europe/Berlin",
  "slots": [
    { "starts_at_local": "2026-09-24T18:00",
      "starts_at": "2026-09-24T18:00:00+02:00",
      "available_table_ids": ["t_2"] }
  ]
}
```

`starts_at_local` is the full `YYYY-MM-DDTHH:MM` and goes into `POST /reservations` unchanged.

A slot appears for every `slot_minutes` step from `opens` such that
`slot + reservation_duration_minutes <= closes`. `available_table_ids` lists the tables of that
restaurant with `capacity >= party_size` and no overlapping confirmed reservation, in fixture
order. A slot with no available table still appears, with an empty list.

A closed day returns `"slots": []`.

### `POST /reservations`

`Idempotency-Key` is required; see §7.

```http
POST /reservations
Authorization: Bearer <token>
Idempotency-Key: 2f9c1a...

{ "restaurant_id": "r_anker", "table_id": "t_2",
  "starts_at_local": "2026-09-24T19:00", "party_size": 4 }
```

`starts_at_local` is wall-clock at the restaurant, with no offset and no `Z`. Resolve it against
the restaurant's `timezone`.

```json
201
{
  "reservation_id": "res_7",
  "reference": "K3P7QW",
  "restaurant_id": "r_anker",
  "table_id": "t_2",
  "party_size": 4,
  "status": "confirmed",
  "starts_at_local": "2026-09-24T19:00",
  "starts_at": "2026-09-24T19:00:00+02:00",
  "ends_at": "2026-09-24T20:30:00+02:00",
  "created_at": "2026-09-21T11:04:03+00:00"
}
```

`reference` is 6 to 12 characters of `A-Z0-9`, unique across all reservations, and never changes.

| Case | Response |
|---|---|
| The table is taken for an overlapping interval | 409 `table_unavailable` |
| `starts_at_local` is not on the slot grid | 422 `not_on_slot_grid` |
| Slot outside opening hours, or the reservation would end after `closes` | 422 `outside_opening_hours` |
| `party_size` exceeds the table's `capacity` | 422 `party_exceeds_capacity` |
| `party_size` below 1, or not an integer | 422 `validation_failed` |
| `starts_at_local` is a local time that does not exist (see §9) | 422 `invalid_local_time` |
| Unknown restaurant, unknown table, or the table belongs to another restaurant | 404 `not_found` |

### `GET /reservations`

The caller's reservations, `starts_at` descending, confirmed and cancelled alike.
Return `200` with `{"reservations": [...]}`; each entry has the same shape as the
create response. An empty list is `{"reservations": []}`.

### `GET /reservations/{reference}`

One reservation. **404 if it is not the caller's** — do not leak the existence of other people's
bookings.

### `POST /reservations/{reference}/cancel`

```json
200
{ "reference": "K3P7QW", "status": "cancelled", ... }
```

Frees the table immediately: the next `GET /availability` must offer that slot again.

| Case | Response |
|---|---|
| Already cancelled | 200 with the current state — cancelling twice is not an error |
| Now is within `cancellation_cutoff_minutes` of `starts_at`, or later | 409 `cutoff_passed` |
| Not the caller's reservation | 404 `not_found` |

### `PATCH /reservations/{reference}`

Change the time, the table or the party size. Any subset of `table_id`, `starts_at_local`,
`party_size`. No idempotency key is required here.

Validation is identical to `POST /reservations`, and the same cutoff rule as cancel applies
(409 `cutoff_passed`), measured against the **current** start time. A cancelled reservation is
409 `reservation_cancelled`. A successful amendment releases the old slot and reserves the
new one together. A failed amendment leaves the original booking and its occupancy unchanged.

`reference` and `reservation_id` survive a change.

## 9. Time and DST

Local dates and times follow the restaurant's `timezone`, including daylight-saving transitions.

**Spring forward.** Local times in the skipped hour do not exist. They never appear in
availability, and booking one is 422 `invalid_local_time`.

**Fall back.** Local times in the repeated hour occur twice. **Always resolve to the first
occurrence — the one before the clocks change.** The slot appears once in availability, and the
second occurrence is not bookable.

`reservation_duration_minutes` is **absolute time**, not wall-clock. A 90-minute reservation
starting at 01:30 on a fall-back night ends 90 real minutes later, and its local `ends_at` will
read 02:00, not 03:00.

The transitions that must be handled:

| Zone | Spring forward | Fall back |
|---|---|---|
| `Europe/Berlin` | 2026-03-29, 02:00 → 03:00 | 2026-10-25, 03:00 → 02:00 |
| `America/New_York` | 2026-03-08, 02:00 → 03:00 | 2026-11-01, 02:00 → 01:00 |

Offsets must follow the IANA rules for the specified zone and date.

## 10. Export and import

The service must support `GET /_test/export` and `POST /_test/import`. Like reset, these
are unauthenticated test endpoints.
Exports may contain credentials and session tokens; handle them as private test artifacts.
Return 200 from export with a JSON object containing `track: "tablekeeper"`,
`format_version: 1` and `state` (an implementation-defined JSON object). The state format
is opaque to the caller and must be accepted unchanged by import.

Import takes that entire object and atomically replaces the service's state, returning
204. It must accept an unchanged export produced by this service. No dependency on the
source process, files, volume, port or network address is allowed. Import is replacement,
not merge; repeating it restores the exported state without duplicating anything. Invalid
JSON follows §5; missing fields, wrong track/version or an invalid state give 422
`validation_failed` without changing the destination. Test control calls have a 10-second
timeout. Export is an atomic, read-only snapshot; subsequent source writes do not change it.

Preserve accounts and hashed-password login, existing bearer tokens, fixture configuration,
reservations, references, all completed idempotent request bodies and original responses.
Identities, statuses and timestamps must not be regenerated. Failed request keys remain
reusable. Existing receipts, references, tokens and retries must remain valid after import;
replacing the state with a fresh fixture does not satisfy this requirement. Import removes
all previous destination data and credentials. Reset continues to clear all state, including
imported state. State need not survive an abrupt container restart.

## 11. Atomic reservation moves

A diner may change several bookings in one request.

`POST /reservation-moves` requires authentication and an idempotency key. Body:

```json
{"moves": [{"reference": "BOOK01", "table_id": "t_2"},
           {"reference": "BOOK02", "table_id": "t_1"}]}
```

`moves` contains 1..8 objects with distinct string references. Invalid shape or duplicate
references gives 422 `validation_failed`. Every booking must belong to the caller and the
same restaurant. Unknown/another owner's reference gives 404 `not_found`; different
restaurants give 422 `validation_failed`. No token gives 401.

Each item accepts the ordinary PATCH fields `table_id`, `starts_at_local`, `party_size`;
omitted fields retain their current values and unknown fields are ignored. The booking's
identity, owner and creation time never change. Cancelled bookings give 409
`reservation_cancelled`. Each booking's existing cutoff applies. Non-occupancy errors use
ordinary amendment codes and take precedence in input order, with cutoff errors preceding
other changes for that booking. An overlap among resulting bookings or with an unlisted
booking gives 409 `table_unavailable`. Unchanged listed bookings retain their occupancy.

Either every move commits or nothing changes: occupancy, reservation records and retry
keys. On success return 201 with `{"reservations": [...]}` in input order, including
unchanged items.
Replays return that original response with 200, even after amendments or cancellations.
No-op moves retain all existing values. Export/import preserves successful batch receipts
as well as the resulting bookings. No batch UI is required.



