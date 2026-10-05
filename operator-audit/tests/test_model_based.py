"""Stage 4: random operation sequences checked against invariants after every step."""
import datetime as dt, os, random, pytest
from kit import *
pytestmark = pytest.mark.s4
TABLES = [{"id": f"t_{i}", "label": str(i), "capacity": c} for i, c in enumerate([2, 4, 4, 6, 2], 1)]
PAIR_LIST = [["t_1", "t_2"], ["t_2", "t_3"], ["t_3", "t_4"], ["t_4", "t_5"]]
PREVIEW = {"table_id": "t_1", "from": "2001-01-01T00:00:00+00:00", "to": "2001-01-01T01:00:00+00:00"}
DAYS = [date(14 + i) for i in range(3)]
HOURS = ["18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00", "21:30"]
iso = lambda s: dt.datetime.fromisoformat(s)


class Harness:
    def __init__(self, reset, api, seed):
        self.rng = random.Random(seed); self.api = api
        world(reset, api, restaurants=[rest(managers=["u_ada"], tables=TABLES, combinable=PAIR_LIST)]); self.users = [ada(api), bob(api)]; self.closures = []; self.series = []

    def snapshot(self):
        out = {}
        for u in self.users:
            for r in u.get("/reservations").json()["reservations"]: out[r["reference"]] = r
        return out

    def rev(self): return self.users[0].post("/restaurants/r_anker/replans", json=PREVIEW, idempotency_key=new_key()).json()["restaurant_revision"]

    def check(self, label):
        snap = self.snapshot(); occ = []
        for r in snap.values():
            if r["status"] != "confirmed": continue
            for t in r["table_ids"]: occ.append((t, iso(r["starts_at"]), iso(r["ends_at"]), r["reference"]))
        for i in range(len(occ)):
            for j in range(i + 1, len(occ)):
                a, b = occ[i], occ[j]; assert not (a[0] == b[0] and a[1] < b[2] and b[1] < a[2]), (label, "double occupancy", a, b)
        for day in DAYS[:2]:
            ex = avail(self.users[1], day, 1, explain=True).json()["slots"]
            for s in ex:
                st = iso(s["starts_at"]); en = st + dt.timedelta(minutes=90); free = []
                for t in TABLES:
                    taken = any(o[0] == t["id"] and o[1] < en and st < o[2] for o in occ) or any(c[0] == t["id"] and c[1] < en and st < c[2] for c in self.closures)
                    if not taken: free.append(t["id"])
                assert s["available_table_ids"] == free, (label, s["starts_at_local"], s["available_table_ids"], free)
                opt = [o["table_ids"] for o in s["available_options"]]; assert all(all(t in free for t in ids) for ids in opt), (label, "option uses a taken table")
        for ref, r in snap.items():
            h = self.users[0 if ref in {x["reference"] for x in self.users[0].get("/reservations").json()["reservations"]} else 1].get(f"/reservations/{ref}/history").json()["entries"]
            assert [e["seq"] for e in h] == list(range(1, len(h) + 1)) and len(h) == r["revision"], (label, ref, len(h), r["revision"])
        return snap

    def pick(self, snap, status="confirmed"):
        xs = sorted(ref for ref, r in snap.items() if r["status"] == status); return self.rng.choice(xs) if xs else None

    def owner(self, ref, snap):
        return next(u for u in self.users if ref in {x["reference"] for x in u.get("/reservations").json()["reservations"]})

    def step(self, n):
        snap = self.snapshot(); r0 = self.rev(); rng = self.rng; kind = rng.choice(["book"] * 5 + ["cancel", "patch", "patch", "moves", "series", "amend", "replan"]); label = f"step {n} {kind}"; expect_bump = None
        if kind == "book":
            tid = rng.choice([[t["id"]] for t in TABLES] + PAIR_LIST); u = rng.choice(self.users)
            resp = book(u, rng.choice(DAYS), tid if len(tid) > 1 else tid[0], rng.choice(HOURS), rng.randint(1, 8))
        elif kind == "cancel" and (ref := self.pick(snap)):
            resp = self.owner(ref, snap).post(f"/reservations/{ref}/cancel")
        elif kind == "patch" and (ref := self.pick(snap)):
            ch = rng.choice([{"party_size": rng.randint(1, 8)}, {"starts_at_local": at(snap[ref]["starts_at_local"][:10], rng.choice(HOURS))}, {"table_ids": rng.choice(PAIR_LIST)}, {"table_id": rng.choice(TABLES)["id"]}])
            resp = self.owner(ref, snap).patch(f"/reservations/{ref}", json=ch)
        elif kind == "moves" and (ref := self.pick(snap)):
            mine = [x for x in sorted(snap) if snap[x]["status"] == "confirmed" and x in {y["reference"] for y in self.owner(ref, snap).get("/reservations").json()["reservations"]}]; sel = rng.sample(mine, min(len(mine), rng.randint(1, 3)))
            resp = self.owner(ref, snap).post("/reservation-moves", json={"moves": [{"reference": x, "table_id": rng.choice(TABLES)["id"]} for x in sel]}, idempotency_key=new_key())
        elif kind == "series" and (ref := self.pick(snap)):
            resp = self.owner(ref, snap).post("/series", json={"anchor_reference": ref, "count": rng.randint(2, 3), "interval_weeks": rng.randint(1, 2)}, idempotency_key=new_key())
            if resp.status_code == 201: self.series.append((self.owner(ref, snap), resp.json()["series_id"]))
        elif kind == "amend" and self.series:
            u, sid = rng.choice(self.series); cur = u.get(f"/series/{sid}").json()
            resp = u.post(f"/series/{sid}/amend", json={"expected_revision": cur["revision"], "from_index": rng.randrange(len(cur["occurrences"])), "local_time": rng.choice(HOURS)}, idempotency_key=new_key())
        elif kind == "replan":
            day = rng.choice(DAYS); t = rng.choice(TABLES)["id"]; h1 = rng.choice([18, 19, 20]); body_ = {"table_id": t, "from": instant(day, h1), "to": instant(day, h1 + rng.randint(1, 3))}
            p = self.users[0].post("/restaurants/r_anker/replans", json=body_, idempotency_key=new_key()); assert p.status_code in (201, 409), (label, p.text)
            if p.status_code == 409: assert p.json()["error"]["code"] == "no_feasible_plan"; self.check(label); return
            resp = self.users[0].post(f"/restaurants/r_anker/replans/{p.json()['plan_id']}/apply", json={}, idempotency_key=new_key())
            if resp.status_code == 201: self.closures.append((t, iso(body_["from"]), iso(body_["to"]))); expect_bump = 1
        else: return
        assert resp.status_code < 500, (label, resp.text[:200])
        after = self.check(label); r1 = self.rev()
        if resp.status_code >= 400: assert after == snap and r1 == r0, (label, "a rejected request changed state", resp.status_code, resp.text[:120])
        else:
            want = expect_bump if expect_bump is not None else (1 if after != snap else 0); assert r1 - r0 == want, (label, "restaurant revision", r0, r1, want)
            for ref, old in snap.items():
                if ref in after: assert after[ref]["revision"] >= old["revision"], (label, ref)


@pytest.mark.parametrize("seed", range(int(os.environ.get("AUDIT_SEEDS", 16))))
def test_random_sequences_keep_every_invariant(reset, api, seed):
    h = Harness(reset, api, seed)
    for n in range(int(os.environ.get("AUDIT_STEPS", 35))): h.step(n)
