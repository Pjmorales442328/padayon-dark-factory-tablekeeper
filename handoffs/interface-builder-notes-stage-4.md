# Interface Builder Stage 4 Baseline Notes

Dispatch: `handoffs/dispatch-stage-4-initial.md` at coordinator revision `f609d522c75cceea0b91cecbe568b14b162074f3`. Baseline only; no Stage 4 feature work before coordinator gate release.

Frozen source: Stage 3 `8093f21e49c005e03d770751e0f222a060c224ca`. Interface-owned Stage 4 paths: `stage-4/tablekeeper/server.py`, `web.py`, `static/**`, `templates/**`, `Dockerfile`, `RUN.md`, `requirements.txt`, `.dockerignore`.

Coverage notes below preserve every numbered ledger line. `[ ]` means independent feature evidence is pending; this baseline pass does not assert feature acceptance. Core API/domain lines remain core-owned; independent checks remain tester-owned.

1. [ ] Implement stage3 only, with inherited stages1/2 API/browser and policies/history/recurrence additions; no existing-product source/docs/schemas.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
2. [ ] Complete buildable stage-3 copied from frozenstage-2 contains Dockerfile,RUN.md,every asset;no nested.git/generatedcache committed.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
3. [ ] Python implementation builds from clean checkout and starts with documented command without manual setup.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
4. [ ] Listen on 0.0.0.0, PORT environment variable, default 8080.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
5. [ ] Runtime has no outbound network and requires no external service or Compose.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
6. [ ] Operate within 2 CPUs and 2 GiB.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
7. [ ] Health becomes 200 {status:ok} within 60 seconds when store is usable.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
8. [ ] Support 50 in-flight requests without 5xx.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
9. [ ] Requests finish within 5 seconds; reset and test control calls within 10 seconds.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
10. [ ] State may be ephemeral across container restart.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
11. [ ] JSON responses use application/json; charset=utf-8; timestamps are RFC3339 with explicit offset.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
12. [ ] Unknown body fields and query parameters are ignored.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
13. [ ] Every identifier is an opaque string at most 64 characters, including fixture IDs.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
14. [ ] Reset is unauthenticated, enabled, returns 204 and atomically replaces all state.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
15. [ ] Repeated reset removes prior accounts, sessions, reservations, receipts and imported state.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
16. [ ] Restaurant and table configuration comes only from reset; no creation APIs required.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
17. [ ] Restaurant timezone is valid IANA zone; slot and duration minutes are positive integers; cutoff is nonnegative integer.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
18. [ ] Opening weekdays are mon through sun; missing weekday is closed.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
19. [ ] Opening times are valid HH:MM with closes later on same day; no overnight opening.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
20. [ ] Table capacities are positive integers; booleans never count as integers.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
21. [ ] Seed users log in immediately with supplied password.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
22. [ ] Seed reservations accept table_id or table_ids and default confirmed unless explicit cancelled; preserve validation and supplied identities.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
23. [ ] Past booking dates alone never cause rejection; cutoff still applies.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
24. [ ] Every error uses {error:{code,message}} with specified status/code and human readable message.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
25. [ ] Unparseable JSON, empty request body, non-object request body and ordinary wrong body field types give 400 malformed_request.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
26. [ ] Numeric starts_at_local gives 400 malformed_request.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
27. [ ] Missing required fields and valid-type invalid formats/ranges give 422 validation_failed unless specific code applies.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
28. [ ] Invalid party_size including string, boolean, fraction, zero and negative gives 422 validation_failed.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
29. [ ] starts_at_local strings must be bare YYYY-MM-DDTHH:MM; offsets, Z, seconds and invalid dates give 422 validation_failed.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
30. [ ] Integer query parameters accept plain decimal digits only; 1e9, 4.0 and +4 give 422 validation_failed.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
31. [ ] Required absent/empty idempotency header gives 400 missing_idempotency_key; length over 255 gives 422 validation_failed.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
32. [ ] No request produces a 5xx, including malformed input and concurrent load.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
33. [ ] Signup returns 201 user_id, display_name and token.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
34. [ ] Signup duplicate email gives 409 email_taken.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
35. [ ] Signup password under eight characters and email outside local@domain give 422 validation_failed; fixture passwords are strings without signup minimum.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
36. [ ] Login returns 200 user_id, display_name, token; wrong password/unknown email gives 401 unauthenticated.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
37. [ ] Passwords stored only as password-function hashes, never plaintext.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
38. [ ] Missing/malformed/unknown bearer token gives 401 unauthenticated except booking visibility exception below.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
39. [ ] Tokens never expire and multiple tokens/concurrent sessions remain valid.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
40. [ ] Health, reset, signup, login, restaurant list/detail, availability, export and import are public.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
41. [ ] Other endpoints require bearer authentication; permitted-resource restrictions use specified 403/404 codes.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
42. [ ] Another guest and anonymous caller receive 404 not_found for someone else's booking; do not expose existence.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
43. [ ] Idempotency applies to reservations,reservation-moves,restaurant policy publication and series creation.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
44. [ ] Receipt identity scopes user, method, path and key; different users do not interfere.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
45. [ ] Same key/body on another path is independent and succeeds normally.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
46. [ ] Resolve receipts after JSON-object parsing and authentication, before field/current-resource validation.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
47. [ ] Used key with different JSON body gives 409 idempotency_key_reuse even if new body invalid.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
48. [ ] First successful request returns 201; replay returns 200 identical original JSON response.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
49. [ ] JSON body comparison ignores whitespace and key order and preserves JSON value types.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
50. [ ] Failed 4xx requests do not consume keys; reuse is first use.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
51. [ ] Concurrent identical unused-key writes return exactly one 201 and others 200 identical bodies with one operation.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
52. [ ] Replay after amendment/cancellation returns original response without state changes.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
53. [ ] Restaurant list returns restaurants with id,name,timezone in fixture order.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
54. [ ] Restaurant detail returns full fixture-shaped configuration; unknown gives 404 not_found.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
55. [ ] Availability requires restaurant_id,date,party_size; missing gives 422 validation_failed.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
56. [ ] Availability date is valid local calendar date and party_size is positive integer query.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
57. [ ] Availability response includes restaurant_id,date,timezone and slots.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
58. [ ] Slots step from opening by slot_minutes and fit absolute duration within closing; include single-table availability and available_options.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
59. [ ] Each slot has starts_at_local, offset starts_at, available_table_ids in fixture order.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
60. [ ] Available tables have capacity >= party_size and no overlapping confirmed reservation.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
61. [ ] Fully occupied slots still appear with empty table list; closed day returns empty slots.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
62. [ ] Create supports table_id/table_ids and returns stage2shape plus revision1 and entire selected accepted_terms snapshot; old receipt replays stay original.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
63. [ ] Unknown restaurant/table or table outside restaurant gives 404 not_found.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
64. [ ] Occupancy uses restaurant plus table ID; table IDs may repeat in different restaurants.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
65. [ ] Confirmed occupancy is half-open absolute [start,start+duration); adjacent bookings do not overlap.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
66. [ ] Overlap gives 409 table_unavailable; two racing same-table/time requests have exactly one winner.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
67. [ ] Off-grid start gives 422 not_on_slot_grid measured from opening.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
68. [ ] Outside opening or ending after closing gives 422 outside_opening_hours.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
69. [ ] Party exceeding sum of selected tables' capacities gives 422 party_exceeds_capacity.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
70. [ ] Nonexistent local time gives 422 invalid_local_time.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
71. [ ] Reference is globally unique, 6..12 A-Z0-9 characters, immutable across changes.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
72. [ ] Reservation ID is globally unique, immutable across changes; owner,restaurant and created_at preserved.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
73. [ ] Reservation list includes only caller's confirmed/cancelled bookings, starts_at descending, exact create shapes; empty list supported.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
74. [ ] Reference lookup returns own booking or 404 for absent/invisible booking.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
75. [ ] First cancel returns200 cancelledstate, increments booking revision once, adds one cancelled history entry with emptychanges, frees all occupancy.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
76. [ ] Repeat cancel returns same currentstate200 and changes no booking/series/history counters,even aftercutoff.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
77. [ ] Cancel at/within accepted_terms cutoff or after currentstart409 cutoff_passed.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
78. [ ] PATCH accepts table_id or table_ids,starts_at_local,party_size; omitted fields retained; both table selectors invalid; no key required.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
79. [ ] PATCH checks optional expected_revision stale/type/range first,then current old acceptedcutoff and confirmedstatus,then full resultingfields under resultingdate policy.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
80. [ ] Successful PATCH releases/reserves together; failure preserves booking/occupancy.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
81. [ ] No-op amendment including reversedpair returns200 retaining terms,end,booking+series revisions and history;still confirmed/editable required.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
82. [ ] Spring-gap times absent in availability and rejected on create/amend.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
83. [ ] Fall-fold times resolve first occurrence only, appear once, second occurrence not bookable.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
84. [ ] Duration arithmetic is absolute time; ends_at follows resulting local offset, including fold example.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
85. [ ] Berlin 2026-03-29 and 2026-10-25 transitions handled with IANA offsets.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
86. [ ] New York 2026-03-08 and 2026-11-01 transitions handled with IANA offsets.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
87. [ ] Export returns200 tracktablekeeper,format_version1,stateobject;preserves new policies/terms/history/revisions/series and original receipts.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
88. [ ] Export is atomic read-only detached snapshot unaffected by later source writes.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
89. [ ] Import accepts unchanged service export across independent process/port/files/network; returns 204 atomically.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
90. [ ] Import replaces rather than merges and repeated import does not duplicate data.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
91. [ ] Invalid JSON import uses malformed_request; missing fields, wrong track/version or invalid state give 422 validation_failed without any changes.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
92. [ ] Another track export gives 422 validation_failed and preserves destination state.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
93. [ ] Import preserves accounts/password hashes, token validity, configuration, reservation identities/statuses/timestamps/references.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
94. [ ] Import preserves completed request bodies and original responses for create and moves; failed keys stay reusable.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
95. [ ] Import deletes all previous destination accounts/tokens/data; reset clears imported state.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
96. [ ] Reset fixtures and imported state validate all types, IDs, relations and booking rules, including confirmed overlaps.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
97. [ ] User IDs scope globally; emails uniquely identify accounts; loading validates unique IDs/emails and account field types.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
98. [ ] Restaurant IDs scope globally; loading validates uniqueness, timezone, policy and hours types/ranges.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
99. [ ] Table IDs scope within restaurant only; loading validates uniqueness within restaurant and capacity types/ranges.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
100. [ ] Reservations refer to existing user,restaurant and restaurant-local table; loading validates IDs/references uniqueness and temporal consistency.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
101. [ ] Tokens scope globally, map to existing user; loading validates token types/uniqueness/ownership and preserves multiple sessions.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
102. [ ] Receipts scope user/method/path/key, refer to existing user and valid immutable response snapshots; loading validates bodies/responses and key constraints without requiring equality to subsequently changed bookings.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
103. [ ] Batch moves requires auth/key; moves is 1..8 objects with distinct string references; invalid shape/duplicates give 422 validation_failed.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
104. [ ] Every batch booking belongs to caller and same restaurant; unknown/other owner gives 404; different restaurants gives 422 validation_failed.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
105. [ ] Batch accepts PATCHfields/table_ids/expected_revision;preserves identity/owner/createdtime;changeditems adopt resultingpolicy and increment bookingrevision/history once.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
106. [ ] Cancelled batch booking gives 409 reservation_cancelled; existing cutoff applies per booking.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
107. [ ] Batch non-occupancy errors precede any occupancy conflict, in input order; cutoff precedes other changes for that booking.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
108. [ ] Resulting bookings overlapping each other or unlisted confirmed bookings give 409 table_unavailable; unchanged items retain occupancy.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
109. [ ] Batch commits all records/occupancy/receipt together or none; swaps supported.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
110. [ ] Successbatch201 ininputorder includes unchangeditems;no-op retains every value/revision/history;affected series increment once each for batch.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
111. [ ] Batch replay gives 200 original response after changes/cancellation; exported/imported receipts preserve behavior.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
112. [ ] Kickoff package, supplied tests and harness remain unmodified; install nothing into harness interpreter.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
113. [ ] Independent checks cover every ledger line and full supplied harness without skips or deselection.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
114. [ ] Exact --repo stage3 isolated harness prints claimed stage: 3; expectedextra stage4 failure recorded separately.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
115. [ ] Each seat commits explicit owned files with exact seat author and local non-personal email without shared git setting changes or history rewriting.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
116. [ ] Coordinator never edits servicecode/checks/rootREADME/FACTORY;recordstage/rejectiontimes/metrics;frozenstage1+stage2 unchanged.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
117. [ ] Beforefeatures,each builder commits SHORT behavior-preserving restructuring on copiedownedstage3 files;stage1 unchanged344e085 andstage2 unchanged94e7654.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
118. [ ] Browser routes /, /signup, /login, /lookup return HTML, reachable directly by URL; API remains JSON and all other required screens reachable through UI.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
119. [ ] Browser supports searching, booking and managing reservations, including approved two-table combinations.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
120. [ ] If search A starts before B but completes later, grid, table labels and booking form remain B; stale responses never restore A.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
121. [ ] If another client takes selection after form opens, 409 table_unavailable shows booking-error, refreshes availability, preserves selected form/inputs and shows no confirmation for attempt.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
122. [ ] Lost booking response before/after commit shows nonempty booking-uncertain, no booking-error or new confirmation, retaining unchanged form.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
123. [ ] Unchanged uncertain booking retry sends same body and key; success clears uncertainty/error and displays original reference; confirmed rejection uses booking-error.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
124. [ ] Out-of-order and uncertain-result rules apply to combined bookings too; server remains authoritative and browser never invents cached success.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
125. [ ] No background polling/live updates/cross-tab sync/reload recovery is required.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
126. [ ] Presentation-ready coherent restaurant product uses warm hospitality character with clear search/availability/booking hierarchy.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
127. [ ] Dates, times, party size and seating choices are scannable; combined tables read as intentional seating choices with human labels.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
128. [ ] Consistent typography, spacing, colors, controls and feedback; primary actions obvious.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
129. [ ] Available,unavailable,selected,loading,success,refusal and uncertainty states visually distinct.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
130. [ ] Human-readable restaurant/table labels prominent; technical identifiers shown only when useful.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
131. [ ] 375 CSS-pixel mobile and conventional desktop layouts remain usable without horizontal page scroll.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
132. [ ] Visible input labels, apparent keyboard focus and sufficient text/control contrast throughout.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
133. [ ] Considered empty/loading/error states and consistent navigation across required routes; no custom asset required.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
134. [ ] Signup inputs expose signup-email,signup-password,signup-display-name and signup-submit button.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
135. [ ] Login inputs/button expose login-email,login-password,login-submit.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
136. [ ] auth-error exists only when auth error present; current-user appears every signed-in screen and contains display name; logout-button provided.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
137. [ ] Logout removes active browser auth and all routes reflect signed-out state; account/token server rules remain inherited.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
138. [ ] restaurant-select option values are restaurant IDs; date-input YYYY-MM-DD; party-size-input number; search-button runs search.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
139. [ ] availability-grid holds results; no-slots is shown instead of grid when day has no slots.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
140. [ ] Single cells have slot-{table_id}-{HH:MM} testids and data-available=true exactly when table_id in searched slot available_table_ids; false otherwise.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
141. [ ] Click available single cell opens correct table/time booking form; unavailable click does nothing.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
142. [ ] Signed-out available-cell click produces auth-error or navigates /login; authenticated booking requires server auth.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
143. [ ] booking-form, booking-summary, booking-party-size and booking-submit testids present; summary includes all selected table labels/local start.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
144. [ ] booking-party-size numeric input prefilled with searched party size; booking-error present only on confirmed refusal.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
145. [ ] Keep form after successful booking; unchanged submit repeats original reference with no error/second booking.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
146. [ ] Changing a field creates a new booking request/retry identity; unchanged requests reuse same body/key.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
147. [ ] confirmation and confirmation-reference appear after successful server booking; reference text exactly reference only.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
148. [ ] confirmation-details includes restaurant name,table label(s),local start; confirmation-tables includes every reservation table label.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
149. [ ] Lookup has lookup-reference-input,lookup-submit; found reservation-detail and reservation-status exactly confirmed/cancelled.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
150. [ ] reservation-cancel-button cancels and is absent after cancellation; reservation-error shown for not found/cancel refused.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
151. [ ] reservation-tables on lookup names every selected table; single confirmation/lookup behavior unchanged.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
152. [ ] Stage3 accepts own stage1 andstage2exports,source stopped before import;no process/files/port/networkdependency.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
153. [ ] Pre-upgrade signed-in browser remains signed in after between-request import, without reload/new screen.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
154. [ ] Retained pre-upgrade booking reference works in lookup after import.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
155. [ ] Response-lost pre-upgrade booking retries after import with same body/key and original confirmation; form and pending retry identity survive.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
156. [ ] Restaurant combinable field is ordered list of unordered pairs of that restaurant's table IDs; pair member order preserved for option output/testids.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
157. [ ] Only declared pairs bookable; never triples; combination relation nontransitive.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
158. [ ] Combination capacity equals sum of two distinct member capacities.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
159. [ ] Confirmed combination occupies each member for entire half-open absolute duration, scoped restaurant+table.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
160. [ ] Seed reservations may use table_id or table_ids and status cancelled; confirmed default; cancelled seeds occupy no tables.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
161. [ ] Availability available_table_ids remains singles-only behavior; slots gain available_options.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
162. [ ] available_options lists all eligible free singles first in fixture order, then eligible free pairs in combinable order.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
163. [ ] Pair option table_ids keeps combinable order; capacity sum; every member must be free and capacity>=party size.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
164. [ ] Combination overlapping any occupied member omitted from available_options even if other member free; cross-restaurant identical table IDs independent.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
165. [ ] Create legacy table_id means singleton; table_ids supports singleton or declared pair; sending both gives422 validation_failed.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
166. [ ] Reservation responses always contain table_ids; table_id present exactly for singleton and absent for pair.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
167. [ ] Unlisted pair or more than two tables gives422 combination_not_allowed.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
168. [ ] Duplicate selected table ID gives422 validation_failed; empty selection invalid with422 validation_failed; wrong JSON types follow inherited precedence unless overridden.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
169. [ ] Unknown member or restaurant-local mismatch gives inherited404 not_found; IDs remain string max64.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
170. [ ] Any member occupancy overlap gives409 table_unavailable; party above summed capacity gives422 party_exceeds_capacity.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
171. [ ] PATCH accepts table_ids same rules, atomically releases old members/reserves new members; failure changes none.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
172. [ ] Cancellation frees all members immediately; repeated cancellation identical state200.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
173. [ ] No-op pair order reversal returns200 without changing identities,timestamps,table selection values or occupancy.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
174. [ ] Combination UI cells use slot-{t_a}+{t_b}-{HH:MM} in combinable order and data-available consistent with eligible option.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
175. [ ] Combination cells shown when declared pair available for searched party size; all names use table labels.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
176. [ ] Single cell testids, confirmations and lookup remain compatible with stage1 singles.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
177. [ ] Atomic moves accept table_ids per item with inherited validation/cutoff/order/retry behavior; resulting booking sets cannot overlap any member.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
178. [ ] Batch swap between singles/pairs commits all or nothing; non-occupancy errors precede occupancy; unchanged pair permutations no-op.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
179. [ ] Combination receipt retries preserve original response after amendment/cancel and export/import; body comparison remains JSON-value based.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
180. [ ] Concurrent bookings/amendments/moves/read/reset/export/import are serializable: every read sees consistent before/after state, never partial occupancy.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
181. [ ] Race for any shared member table/time gives exactly one winner; disjoint member sets may both succeed.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
182. [ ] Reset validates combinable shape, distinct member strings, known local tables and duplicate unordered declarations; invalid fixture replacement changes nothing.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
183. [ ] Import validates stage2 combination config/selection/relations/status/type/overlap as create; another track/invalid state422 atomically without5xx.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
184. [ ] Stage1 imported configs without combinable behave as no pairs; imported singleton bookings gain stage2 table_ids while preserving legacy table_id.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
185. [ ] Stage1 successful receipt snapshots retain original JSON responses exactly, even if missing stage2 table_ids; retries remain valid without regenerated identities.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
186. [ ] Loading/transferring user IDs/emails,tokens,restaurant IDs/table-local IDs,reservation IDs/global references and receipt scope retain inherited invariants.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
187. [ ] Pair declaration identifier is unordered restaurant-local member set, not globally scoped table IDs; stored order remains presentation order.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
188. [ ] Confirmed occupancy invariant applies to every member across all reservations; cancelled bookings/receipts cannot create occupancy.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
189. [ ] Import/reset validates reservation owner/configuration/member relationships, unique references/IDs, temporal consistency and receipt-token ownership; validates legacy and new versions before replacement.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
190. [ ] Browser session storage contains token/display identity and pending request key/body; successful stage1 token import remains valid; browser state never substitutes for server response.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
191. [ ] Use supplied interpreter/playwright Chromium/axe tools for browser checks; install nothing into harness interpreter.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
192. [ ] Independent browser checks exercise late searches,409 refresh preserving form,lost responses before/after commit,same-key retry,changed form key,combination equivalents and between-request upgrade.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
193. [ ] Independent checks cover responsive375px/desktop,no horizontal scroll,labels/focus/contrast,distinct states and complete required flows; retain screenshots outside frozen source as reviewable evidence.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
194. [ ] Stop actual frozenstage2 source before independentstage3 importproof;verifyaccounts,tokens,single/pairbookings/references/create+batchreceipts,browser pending recovery.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
195. [ ] Run inheritedstage1/2 behavioral suites againststage3,newstage3 APIchecks and inheritedbrowser,fullisolatedharness withoutsuppliedskips/deselection/editing.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
196. [ ] Measuremaintainability vsfrozenstage2 baseline(rad on/lizard/JS/limits);recordduplicationlimitations.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
197. [ ] Finalstage3report includesaccepted/finalrevision,eachseatcontributions,harnessclaim/report,allrejections/changes,times/metrics/limitations.
   Interface coverage: Inherited Stage 1/2 contract: preserve interface behavior, transport, packaging, and screen states; domain/API validation is core-owned.
198. [ ] Availability capacity and no_overlap rules are independent; available iff both true; available_table_ids retains meaning and stage2 available_options remains inherited.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
199. [ ] explain query optional; accepts only literal true; false,1,empty,True or other values422 validation_failed.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
200. [ ] Without explain,no explanationfields in slots; inherited single/pair slotshape remains except policy-determinedvalues.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
201. [ ] With explain,every slot has full table explanation exactlyonce per restauranttable infixtureorder.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
202. [ ] Each table explanation contains table_id,policy_version,available and rules capacity then no_overlap in fixedorder.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
203. [ ] Both rules always reported independently including bothfalse; availabletrue IDs exactlymatch available_table_ids in sameorder.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
204. [ ] Closed day slots[]; fully unavailable slots remain with complete explanations for everytable.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
205. [ ] Availability/publishedpolicy decisions use selecteddate policygrid,duration,hours,capacities not originalrestaurantdetail.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
206. [ ] GET /reservations/{reference}/history owneronly;unknown,anotherguest,anonymous404;cancelledhistory still readable.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
207. [ ] History entries oldestfirst in seqorder and atorder;seq starts1 increments exactly1 even same-secondwrites.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
208. [ ] History created names tables,starttime,partysize fromnull in fixedorder.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
209. [ ] Single creation/table single-to-singlechanges use table_id historyfield;paircreation uses table_ids fromnull todeclaredorderpair.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
210. [ ] Anychange involving pair uses complete table_ids before/after,declaredcombinationorder;tablesfield precedes starts_at_local then party_size.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
211. [ ] Changedhistory includes ONLY fieldsactuallychanged;one changedentry per realamendment;no-op nohistory.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
212. [ ] Cancelledhistory event has changes[];nothing follows cancellation.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
213. [ ] Idempotentreplay create/batch/series/policy adds nohistory/revisions/termschanges.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
214. [ ] Every historyentry carries resultingbookingrevision and COMPLETE accepted_terms fromthat event;oldentries never acquirelaterterms.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
215. [ ] No new screens required for history/explain/policy/series;existingstage2 browsergrid follows sameauthoritative rules.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
216. [ ] Restaurantfixture manager_user_ids defaults[];onlylistedusers publishpolicy;managerrole neverpermits otherdinerprivatebooking/history/decision/series.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
217. [ ] Policy publication POST /restaurants/{id}/policies requiresauth andkey;unknownrestaurant404,authenticatednonmanager403,no token401.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
218. [ ] Policy publication completebody required effective_from,slot_minutes,reservation_duration_minutes,cancellation_cutoff_minutes,opening_hours,capacities;not patch.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
219. [ ] Policy effective_from validactualYYYY-MM-DD;grid,duration integers1..1440;cutoffinteger0..10080;boolneverinteger.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
220. [ ] Policy openinghours validstage1format,no duplicateweekday.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
221. [ ] Policy capacities names EXACT restaurant-localtableIDs with integer1..100;missing/extra/unknownkeyinvalid.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
222. [ ] Every invalidpolicy422 validation_failed,no versionallocation or any statechange;unknownfieldsignored.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
223. [ ] Policy cannot altertableIDs/labels/timezone/declaredcombinations;unknown unrelatedfieldsignored.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
224. [ ] Successfulpublication201 suppliedrecognizedpolicy pluspolicy_version;versionperrestaurant begins1 increments1onlysuccess;replay200original/noallocation.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
225. [ ] Policy0 originalfixture rules appliesbeforepublishedpolicy;immutable originalconfiguration.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
226. [ ] Select policyby bookingLOCALstartdate:greatest effective_from<=date,tiestakegreatestpolicy_version;publicationordercan differ dateorder.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
227. [ ] Effective dates may be past;new samedatepolicy supersedes futuredecisions only;publication never retroactively editsacceptedbooking/end/history/revisions.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
228. [ ] GET /restaurants/{id}/policies public,policieslist publicationorder,omitpolicy0;unknownrestaurant404.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
229. [ ] Ordinaryrestaurantdetail stays originalfixtureconfiguration includingtablecapacities,hours;availability/decisions selectedpolicy.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
230. [ ] EveryNEW reservationcurrentresponse gains revisioninteger1 atcreation andaccepted_terms entireselectedpolicy excluding effective_from.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
231. [ ] accepted_terms includespolicy_version,grid,duration,cutoff,openinghours,completecapacities;immutable copies,not sharedmutablepolicyrefs.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
232. [ ] Seedbookings revision1 underpolicy0;seedhistory createdor supported consistent default;types/cancelledstates valid.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
233. [ ] Old idempotencyresponses remain EXACT originalJSON including absentnewfields/originalrevision+terms,not currentviews.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
234. [ ] Cancel usesacceptedoldcutoff/currentstart;firstcancel incrementsbookingrevision1;repeatcancel nochange.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
235. [ ] Realamendment checksoldacceptedcutoff first then validates ALL resultingfields under resultingdatepolicy,evenunchangedfields.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
236. [ ] Realamendment atomically replacesacceptedterms/endtime,revision+1,changedhistory+1,occupancy;failedchangesnone.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
237. [ ] No-op retainsacceptedterms,endtime,revision/historyevenifnewpublishedpolicyapplies;stillconfirmed/editablerequired.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
238. [ ] PATCH expected_revision optional;integer>=1 mismatched409 stale_revision BEFOREcutoff/validation;invalidtype/range422.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
239. [ ] Two concurrent realchanges using sameexpected_revision have exactlyonewinner;no-opserialsemantics preservecounter.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
240. [ ] UnrelatedunknownPATCHfields ignored;expected_revision wrongbool/fraction/string/zero/negative422.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
241. [ ] GET /reservations/{reference}/decision returnsreference,currentrevision,accepted_termsincludingcancelled;owneronly404evenanonymous.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
242. [ ] History/decision authvisibility exception resolved404foranonymous;privateexistenceneverleaks.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
243. [ ] POST /series adopts existinganchor occurrence0;requiresauth/key,anchor_reference,count,interval_weeks;unknownfieldsignored.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
244. [ ] Series anchorowned,confirmed,editableunderacceptedcutoff;unknown/otherowner404,cancelled409reservation_cancelled,alreadyadopted409already_in_series.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
245. [ ] Series countinteger2..12 inclanchor,interval_weeksinteger1..4;bool/wrongtype/range422;no token401.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
246. [ ] Occurrence0 isanchor unchangedreference,identity,revision,terms,history,timestamps,originalbookingreceipt.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
247. [ ] Occurrence i localcalendaranchor date+i*interval_weeks*7days,samelocalclock acrossDST;not absoluteweeklyseconds.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
248. [ ] Each generatedoccurrence chooses owndatepolicy,includinggrid/duration/capacity/cutoff/hours;sametable selection/partysizeasanchor.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
249. [ ] Generatedgaplocaltime invalid_local_time rejectsWHOLEadoption;foldresolvesfirstonly.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
250. [ ] Ordinarybookingslot/opening/capacity/occupancyrulesapplyeachgeneratedoccurrence;firstfailingindex determinesordinarycode.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
251. [ ] Failedseries leavesno partialseries,reservations,histories,counters,anchormembership orkeyclaim;samekeymaylater succeed.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
252. [ ] Series success201 series_id,revision1,interval_weeks,occurrences orderedindex0..count-1 eachreference/exceptionfalse/reservationordinaryshape.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
253. [ ] Occurrence references globallydistinct,indicesstable and identities immutablewhenlaterdates/tableschange.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
254. [ ] Occurrences appearordinaryreservationlists,occupytables,own ordinaryhistories.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
255. [ ] GET /series/{series_id} returnscurrentstateshape;owneronly;otherguest/anonymous/unknown404.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
256. [ ] RealindividualPATCH permanentlysetsoccurrenceexceptiontrue andincrementsseriesrevisiononce;no-op/failure leavesunchanged.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
257. [ ] Firstoccurrencecancel incrementsseriesrevisiononce withoutnewexceptionflag;repeatcancelnothing;cancelledretainedoccurrence.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
258. [ ] Cancellinganchor nevercancelsiblings;ordinarycutoff/expectedrevision checksapply.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
259. [ ] Seriesadoption restaurantrevisionchanges deferred correctnessuntilstage4 perorganiser;notstage3acceptanceblocker.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
260. [ ] Series replay200 originalseriesresponse evenafteramend/cancel;changesnocounters/exceptions/history.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
261. [ ] Stage3 accepts ownstage1+stage2exports;importedbookings revision1/policy0terms withhistoryEMPTYoronecreatedentry perorganiser.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
262. [ ] Imported legacyanchor canbeadopted;confirmationlinks/sessions/originalbookingretry remainvalid.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
263. [ ] Stage2 combinedacceptedterms useSUMSELECTEDpolicycapacities,notfixturecapacities.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
264. [ ] Reversedinputpair sameunorderedset no-op;declaredorder histories/responsesnormalizedwithoutnewrevision.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
265. [ ] Batch permoveexpected_revision optional followsPATCHvalidation/stale-before-cutoff;realchange adopts resultingdatepolicy;no-op retainterms/history.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
266. [ ] Batchvalidatesallamendmentrules before occupancy,nonoccupancyerrors precedenceininputorder;failureallrecord/occupancy/terms/history/revision/seriesflags/receipt unchanged.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
267. [ ] Batch everychangedbooking +1revision/+1changedhistory;unchanged nohistory/revision.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
268. [ ] Batch eachAFFECTEDseries+1 revisionTOTALevenmultiplechangedoccurrences;eachchangedoccurrenceexception permanentlytrue.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
269. [ ] Batchfailure/replay no revisions/history/exceptionflags;successful originalbatchreceipt survives laterchanges/import.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
270. [ ] Sharedanchor concurrentseriesadoptions exactlyonewinner;unusedidenticalkeyreplaysone201others200sameoriginalseriesresponse.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
271. [ ] Policyversionidentifier scopedrestaurant;policymappingversion/effectivedate consistent,immutable,currentselectiondeterministic.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
272. [ ] Bookingrevision scopedreservation,integer>=1;historyseqscopedreference,strictsequential/monotonictimestamps/revision/event/changes/termsconsistent.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
273. [ ] Acceptedterms snapshot references validoriginalorselectedimmutablepolicy,fullrestauranttablescapacities,positiveintegerfields and validhours;loading verifiesnot currentpolicyreplacement.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
274. [ ] SeriesID globallyuniqueopaque<=64;ownerexistinguser,occurrenceanchor/reservationownership/restaurantcompatible,count/intervalbounds,indexsequence,distinctrefs and onemembershipperreservation.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
275. [ ] Seriesrevision scopedseries integer>=1,perchange/cancel/batchsemantics;exceptionboolperoccurrence andpermanentafterrealchange.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
276. [ ] Seriesmembership links existingreservations bidirectionally,stableindex/reference;noorphan/doubleadoption;loading/reset/transfer validatesrelationships.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
277. [ ] New policy/series idempotencyrecords scopeduser/method/path/key with parsedbody/originalresponse;invalidrequestsconsumenothing;transferpreservesoriginalresponsesandowners.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
278. [ ] Reset validatesmanager_user_ids array ofdistinctknownuserIDs,restaurantpolicyrules/IDscopes/types includingboolintegerrefusal.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
279. [ ] Resetall newstate policyversions/series/history/receipts cleared;repeatedreset atomic and oldtokensinvalid.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
280. [ ] Import newstate includesimmutablepolicies,acceptedterms,booking/history/seriesrevisions,exceptionflags,membership and everynewpathreceipt;validate beforeatomicreplace.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
281. [ ] Badnewstate (invalidboolintegers,policyversion/date/managerrelations,historyseq/events/terms,seriesownership/index/membership/overlap)422withoutstatechange/no5xx.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
282. [ ] Legacyimport validbookingfields/overlap/type/relationschecked unchanged;conversiondefaultspolicy0/revision1/historyemptyorcreated withoutregeneratingexistingIDs/timestamps/receipts.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
283. [ ] Exportatomicsnapshot read-only detached acrosspolicies/bookinghistory/series/receipts;sourcewritesafterexportdon'tmutateit.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
284. [ ] Failedrequestkeys remain reusable acrossseries/policyfailure andtransfer;resetclearsimportedstate.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
285. [ ] API old/new policies/history/series/receipts concurrency serializable underup-to50load,consistentreads;nopartialcounter/history/terms/membership observed.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
286. [ ] Stoppedstage2->stage3 actualprocess/container proof beforedestinationimport includesoldsessions,single/pairbookings,originalcreate/movereceipts,browserpendingretry;alsoownstage1export accepted.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
287. [ ] Roundtripstage3->independentstage3 carriespolicies,series,history,acceptedterms,currentrevisions andallreplayresponses exactly.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
288. [ ] Independentchecks testpolicyinvalidwritesnoversion,publicationdateorder/samedatetie,perdateacceptanceandimmutability,cutoffoldterms,no-op/historyfixedorder,cancelrepeat.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
289. [ ] Independentchecks testexpectedrevisiontypes/staleerrorprecedence/concurrentwinner,private404guest/anonymousforallnewprivatepaths,explainliteraltrue/allrulesbothfalse.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
290. [ ] Independentchecks testseriesDSTgap/fold/localclock/peroccurrencepolicy/atomicfailurekeyreuse/anchoradoptionrace/occurrenceexceptions/onebatchseriesincrement/transferreceipts.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
291. [ ] Browserallinheritedflows retainnewresponsefields andselectedpolicyavailabilitywithoutnewrequiredscreens;375px/1280px,label/focus/contrast/recoverystates/axe/upgradevisualevidence.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
292. [ ] Record exactstage/rejection start/end,fullcandidate/reviewrevision,harnessclaimedstage3,newfolderreport,perseatresults,maintainabilityvsstage2/openlimits.
   Interface coverage: Inherited Stage 3 contract: preserve selected-policy rendering, accepted response compatibility, and same-tab upgrades; domain/API validation is core-owned.
293. [ ] Preview manager/auth/key permissions and receipt precedence inherited; unknownrestaurant404,nonmanager403,noauth401.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
294. [ ] Requiredtable_id/from/to explicitoffsetinstants from<to; invalidinterval422 validation_failed,unknownlocaltable404.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
295. [ ] Closurehalfopenabsolute restaurant+table scope; considerALLconfirmedrestaurantbookings overlapping interval, othersfixed.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
296. [ ] Support6tables,4declaredpairs,6consideredbookings; larger may422 planning_limit.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
297. [ ] Eachassignment single/declaredpair capacity under ownacceptedterms, retains reference/owner/party/start/end/terms; repairignorescutoff.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
298. [ ] Avoidfixedbookings,otherassignments,appliedclosures,proposedclosure per member forfullbookinginterval.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
299. [ ] Lexicographicallyminimize changedTABLESETcount,totalunusedseats,rankvector inascendingreferenceorder.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
300. [ ] Optionranks0-based singlesfixtureorder then declaredpairorder; reversedpairs sameSET; unusedseats allconsideredcapacity-minusparty.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
301. [ ] Preview201 plan_id,restaurant_revision,closure,allassignments referenceorder/changedbool,moved_count,unused_seats.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
302. [ ] Preview storesONLYplan; no closure/occupancy/history/booking/series/restaurantrevision changes.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
303. [ ] No feasibleplan409 no_feasible_plan changesnothing/consumesnokey.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
304. [ ] Restaurantrevision scope restaurant,integer>=0,boolinvalid; starts0afterreset.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
305. [ ] Newbooking,realPATCH,firstcancel,successfulpolicypublication incrementrestaurantrevision ONCE perrequest.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
306. [ ] Seriesadoption and realatomicbatch eachincrementONCE; all-noopbatch none.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
307. [ ] Failure/noop/preview/replay/read neverincrement; otherrestaurantwrite doesnot stale targetplan.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
308. [ ] Applymanager/auth/key POST replanapply body{}; unknownplan/wrongrestaurant404.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
309. [ ] Interveningtargetrestaurantrevision409 stale_plan atomicallyunchanged.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
310. [ ] Alreadyapplieddifferentkey409 plan_already_applied; successfulsamekeyreplay200 EXACToriginalevenafterchanges.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
311. [ ] Apply201 plan_id,restaurant_revision,reservationsALLconsideredreferenceorder.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
312. [ ] Applyatomicclosure+assignments; everyread before/after,no partialoccupancy.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
313. [ ] Movedbookingrevision+1,reassignedhistory table_ids completebefore/after andplan_id; even singletonrepair uses table_ids.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
314. [ ] Unmovedbooking nohistory/revision; movedterms/times/party/owner/identity preserved.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
315. [ ] Wholeplan restaurantrevision+1 includingzero-moveclosure.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
316. [ ] Closures exclude singles/pairs availability andrealcreates/amends409 table_unavailable; explainno_overlapfalse independentlycapacity.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
317. [ ] Halfopenclosureadjacency/nonlocalrestaurantunaffected; serialapplicationrace exactlyonewinner/newkeys,samekeyone201others200.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
318. [ ] Seriesamend owner/auth/key;unknown/otherowner404,noauth401.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
319. [ ] Requiredexpected_revision integer>=1,from_indexinteger0..count-1,local_time exactHH:MM00:00..23:59;bool/fraction/stringinvalid422.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
320. [ ] Mismatchedseriesrevision409 stale_revision beforeoccurrencecutoff/bookingvalidation;unknownfieldsignored.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
321. [ ] Eligibleindices>=from_index skipscancelled/exceptions,retainothersunchanged.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
322. [ ] UseORIGINALscheduledlocaldate/newclock,currenttables/reference/owner/party; movedindividualdate mustnotbecomeschedule.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
323. [ ] No-op retains terms/end/history/allrevisions; realchangeoldacceptedcutoffthenallresultfieldsselecteddatepolicy.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
324. [ ] DSTgaprejectwhole,foldfirst,absolute duration inherited; nonoccupancyerror indexorder outranks ANYoccupancy.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
325. [ ] Avoidunchangedoccurrences/otherbookings/closures;conflict409 table_unavailable.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
326. [ ] Failureallrecords/terms/history/revisions/flags/receipts unchanged;samekeyreusable.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
327. [ ] Success201 currentseriesorderedstableindices;eachrealchangebookingrevision+1/ordinarychangedhistory.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
328. [ ] Series+restaurantrevision each+1TOTALifanychange;all-noop/emptyeligible succeeds201 unchanged.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
329. [ ] Seriesamend nevermarks/clearsexceptions;replay200originalafterlaterchanges/import.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
330. [ ] Repairpreserves seriesexceptionflags/scheduleddates/terms/identity;eachaffectedseries+1onceifmembersmoved.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
331. [ ] SameexpectedseriesrevisionconcurrentREALchanges exactlyonewins;identicalsamekeyone201others200.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
332. [ ] Resetclearsclosures/plans/appliedflags/newreceipts/restrevision0 andallinheritedstateatomically.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
333. [ ] Closure records validate offsetinterval/localtable/restaurantrelations andconflictconsistency onload/import.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
334. [ ] PlanID globallyuniqueopaque<=64,existingrestaurant,capturedrevisioninteger>=0,detachedsnapshot.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
335. [ ] Planassignments uniqueknownreferences/referenceorder/memberrelations/owntermscapacity/changedflags/objective totals valid.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
336. [ ] Validatehistoric/appliedplan snapshots withoutrequiringequalitywith laterchangedbookings;appliedmarker preventsdoubleapplyaftertransfer.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
337. [ ] Seriesoriginalscheduleddate/index/anchorcalendarrelationships stablethroughmoves/repairs/amend,loadingchecksconsistency.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
338. [ ] Reassignedhistory validplan_id/table_ids/revision/terms;newreceiptuser/method/path/keyscopes andimmutableoriginalresponses validated.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
339. [ ] Nativeexport preserves closures/plans/status/restrevision/scheduleddates/series/history/terms/ALLnewpathreceipts; detachedatomicread.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
340. [ ] Nativeimportallnewtypes/boolintegers/IDs/owners/relations/intervals/snapshots/counters validatedbeforeatomicreplace;bad422unchanged/no5xx,malformedJSON400.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
341. [ ] AcceptownStage1–3exports,preserveoldtokens/refs/revisions/terms/history/receipts;legacyrestaurantrevisiondefaultwell-definedcorrectFROMStage4.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
342. [ ] Importedseriesincludingmoved/cancelled/exceptions supportsamend/repair andoriginalscheduleddates.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
343. [ ] ActualfrozenStage3source stopped/portclosed BEFOREindependentStage4import,no sourcefiles/volume/networkdependence.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
344. [ ] Same-tabStage3->4auth/form/pendingbody/key/originalretry/lookup surviveswithoutreload.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
345. [ ] Existing375px/desktopUIreflectsappliedplanauthoritativeavailability/confirmation/lookup;nonewscreensrequired.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
346. [ ] NativeStage4roundtrip preservesunappliedplanstaleness/applicability,appliederrors,closures,series/history/replayresponses exactly.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
347. [ ] 50mixedconcurrentreads/writes/reset/export/import/preview/apply/seriesamend serializable,no5xx.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
348. [ ] Independentplanningoracle proves everyobjective priority/ownterms/mixedpairs/fixedbookings/closures/adjacency/limits.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
349. [ ] Independentchecks everyrestaurantrevisionwritepath/noop/failure/replay/preview/localstaleness andplan/series/anchor races.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
350. [ ] Exactisolated --repo --stage4harness claimedstage4,allshippedinherited/newchecks no skips/deselection/edits.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.
351. [ ] MeasurePythonradon/lizard/JS/duplicationlimitsagainst frozenStage3;recordstages/rejectionsstart/end/finalacceptedrevisions/contributions/claimpath/openlimits.
   Interface coverage: Stage 4 addition: no new screen is required; existing UI must reflect authoritative applied-plan results. Domain/API behavior is core-owned.

## Baseline inspection

The copied Stage 4 browser already has separate `app.js`, `common.js`, and `grid.js` modules, separate static/template roots, and separate HTTP transport (`server.py`/`web.py`) from the domain service. The UI JavaScript source is already at or below the 300-line file budget (`app.js` 290, `common.js` 50, `grid.js` 42); baseline design is an intentional no-op restructure. Owned `server.py`, `web.py`, all static/template files, Dockerfile, requirements and `.dockerignore` were byte-identical to the Stage 3 copied source before the `RUN.md` correction. Prior baseline measured server/web radon mean CC 2.64/max B(9); Python lizard 181 NLOC, 20 functions, average CCN 2.6, no warnings; JavaScript lizard 359 NLOC, 46 functions, average CCN 2.7, max CCN 14, no warnings. `RUN.md` still named Stage 3 and required a Stage 4-only documentation correction.

## Baseline action/evidence

- Baseline commit: `8e4e161166d4cae499a587acd723d50d8b39a0a2`, author `interface-builder <interface-builder@local.test>`, `2026-10-04T18:04:02+08:00`. It contains this full 351-line ledger checklist, all copied owned Stage 4 interface/transport/package files, and only a Stage 4 tag/path correction in `RUN.md`; runtime code remains byte-identical to Stage 3.
- `git diff --check -- stage-4/RUN.md handoffs/interface-builder-notes-stage-4.md`: passed before commit.
- `docker build --no-cache -t tablekeeper:stage-4 .\stage-4`: passed; log at `C:/Users/Prince/Documents/darkfactory/band-work/checks/stage4-interface-baseline/docker-build.log`.
- Started image as `docker run -d --name tk-stage4-interface-baseline --network none --cpus=2 --memory=2g -e PORT=18084 -p 18084:18084 tablekeeper:stage-4`. Inside the isolated container, `/health`, `/`, `/signup`, `/login`, `/lookup`, `/static/app.js`, and `/static/site.css` all returned 200 with expected JSON/HTML/JavaScript/CSS content types. Container was stopped after the check.
- Inherited Stage 3 browser command: supplied interpreter `verification/stage3/run_stage3.py --part browser --out C:/Users/Prince/Documents/darkfactory/band-work/checks/stage4-interface-baseline/stage3-browser`, with `S3_DIR` set to `stage-4`: 5 run, 5 passed, 0 failures, 0 errors, 0 skips, 0 superseded. This includes the policy grid, late-search, pair-booking, and real stopped-source Stage 2-to-Stage 4 upgrade tests. Log and service logs are in the external checks folder above.
- Maintainability comparison is unchanged from the Stage 3 interface baseline because owned executable files/assets were copied byte-for-byte: Python server/web radon mean CC 2.64, maximum B (9); Python lizard 181 NLOC, 20 functions, average CCN 2.6, zero warnings; JavaScript lizard 359 NLOC, 46 functions, average CCN 2.7, maximum CCN 14, zero warnings. The UI module line counts remain app.js 290, common.js 50, grid.js 42. Duplication-tool limits are inherited from the Stage 3 report; no new duplication metric was available or run for this baseline.
- Stage 4 feature-level ledger evidence remains pending the coordinator's baseline-gate review and feature release.

## Stage 4 feature compatibility in progress

The feature release (`e508389f2f7e7b6dd93dc949d05894b5505eb3d3`) authorizes owned interface work. Existing availability and lookup renderers already read the authoritative slot/reservation response, including `table_ids`, so applied closures and repaired seating appear on the next search or lookup. A successful booking now also performs an owner-authenticated `GET /reservations/{reference}` before rendering confirmation. This lets a same-key retry display current assigned tables after a repair while preserving the original POST receipt and falls back to that confirmed receipt if the follow-up read fails. No manager or series screens are added. Integrated verification awaits the core feature routes and exact candidate.
