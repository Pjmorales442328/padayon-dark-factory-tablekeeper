Resolve the interface-owned finding in committed C:/Users/Prince/Documents/darkfactory/band-work/result/handoffs/core-builder-findings-stage-1-run-1.md at revision 0130c11b286f8b71671e0cdf44e00bd215c365e4. Preserve its evidence; inspect logs, fix your owned transport, and run/commit observed image/start/network/resource and 50-concurrency checks now that Service is complete. Do not edit core/checks. This is rejection R1, opened 2026-10-04T06:55:12+08:00. Report exact fix revision and evidence; do not close on assumptions.
Repository: C:/Users/Prince/Documents/darkfactory/band-work/result
Exact target revision: 0130c11b286f8b71671e0cdf44e00bd215c365e4

Complete original task, ledger, contract and spec:
Implement only transport/deployment files owned in ownership-stage-1.md: server.py, Dockerfile, RUN.md, requirements.txt, .dockerignore. Use shared Service.dispatch contract. No UI. Include IANA tzdata and all runtime dependencies in image. Build/run and check health when core ready; commit and report exact observed outcomes.

Repository: C:/Users/Prince/Documents/darkfactory/band-work/result
Contract baseline revision: 0c0152415ccece9bafbee8acc48fb49a3f6ea842
Requirement file: C:/Users/Prince/Documents/darkfactory/band-work/result/handoffs/requirements-stage-1.md
Handoff folder: C:/Users/Prince/Documents/darkfactory/band-work/result/handoffs
Harness: C:/Users/Prince/Documents/darkfactory/dark-factory-wearedevs/.venv/Scripts/python.exe (install nothing). Kickoff is read-only C:/Users/Prince/Documents/darkfactory/dark-factory-wearedevs. Python required. Stage 1 only; do not edit kickoff, supplied tests, harness, root README.md or FACTORY.md. Every seat commits explicit owned files with seat handle author and local non-personal email on each command; do not change git settings/amend/rebase/squash. Write numbered requirement notes before implementation/check work and commit with result. Commit findings before posting. No human clarification or approval. Report blockers with evidence. Complete task autonomously and send exact revision, changed files, observed commands/results to coordinator.
Binding organiser clarifications: empty request body and numeric starts_at_local give 400 malformed_request. Table IDs scoped to restaurant; reset/import same booking validation including types/overlap; bad import/other track 422 atomically; no 5xx; boolean never integer; no-op change 200; repeat cancel same result; other guest and anonymous 404 for someone else's booking; batch non-occupancy error outranks occupancy; same-table/time race exactly one winner.

# Stage 1 requirement ledger

Every numbered line requires an independent check. Spec is authoritative; dispatch requires Python. Full spec is requirements-stage-1.md.

1. Implement stage 1 only; only HTTP API required; no existing-product source, documentation or schemas.
2. Complete buildable stage-1 folder contains Dockerfile, RUN.md and every runtime asset; no nested .git.
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
22. Seed reservations use create fields plus id, reference, user_id and are confirmed.
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
35. Password under eight characters and email outside local@domain give 422 validation_failed.
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
58. Slots step from opening by slot_minutes and fit absolute duration within closing.
59. Each slot has starts_at_local, offset starts_at, available_table_ids in fixture order.
60. Available tables have capacity >= party_size and no overlapping confirmed reservation.
61. Fully occupied slots still appear with empty table list; closed day returns empty slots.
62. Create requires restaurant_id,table_id,starts_at_local,party_size and returns full documented reservation shape.
63. Unknown restaurant/table or table outside restaurant gives 404 not_found.
64. Occupancy uses restaurant plus table ID; table IDs may repeat in different restaurants.
65. Confirmed occupancy is half-open absolute [start,start+duration); adjacent bookings do not overlap.
66. Overlap gives 409 table_unavailable; two racing same-table/time requests have exactly one winner.
67. Off-grid start gives 422 not_on_slot_grid measured from opening.
68. Outside opening or ending after closing gives 422 outside_opening_hours.
69. Party exceeding table capacity gives 422 party_exceeds_capacity.
70. Nonexistent local time gives 422 invalid_local_time.
71. Reference is globally unique, 6..12 A-Z0-9 characters, immutable across changes.
72. Reservation ID is globally unique, immutable across changes; owner,restaurant and created_at preserved.
73. Reservation list includes only caller's confirmed/cancelled bookings, starts_at descending, exact create shapes; empty list supported.
74. Reference lookup returns own booking or 404 for absent/invisible booking.
75. Cancel returns 200 full cancelled state and immediately frees occupancy.
76. Repeat cancel returns same current state with 200 even after cutoff.
77. Cancel at/within cutoff or after current start gives 409 cutoff_passed.
78. PATCH accepts any subset table_id,starts_at_local,party_size; omitted fields retain values; no key required.
79. PATCH uses create validation and current start cutoff; cancelled gives 409 reservation_cancelled.
80. Successful PATCH releases/reserves together; failure preserves booking/occupancy.
81. No-op amendment returns 200 retaining all values.
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
105. Batch accepts PATCH fields, retains omitted values, ignores unknown fields and preserves identity,owner,creation time.
106. Cancelled batch booking gives 409 reservation_cancelled; existing cutoff applies per booking.
107. Batch non-occupancy errors precede any occupancy conflict, in input order; cutoff precedes other changes for that booking.
108. Resulting bookings overlapping each other or unlisted confirmed bookings give 409 table_unavailable; unchanged items retain occupancy.
109. Batch commits all records/occupancy/receipt together or none; swaps supported.
110. Successful batch returns 201 reservations in input order including unchanged items; no-op items retain all values.
111. Batch replay gives 200 original response after changes/cancellation; exported/imported receipts preserve behavior.
112. Kickoff package, supplied tests and harness remain unmodified; install nothing into harness interpreter.
113. Independent checks cover every ledger line and full supplied harness without skips or deselection.
114. Harness isolated command must print claimed stage: 1; expected extra stage 2 failure recorded separately.
115. Each seat commits explicit owned files with exact seat author and local non-personal email without shared git setting changes or history rewriting.
116. Coordinator never edits service code/checks or root README.md/FACTORY.md; record stage/rejection start/end and maintainability evidence.

# Stage 1 ownership and integration contract

Repository: C:/Users/Prince/Documents/darkfactory/band-work/result
Core-builder owns stage-1/tablekeeper/*.py except server.py, plus stage-1/tablekeeper/__init__.py. Core may add modules only under that ownership. Core implements the complete state/domain API, validation, authentication, atomic operations, DST and state transfer.
Interface-builder owns stage-1/tablekeeper/server.py, stage-1/Dockerfile, stage-1/RUN.md, stage-1/requirements.txt, stage-1/.dockerignore. No browser UI is required.
Tester owns verification/** and handoffs/tester-*.md. Reviewer owns handoffs/reviewer-*.md. Each builder owns handoffs/<seat>-*.md. Coordinator owns other handoff records. No overlapping ownership.

Core exposes tablekeeper.service.Service with dispatch(method: str, path: str, query: dict[str,str], headers: dict[str,str], body: object|None) -> tuple[int, object|None]. Headers arrive lowercased. Server parses JSON into object on POST/PATCH; malformed JSON, empty bodies and non-object bodies produce standard 400 JSON error before dispatch, except cancellation may use no body. Query is decoded, first value retained. Service manages every route including health and all error precedence, and is thread safe across shared instance. Server is a stdlib ThreadingHTTPServer transport listening on PORT and serializes returned JSON with UTF-8 content type; 204 has no body. Core exceptions must not leak; domain errors are returned status/payload. Interface must report unexpected domain exception evidence rather than fabricate success. Core must coordinate any necessary contract adjustment in room before touching another owner's file.

Tester receives requirements/ledger only, designs independent HTTP checks (never imports service implementation), runs full isolated supplied harness with provided interpreter from read-only kickoff working directory, output in a new checks folder each run, collects maintainability with radon/lizard and limits. Tester may inspect implementation only after independent checks are committed for maintainability measurement. No supplied check edits/skips. Reviewer independently checks exact committed revision against requirements and ledger, reports committed findings or exact-revision acceptance; stage freezes only on acceptance with harness claim evidence.



Complete stage 1 spec:
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




