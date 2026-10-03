Design independent stage2 HTTP+browser checks from full specs/ledger, not implementation. Own verification/stage2/** and specified tester notes; never edit prior verification checks. Create one independent check for every197 ledger statement and special clauses. Commit checks before running candidate. Exercise inherited stage1 API and new combined API/UI, browser races/out-of-order/lost responses,375px+desktop accessibility using installed playwright/axe Chromium,maintainability baseline vs stage1. Version-transfer proof must export actual frozen stage1, STOP that source, import independently into stage2,verify accounts/tokens/bookings/references/create+batch receipts plus browser remaining signed-in/pending lost-response same-body/key retry without reload. Source must be stopped BEFORE import. No mocks replacing migration proof. Exports/hash/token artifacts private outside repo/room. Run exact command from kickoff working directory: C:/Users/Prince/Documents/darkfactory/dark-factory-wearedevs/.venv/Scripts/python.exe -m harness run --track tablekeeper --repo C:/Users/Prince/Documents/darkfactory/band-work/result --stage 2 --mode isolated --out C:/Users/Prince/Documents/darkfactory/band-work/checks/<new folder>. Must print claimed stage:2; extra failing stage3 expected. No supplied check edits/skips/deselection. Preserve known pre-run manifest mismatch as visible environment evidence rather than hiding it. Long logs/screenshots outside frozen folders. Send committed findings and exact tested revision,commands/results,harness report path,metrics and screenshot evidence. Builders are under restructure-only gate while you design checks.

Stage2 contract baseline fc078b6fbf6ed532bcd08bb6e1f417e9b47c4cca. Repository C:/Users/Prince/Documents/darkfactory/band-work/result. Frozen prior service C:/Users/Prince/Documents/darkfactory/band-work/result/stage-1, accepted revision344e085d8e3d0629dcc17fc95f22a43efe2a85d2; stage2 copied at stage-2. Handoffs C:/Users/Prince/Documents/darkfactory/band-work/result/handoffs. Spec files requirements-stage-2.md and inherited requirements-stage-1.md there. Kickoff read-only C:/Users/Prince/Documents/darkfactory/dark-factory-wearedevs. Harness interpreter C:/Users/Prince/Documents/darkfactory/dark-factory-wearedevs/.venv/Scripts/python.exe; install nothing. New run folders C:/Users/Prince/Documents/darkfactory/band-work/checks/<new>. Stage2 only; Python; clean Docker build, PORT, no runtime outbound,2CPU/2GiB. Never touch frozen stage1,kickoff/tests/harness,root README.md/FACTORY.md. Commit explicit owned paths using exact seat author handle and local non-personal address on each commit command; never change git config/amend/rebase/squash. Write numbered task notes covering all197 ledger lines before changes/checks, tick and commit results. Commit findings before posting path/revision/one line per finding. Do not ask human,wait approval or recruit agents. Full prior-stage contract remains binding except stage2 changes. Binding empty body/numeric starts_at_local400; restaurant-local table IDs, validated fixtures/import including overlapping confirmed bookings, bad/other-track import422 atomic,no5xx,no-op including reordered pair200,shared-table race exactly1winner.

# Stage 2 ownership and integration contract

Repository C:/Users/Prince/Documents/darkfactory/band-work/result. Frozen source stage-1 accepted344e085; copied destination stage-2 already present. No .git detected in copy; generated cache directories are not runtime source and must never be staged.

Core-builder exclusively owns stage-2/tablekeeper/*.py EXCEPT server.py and web.py. Existing domain modules plus additional modules under that rule. Core implements combined-table model, all API semantics, atomic occupancy/batches/concurrency, validated stage1/stage2 import/export compatibility and preserved original receipts.
Interface-builder exclusively owns stage-2/tablekeeper/server.py, stage-2/tablekeeper/web.py (if needed), stage-2/static/**, stage-2/templates/**, stage-2/Dockerfile, stage-2/RUN.md, stage-2/requirements.txt, stage-2/.dockerignore. Interface implements browser UI, warm visual system, accessible responsive screens, out-of-order search defense, retry identity and uncertain/conflict recovery, browser upgrade continuity, transport/container/runtime assets.
Tester exclusively owns verification/stage2/**, verification/stage2_* (only if needed), and handoffs/tester-*-stage-2*.md. Frozen stage1 verification files remain unchanged; inherited behavior exercised via own stage2 checks or runner configuration. Reviewer owns handoffs/reviewer-*-stage-2*.md. Each builder owns handoffs/<seat>-*-stage-2*.md. Coordinator owns remaining handoff records. No file has two owners.

Integration: preserve tablekeeper.service.Service.dispatch(method,path,query,headers,body)->(status,payload) for JSON API. Lowercase headers, first decoded query values, strict JSON-object parsing (cancel empty-body exception) and error precedence inherited. Service handles every API route and remains thread safe with serializable state. Interface intercepts required GET HTML routes /,/signup,/login,/lookup and own bundled static assets before Service; screen routes return text/html, static correct MIME; API keeps UTF8 JSON/204 behavior. Assets self-contained, no runtime network. UI fetches public restaurant list/detail/availability, token auth, bookings/cancel/lookup. State2 responses expose table_ids always and table_id only singleton except preserved stage1 original receipts. UI must accept those legacy replay responses using retained pending selection + current restaurant labels without inventing success. available_options authoritative for pairs and available_table_ids authoritative for singles. Interface handles auth token/display identity across routes and between-request import. Core's import must preserve tokens and receipts before browser next request. No shared file edits: dependency/contract changes requested to owning builder with evidence.

Restructuring gate: both builders first inspect copied modules/assets, write numbered notes for all197 ledger lines, make a SHORT behavior-preserving restructuring pass (or justified no-op restructuring result if already suitable), commit only explicitly owned copied files+notes, and report exact revision/baseline verification. No new stage2 behavior until coordinator releases gate after both baseline reports. Stage1 never touched. Core may focus a helper split/normalization boundary; interface may prepare separation of transport vs future HTML/static ownership without new UI feature. Source code remains stage1 behavior until release. Tester may independently design/commit requirements-driven checks meanwhile. Reviewer receives each committed checkpoint with full specs/ledger and later exact final candidate.


Complete197-line ledger:
# Stage 2 requirement ledger

Every numbered line requires an independent check. Lines 1–116 inherit stage 1 with explicit stage 2 changes applied below. Complete specs: requirements-stage-1.md and requirements-stage-2.md. Stage 2 spec controls changed behavior. Python required.

1. Implement stage 2 only, with inherited stage 1 API and new browser UI; no existing-product source/documentation/schemas.
2. Complete buildable stage-2 folder copied forward from frozen stage-1, containing Dockerfile, RUN.md and every runtime asset; no nested .git.
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
43. Idempotency applies to POST reservations and POST reservation-moves.
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
62. Create accepts legacy table_id or table_ids (never both), restaurant_id,starts_at_local,party_size and returns documented shape with table_ids plus table_id only for singles.
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
75. Cancel returns 200 full cancelled state and immediately frees occupancy.
76. Repeat cancel returns same current state with 200 even after cutoff.
77. Cancel at/within cutoff or after current start gives 409 cutoff_passed.
78. PATCH accepts table_id or table_ids,starts_at_local,party_size; omitted fields retained; both table selectors invalid; no key required.
79. PATCH uses create validation and current start cutoff; cancelled gives 409 reservation_cancelled.
80. Successful PATCH releases/reserves together; failure preserves booking/occupancy.
81. No-op amendment, including same unordered pair in another order, returns 200 retaining all values.
82. Spring-gap times absent in availability and rejected on create/amend.
83. Fall-fold times resolve first occurrence only, appear once, second occurrence not bookable.
84. Duration arithmetic is absolute time; ends_at follows resulting local offset, including fold example.
85. Berlin 2026-03-29 and 2026-10-25 transitions handled with IANA offsets.
86. New York 2026-03-08 and 2026-11-01 transitions handled with IANA offsets.
87. Export returns 200 object track tablekeeper, format_version integer 1, state object.
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
105. Batch accepts PATCH fields including table_ids, retains omitted values, ignores unknown fields and preserves identity,owner,creation time.
106. Cancelled batch booking gives 409 reservation_cancelled; existing cutoff applies per booking.
107. Batch non-occupancy errors precede any occupancy conflict, in input order; cutoff precedes other changes for that booking.
108. Resulting bookings overlapping each other or unlisted confirmed bookings give 409 table_unavailable; unchanged items retain occupancy.
109. Batch commits all records/occupancy/receipt together or none; swaps supported.
110. Successful batch returns 201 reservations in input order including unchanged items; no-op items retain all values.
111. Batch replay gives 200 original response after changes/cancellation; exported/imported receipts preserve behavior.
112. Kickoff package, supplied tests and harness remain unmodified; install nothing into harness interpreter.
113. Independent checks cover every ledger line and full supplied harness without skips or deselection.
114. Exact --repo stage2 isolated harness command prints claimed stage: 2; expected extra stage3 failure recorded separately.
115. Each seat commits explicit owned files with exact seat author and local non-personal email without shared git setting changes or history rewriting.
116. Coordinator never edits service code/checks or root README.md/FACTORY.md; record stage/rejection start/end and maintainability; never edit frozen stage-1.


## Stage 2 additions and transfer invariants

117. Before any new feature, each builder commits a short behavior-preserving restructuring pass on its exclusively owned copied stage-2 files; stage-1 tree remains byte-identical to frozen 344e085.
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
152. Stage-2 accepts own stage-1 export with source service stopped before destination import; no source process/files/port/network dependence.
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
194. Before import proof stop actual stage1 process/container, then start independent stage2 destination and verify old accounts/tokens/references/create and batch receipts.
195. Run inherited stage1 behavioral checks against stage2, new stage2 API/UI checks and full supplied isolated harness without skipping/deselecting/editing supplied checks.
196. Measure maintainability against frozen stage1 baseline (radon/lizard plus observed limits), record figures and unresolved duplication-tool limits.
197. Final stage2 report includes exact accepted/final revisions,all seat contributions,harness claim/report path,every rejection/change,start/end/time,maintainability and open limitations.


Complete stage2 spec:
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



Complete inherited stage1 spec:
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

