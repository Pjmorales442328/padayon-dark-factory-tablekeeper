"""Stage 4: the seating planner against an independent brute-force oracle on random restaurants."""
import random, pytest
from kit import *
from oracle import best_plan
pytestmark = pytest.mark.s4
START = ["18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00", "21:30"]
mins = lambda hhmm: int(hhmm[:2]) * 60 + int(hhmm[3:])


def scenario(seed):
    rng = random.Random(seed); n = rng.randint(3, 6)
    tables = [{"id": f"t_{i + 1}", "label": str(i + 1), "capacity": rng.choice([2, 2, 4, 4, 6])} for i in range(n)]
    allp = [[tables[i]["id"], tables[j]["id"]] for i in range(n) for j in range(i + 1, n)]; pairs = rng.sample(allp, rng.randint(1, min(4, len(allp))))
    cap = {t["id"]: t["capacity"] for t in tables}; opts = [[t["id"]] for t in tables] + pairs
    placed = []
    for k in range(rng.randint(3, 9)):
        hh = rng.choice(START); party = rng.randint(1, 8); rng.shuffle(opts)
        for o in opts:
            if sum(cap[t] for t in o) < party: continue
            if any(abs(mins(p["hh"]) - mins(hh)) < 90 and set(p["tables"]) & set(o) for p in placed): continue
            placed.append({"hh": hh, "party": party, "tables": tuple(o), "ref": f"RF{len(placed) + 1:04d}"}); break
    f = rng.choice(START[:5]); t = rng.choice([x for x in START if mins(x) > mins(f)] + ["23:00"])
    return tables, pairs, placed, rng.choice(tables)["id"], f, t


def build(reset, api, seed, d, pre=()):
    tables, pairs, placed, ctab, f, t = scenario(seed)
    seeded = [{"id": f"res_{p['ref']}", "reference": p["ref"], "user_id": "u_bob", "restaurant_id": "r_anker", "starts_at_local": at(d, p["hh"]), "party_size": p["party"],
               **({"table_ids": list(p["tables"])} if len(p["tables"]) > 1 else {"table_id": p["tables"][0]})} for p in placed]
    world(reset, api, restaurants=[rest(managers=["u_ada"], tables=tables, combinable=pairs, opening_hours=fx.all_week("17:00", "23:59"))], reservations=seeded)
    bk = [{"ref": p["ref"], "party": p["party"], "start": mins(p["hh"]), "end": mins(p["hh"]) + 90, "tables": p["tables"], "caps": {x["id"]: x["capacity"] for x in tables}} for p in placed]
    return tables, pairs, bk, ctab, f, t


def preview(a, d, ctab, f, t):
    h = lambda s: instant(d, int(s[:2]), minute=int(s[3:]))
    return a.post("/restaurants/r_anker/replans", json={"table_id": ctab, "from": h(f), "to": h(t) if t != "23:00" else instant(d, 23)}, idempotency_key=new_key())


@pytest.mark.parametrize("seed", range(70))
def test_plan_matches_the_oracle(reset, api, seed):
    d = date(14); tables, pairs, bk, ctab, f, t = build(reset, api, seed, d); a = ada(api)
    cons = [b for b in bk if b["start"] < mins(t) and b["end"] > mins(f)]
    if len(cons) > 6: pytest.skip("beyond the stated planning size")
    want = best_plan(tables, pairs, bk, (ctab, mins(f), mins(t)))
    r = preview(a, d, ctab, f, t)
    if want is None: assert_error(r, 409, "no_feasible_plan"); return
    plan = assert_status(r, 201).json(); assigns, moved, unused = want
    assert [(x["reference"], x["table_ids"], x["changed"]) for x in plan["assignments"]] == assigns, plan
    assert plan["moved_count"] == moved and plan["unused_seats"] == unused and plan["closure"]["table_id"] == ctab


@pytest.mark.parametrize("seed", range(100, 118))
def test_applying_a_plan_leaves_exactly_the_planned_state_and_a_second_closure_respects_it(reset, api, seed):
    d = date(14); tables, pairs, bk, ctab, f, t = build(reset, api, seed, d); a = ada(api)
    cons = [b for b in bk if b["start"] < mins(t) and b["end"] > mins(f)]
    r = preview(a, d, ctab, f, t)
    if r.status_code == 409 or len(cons) > 6: pytest.skip("no first plan")
    plan = r.json(); res = assert_status(a.post(f"/restaurants/r_anker/replans/{plan['plan_id']}/apply", json={}, idempotency_key=new_key()), 201).json()
    assert [x["reference"] for x in res["reservations"]] == [x["reference"] for x in plan["assignments"]] and res["restaurant_revision"] == plan["restaurant_revision"] + 1
    now = {b["ref"]: tuple(b["tables"]) for b in bk}; now.update({x["reference"]: tuple(x["table_ids"]) for x in plan["assignments"]})
    for b in bk:
        got = bob(api).get(f"/reservations/{b['ref']}").json(); assert tuple(got["table_ids"]) == now[b["ref"]]
    bk2 = [{**b, "tables": now[b["ref"]]} for b in bk]; ctab2 = next((x["id"] for x in tables if x["id"] != ctab), ctab); f2, t2 = "18:00", "23:00"
    want = best_plan(tables, pairs, bk2, (ctab2, mins(f2), mins(t2)), closures=[(ctab, mins(f), mins(t))])
    r2 = preview(a, d, ctab2, f2, t2)
    if want is None: assert_error(r2, 409, "no_feasible_plan"); return
    p2 = assert_status(r2, 201).json(); assert [(x["reference"], x["table_ids"], x["changed"]) for x in p2["assignments"]] == want[0] and p2["moved_count"] == want[1] and p2["unused_seats"] == want[2]
