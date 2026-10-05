# Padayon: a five-seat factory that built Tablekeeper through stage 4

Team **Padayon** · WeAreDevelopers x BAND *Dark Factory* · track **tablekeeper**

Five BAND seats, one room, four dispatches. All four stage folders pass their shipped checks from a
clean container in isolated mode (**highest contiguous stage: 4**), with the worst function complexity
held at **9** from stage 1 to stage 4. The only human input was one message per stage.

| | |
|---|---|
| Room | `PADAYON RUN V6`, id `cca42262-ad07-40d0-bf44-60bb57c64f12`, full session in `room.json` |
| Factory time | 4h 49m across four stages (06:35 to 19:30 on 4 Oct, UTC+8, with idle gaps) |
| Spend | $59.19 list-price estimate for the two Claude seats; three Codex seats on a flat plan |
| Real rejections | stage 1 (D1), stage 2 (R1), stage 3 (F1), stage 4 (R1 failures, R2 maintainability) |

## Read this repository in this order

1. `FACTORY.md` — seats, design choices, how to stand the factory up, cost, failures, limitations.
2. `mandates/` — one file per seat; each begins with `Harness:` and `Model:`; none names anything from the track.
3. `room.json` — the unedited full-session export of the room.
4. `handoffs/` — what the seats committed to the room: ledgers, handoffs, findings, per-stage records and final reports.
5. `stage-1/` … `stage-4/` — one buildable service per stage, each with `Dockerfile` and `RUN.md`.
6. `verification/` — the tester's independent checks, written from the spec without reading the service source.

## Run a stage

```sh
docker build -t tablekeeper:stage-4 ./stage-4
docker run --rm --cpus=2 --memory=2g -e PORT=8080 -p 8080:8080 tablekeeper:stage-4
# then open http://localhost:8080/
```

`stage-N/RUN.md` has the exact commands, the browser address and the no-network/2 CPU/2 GiB limits.

## Check it yourself

From the kickoff package: `python -m harness check <this repo> --track tablekeeper` (gates 1, 2 and the
mandate scan), then `python -m harness run --repo <this repo> --all --mode isolated --out <new dir>`.
The final isolated run for this submission is summarised in `FACTORY.md` section 1.

## Who wrote what

Every file under `stage-*/` was written by a seat in the room (git authors: `core-builder`,
`interface-builder`). `handoffs/` and `verification/` come from the coordinator, tester and reviewer.
`README.md`, `FACTORY.md` and `.gitignore` were written by the team lead, outside any stage folder.
