# Interface Builder Stage 3 Feature Compatibility Checkpoint

Coordinator released the feature gate at `2026-10-04T16:31:03+08:00`. This checkpoint follows the interface baseline commit `d06e9bc83013e6fda666477ff863aa19ae8c25e8`.

## Change

The grid previously used original fixture capacities to decide whether to display a combined-table cell and what capacity to show. Stage 3 policies can change capacities by the reservation's local start date. The search now reads the public policy list and selects the applicable policy by greatest `effective_from`, breaking same-date ties with the greatest `policy_version`. The grid uses those selected capacities for single/pair capacity labels and pair eligibility. Availability itself remains API-authoritative: single cells use `available_table_ids`; pair cells use `available_options`.

Only `stage-3/static/app.js` and `stage-3/static/grid.js` were changed for this checkpoint. No service, test, frozen-stage, or deployment files were changed.

## Observed checks

- `node --check stage-3/static/app.js` and `node --check stage-3/static/grid.js`: passed.
- `git diff --check -- stage-3/static/app.js stage-3/static/grid.js`: passed.
- Against the running Stage 3 service on port `18443`, reset a fixture with a two-table combination, published two policies with the same effective date and capacities `2+2` then `4+4`, and confirmed the API selected policy version 2. The supplied interpreter's Playwright Chromium browser at 375px showed the available pair, correct human labels and capacity 8; booking rendered its confirmation and lookup correctly when the create response included `revision: 1` and `accepted_terms.policy_version: 2`. There were no page errors or horizontal overflow.
- Reset and published a date-effective policy with pair capacity 4 for a searched party size of 7. The browser omitted the pair cell while retaining the unavailable single cells, as required.
- Browser scripts and screenshots are outside the repository: `C:/Users/Prince/Documents/darkfactory/band-work/checks/stage3-interface-policy-smoke/`.

The default Playwright browser install was absent; I used the supplied Chromium 1228 executable recorded in the baseline evidence. Early reset attempts used an invalid fixture shape while the core files were still being copied forward; the corrected fixture and checks passed. No browser package or runtime dependency was installed.

## Remaining integration evidence

The full-candidate same-tab Stage 2-to-Stage 3 export/import test remains pending. The core service implementation is still changing in the shared worktree; I will run the source-stop, port-closure, import, retained-session and same-key retry proof against its committed candidate before completing the interface task. This report does not claim full Stage 3 acceptance.
