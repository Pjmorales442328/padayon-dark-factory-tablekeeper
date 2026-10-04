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

## Same-tab upgrade evidence

Against Stage 3 service revision `118bff234a10e6548283913b9f0cc3188bfc7a25`, the supplied interpreter ran `checks/stage3-interface-upgrade/upgrade-proof.py`. It started the Stage 2 service as an independent process on port `18444`, created single and pair bookings plus a batch swap receipt, signed in through the Stage 2 browser, and submitted a booking whose server response was deliberately dropped after commit. The export remained in the test controller's memory.

The script stopped the Stage 2 process and verified with `netstat -ano -p tcp` that port `18444` had no listener before starting the independent Stage 3 process on that same port and importing the export. Import returned 204. In the existing browser tab, without navigation or reload, the account header, form values and session-storage pending body/key remained; an unchanged retry returned the original Stage 2 reference with HTTP 200 and removed the uncertainty state. The pre-upgrade single and pair references remained visible with the old token, and the successful Stage 2 single, pair and batch-move receipts replayed with their exact original response objects. Pair lookup showed both human table labels. No page errors or horizontal overflow occurred at 375px.

Logs, script and screenshot are outside the repository at `C:/Users/Prince/Documents/darkfactory/band-work/checks/stage3-interface-upgrade/`. The export itself was never written to disk. This completes the interface compatibility work assigned here; it is not a full Stage 3 acceptance claim.

## R1 finding F1: legacy policy-route fallback

At R1 candidate `118bff234a10e6548283913b9f0cc3188bfc7a25`, the parallel policy fetch made availability search fail against Stage 1/2 services that do not implement `GET /restaurants/{id}/policies`. `stage-3/static/app.js` now treats only a 404 from that optional route as an empty published-policy list; other policy-fetch errors still fail the search. The grid consequently uses the restaurant's original fixture configuration (policy 0) while Stage 2 availability options remain authoritative.

The supplied-interpreter command `C:\Users\Prince\Documents\darkfactory\dark-factory-wearedevs\.venv\Scripts\python.exe C:\Users\Prince\Documents\darkfactory\band-work\checks\stage3-interface-upgrade\upgrade-proof.py` passed. It started the Stage 2 source, completed search and single/pair booking plus batch-move setup, stopped the source and confirmed port `18444` had no listener before Stage 3 import. In the same tab without reload, auth, form and pending key/body survived; the unchanged request replayed its original response with 200. Old references and create/move receipts remained valid. The script reported no page errors or horizontal overflow at 375px. Logs and `same-tab-recovered-375.png` are outside the repository in `C:/Users/Prince/Documents/darkfactory/band-work/checks/stage3-interface-upgrade/`.

The fix is limited to the optional legacy policy route behavior; no frozen Stage 1/2 source or tests were changed. This resolves interface finding F1 for integrated review and does not claim overall Stage 3 acceptance.

### Post-commit R1 rerun

After commit `8093f21e49c005e03d770751e0f222a060c224ca`, both upgrade checks passed:

- Independent committed browser check: supplied interpreter `verification/stage3/run_stage3.py --part browser -k upgrade --out C:/Users/Prince/Documents/darkfactory/band-work/checks/stage3-r1-f1-recheck` reported `ran 1, failed 0, errors 0, skipped 0, superseded-by-stage-3 0`.
- Focused stopped-source proof: supplied interpreter ran `C:/Users/Prince/Documents/darkfactory/band-work/checks/stage3-interface-upgrade/upgrade-proof.py`, exit 0, reporting that Stage 2 stopped with port closure confirmed before Stage 3 import and same-tab auth/form/key/body, original receipt retry, references and batch receipt all survived.

The service and interface paths used by these runs (`stage-3/static/app.js`, `stage-3/static/grid.js`, `stage-3/tablekeeper/**`, `stage-3/templates/**`) compare unchanged with commit `8093f21e`; later review/checkpoint commits did not alter the tested application files. Evidence logs and screenshot artifacts remain outside the repository under `checks/stage3-r1-f1-recheck/` and `checks/stage3-interface-upgrade/`.
