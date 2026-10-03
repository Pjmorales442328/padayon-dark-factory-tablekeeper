# Stage 2 domain/transport contract preparation

Status: preparation only, no new Stage 2 behavior implemented before coordinator gate release.
Repository: C:/Users/Prince/Documents/darkfactory/band-work/result
Dispatch: d4a79d8a0f3b90e8c277e191a94aa37c5099727f
Requirements: handoffs/requirements-stage-1.md and handoffs/requirements-stage-2.md

1. Keep Service.dispatch(method, path, query, headers, body) and serializable shared-instance locking. Interface owns HTML routes and static content, core owns every JSON API route.
2. After release, current reservation views always expose table_ids and expose table_id only for singleton selections. Successful Stage 1 receipt replays retain their original JSON exactly, including legacy responses without table_ids. Interface can use retained pending selection and current restaurant labels for those legacy replies, while the server remains authoritative for confirmation.
3. Availability keeps available_table_ids authoritative for eligible free singles, and adds available_options: eligible singles in fixture order, followed by eligible declared pairs in declaration order, with each pair's table_ids in its declaration order and summed capacity.
4. Configuration without combinable means no pairs, including configuration imported from frozen Stage 1. Pair identities are unordered member sets scoped to their restaurant; declaration order remains presentation order.
5. Create and amendments accept exactly one of table_id/table_ids when supplied. Omitted amendment selectors retain selection. Pair permutations that leave the member set unchanged preserve existing stored values. Any overlap on any selected member conflicts atomically; all times remain absolute half-open intervals.
6. Reset/import use the same typed field and relationship validation as requests, plus identity/session/receipt integrity. Seed status defaults to confirmed and may explicitly be cancelled. Cancelled records have no occupancy.
7. Import preserves Stage 1 token validity, immutable identifiers/references/timestamps and original successful create/batch receipt bodies/responses. State loading validates original snapshots independently from the current amended/cancelled records; migration must not rewrite replay snapshots.
8. Error precedence remains body-object parsing, authentication, receipt/key resolution, endpoint field/resource validation, then occupancy. Batch non-occupancy errors are resolved in input order before any occupancy check; current-start cutoff precedes changed values for each item.

Interface agreement is required before either builder depends on these additions. No transport, deployment, browser, supplied-test, harness or frozen Stage 1 file is owned by core.
