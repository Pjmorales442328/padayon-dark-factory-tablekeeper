"""Stage 4: closure replans, apply, staleness and effects."""
import datetime as dt, pytest
from harness.concurrent import burst, no_5xx, tally
from kit import *
pytestmark = pytest.mark.s4
TABLES = [{"id": "t_1", "label": "1", "capacity": 2}, {"id": "t_2", "label": "2", "capacity": 4}, {"id": "t_3", "label": "3", "capacity": 6}, {"id": "t_4", "label": "4", "capacity": 4}]
BASE = "/restaurants/r_anker/replans"


def setup(reset, api, extra=()):
    d = date(14); world(reset, api, restaurants=[rest(managers=["u_ada"], tables=TABLES, combinable=[["t_1", "t_2"], ["t_2", "t_3"]]), rest("r_b", managers=["u_ada"])]); return d, ada(api), bob(api)


def closure(d, table="t_2", h1=18, h2=23): return {"table_id": table, "from": instant(d, h1), "to": instant(d, h2)}
def plan(a, d, table="t_2", key=None, **kw): return a.post(BASE, json=closure(d, table, **kw), idempotency_key=key or new_key())
def apply(a, pid, key=None): return a.post(f"{BASE}/{pid}/apply", json={}, idempotency_key=key or new_key())
def rv(a): return plan(a, date(300), "t_1", h1=1, h2=2).json()["restaurant_revision"]


def test_permissions_and_validation(reset, api):
    d, a, b = setup(reset, api)
    assert_error(api().post(BASE, json=closure(d), idempotency_key=new_key()), 401, "unauthenticated"); assert_error(b.post(BASE, json=closure(d), idempotency_key=new_key()), 403, "forbidden")
    assert_error(a.post("/restaurants/nope/replans", json=closure(d), idempotency_key=new_key()), 404, "not_found"); assert_error(a.post(BASE, json=closure(d)), 400, "missing_idempotency_key")
    assert_error(plan(a, d, "t_99"), 404, "not_found")
    for bad in ({**closure(d), "from": instant(d, 20), "to": instant(d, 19)}, {**closure(d), "to": closure(d)["from"]}, {**closure(d), "from": f"{d}T18:00:00"}, {**closure(d), "from": "garbage"}, {"table_id": "t_2"}, {**closure(d), "to": 5}):
        r = a.post(BASE, json=bad, idempotency_key=new_key()); assert r.status_code in (422, 400), (bad, r.text)
        if r.status_code == 422: assert r.json()["error"]["code"] == "validation_failed"


def test_preview_changes_nothing(reset, api):
    d, a, b = setup(reset, api); r = book(b, d, "t_2", "19:00", 4).json(); before = (b.get(f"/reservations/{r['reference']}").json(), b.get(f"/reservations/{r['reference']}/history").json(), avail(a, d, 4).json(), rv(a))
    p = assert_status(plan(a, d), 201).json(); plan(a, d)
    assert (b.get(f"/reservations/{r['reference']}").json(), b.get(f"/reservations/{r['reference']}/history").json(), avail(a, d, 4).json(), rv(a)) == before
    assert p["plan_id"] and p["closure"]["table_id"] == "t_2" and p["assignments"] == [{"reference": r["reference"], "table_ids": ["t_4"], "changed": True}] and p["moved_count"] == 1 and p["unused_seats"] == 0 and p["restaurant_revision"] == 1


def test_no_feasible_plan_is_409_and_changes_nothing(reset, api):
    d, a, b = setup(reset, api); book(b, d, "t_2", "19:00", 4); book(b, d, "t_4", "19:00", 4); book(b, d, "t_3", "19:00", 6); book(b, d, "t_1", "19:00", 2)
    r0 = rv(a); assert_error(plan(a, d), 409, "no_feasible_plan"); assert rv(a) == r0


def test_apply_moves_bookings_and_keeps_everything_else(reset, api):
    d, a, b = setup(reset, api); r = book(b, d, "t_2", "19:00", 4).json(); other = book(b, d, "t_3", "19:00", 6).json(); p = plan(a, d).json(); rev0 = p["restaurant_revision"]
    done = assert_status(apply(a, p["plan_id"]), 201).json(); assert done["plan_id"] == p["plan_id"] and done["restaurant_revision"] == rev0 + 1
    got = {x["reference"]: x for x in done["reservations"]}; assert [x["reference"] for x in done["reservations"]] == sorted([r["reference"], other["reference"]])
    assert got[r["reference"]]["table_ids"] == ["t_4"] and got[r["reference"]]["revision"] == 2 and got[other["reference"]]["revision"] == 1 and got[other["reference"]]["table_ids"] == ["t_3"]
    assert p["assignments"] == sorted([{"reference": r["reference"], "table_ids": ["t_4"], "changed": True}, {"reference": other["reference"], "table_ids": ["t_3"], "changed": False}], key=lambda x: x["reference"])
    now = b.get(f"/reservations/{r['reference']}").json()
    for k in ("reference", "reservation_id", "party_size", "starts_at_local", "starts_at", "ends_at", "created_at", "accepted_terms", "status"): assert now[k] == r[k], k
    assert b.get(f"/reservations/{other['reference']}").json() == other
    es = b.get(f"/reservations/{r['reference']}/history").json()["entries"]; assert [e["event"] for e in es] == ["created", "reassigned"]
    assert es[1]["plan_id"] == p["plan_id"] and es[1]["changes"] == [{"field": "table_ids", "from": ["t_2"], "to": ["t_4"]}] and es[1]["revision"] == 2 and es[1]["accepted_terms"] == r["accepted_terms"]
    assert len(b.get(f"/reservations/{other['reference']}/history").json()["entries"]) == 1 and rv(a) == rev0 + 1


def test_closure_blocks_singles_pairs_creates_amendments_and_explains(reset, api):
    d, a, b = setup(reset, api); assert_status(apply(a, plan(a, d).json()["plan_id"]), 201); s = slot(avail(a, d, 1), "19:00")
    assert "t_2" not in s["available_table_ids"] and all("t_2" not in o["table_ids"] for o in s["available_options"]) and [o["table_ids"] for o in s["available_options"]][-1:] != [["t_1", "t_2"]]
    ex = slot(avail(a, d, 1, explain=True), "19:00")["explain"]; t2 = next(e for e in ex if e["table_id"] == "t_2"); assert t2["available"] is False and {r["rule"]: r["holds"] for r in t2["rules"]}["no_overlap"] is False
    assert_error(book(b, d, "t_2", "19:00", 2), 409, "table_unavailable"); assert_error(book(b, d, ["t_1", "t_2"], "19:00", 5), 409, "table_unavailable")
    ok = book(b, d, "t_1", "19:00", 2).json(); assert_error(b.patch(f"/reservations/{ok['reference']}", json={"table_id": "t_2"}), 409, "table_unavailable")
    assert "t_2" in slot(avail(a, date(15)), "19:00")["available_table_ids"]


def test_closure_applies_only_inside_its_interval(reset, api):
    d, a, b = setup(reset, api); assert_status(apply(a, plan(a, d, h1=19, h2=20).json()["plan_id"]), 201)
    assert_status(book(b, d, "t_2", "20:00", 2), 201); assert_status(book(b, d, "t_2", "21:30", 2), 201)
    for h in ("18:00", "18:30", "19:00", "19:30"): assert_error(book(b, d, "t_2", h, 2), 409, "table_unavailable")


def test_cutoff_does_not_stop_an_operator_repair(reset, api):
    d = date(-2); world(reset, api, restaurants=[rest(managers=["u_ada"], tables=TABLES)]); a = ada(api); b = bob(api); r = book(b, d, "t_2", "19:00", 4).json()
    p = assert_status(plan(a, d), 201).json(); assert p["assignments"][0]["table_ids"] != ["t_2"]; assert assert_status(apply(a, p["plan_id"]), 201).json()["reservations"][0]["status"] == "confirmed"


def test_stale_replayed_and_double_applied(reset, api):
    d, a, b = setup(reset, api); book(b, d, "t_2", "19:00", 4); p1 = plan(a, d).json(); p2 = plan(a, d).json(); k = new_key()
    first = assert_status(apply(a, p1["plan_id"], k), 201).json(); again = apply(a, p1["plan_id"], k); assert again.status_code == 200 and again.json() == first
    assert_error(apply(a, p1["plan_id"]), 409, "plan_already_applied"); assert_error(apply(a, p2["plan_id"]), 409, "stale_plan")
    book(b, d, "t_1", "21:00", 2); assert apply(a, p1["plan_id"], k).status_code == 200


def test_any_intervening_write_makes_a_plan_stale_but_other_restaurant_closures_do_not(reset, api):
    d, a, b = setup(reset, api); book(b, d, "t_2", "19:00", 4)
    for action in (lambda: book(b, d, "t_1", "21:00", 2), lambda: a.post("/restaurants/r_anker/policies", json=fx.policy(d, capacities={"t_1": 2, "t_2": 4, "t_3": 6, "t_4": 4}), idempotency_key=new_key())):
        p = plan(a, d).json(); assert action().status_code == 201; assert_error(apply(a, p["plan_id"]), 409, "stale_plan")
    p = plan(a, d).json(); assert_status(a.post("/restaurants/r_b/replans", json=closure(d, "t_1"), idempotency_key=new_key()), 201); other = a.post("/restaurants/r_b/replans", json=closure(d, "t_1"), idempotency_key=new_key()).json()
    assert_status(apply(a, p["plan_id"]), 201)
    assert_error(a.post(f"/restaurants/r_anker/replans/{other['plan_id']}/apply", json={}, idempotency_key=new_key()), 404, "not_found")
    assert_error(apply(a, "nope"), 404, "not_found"); assert_error(api().post(f"{BASE}/{p['plan_id']}/apply", json={}, idempotency_key=new_key()), 401, "unauthenticated"); assert_error(b.post(f"{BASE}/{p['plan_id']}/apply", json={}, idempotency_key=new_key()), 403, "forbidden")
    assert_error(a.post(f"{BASE}/{p['plan_id']}/apply", json={}), 400, "missing_idempotency_key")


def test_a_failed_apply_changes_nothing(reset, api):
    d, a, b = setup(reset, api); r = book(b, d, "t_2", "19:00", 4).json(); p = plan(a, d).json(); book(b, d, "t_1", "21:00", 2); rev = rv(a)
    assert_error(apply(a, p["plan_id"]), 409, "stale_plan"); assert b.get(f"/reservations/{r['reference']}").json()["table_ids"] == ["t_2"] and len(b.get(f"/reservations/{r['reference']}/history").json()["entries"]) == 1 and rv(a) == rev


def test_concurrent_applications_leave_one_whole_plan(reset, api):
    d, a, b = setup(reset, api); refs = [book(b, d, "t_2", h, 4).json()["reference"] for h in ("18:00", "20:00")]; p = plan(a, d).json()
    rs = burst(lambda i: ada(api).post(f"{BASE}/{p['plan_id']}/apply", json={}, idempotency_key=new_key()), 12); no_5xx(rs); assert tally(rs) == {201: 1, 409: 11}
    assert all(code in ("plan_already_applied", "stale_plan") for code in [r.json()["error"]["code"] for r in rs if r.status_code == 409])
    assert all(b.get(f"/reservations/{x}").json()["table_ids"] != ["t_2"] for x in refs) and all(b.get(f"/reservations/{x}").json()["revision"] == 2 for x in refs)


def test_series_members_keep_flags_dates_and_bump_the_series_once(reset, api):
    d, a, b = setup(reset, api); anc = book(a, d, "t_2", "19:00", 4).json(); s = a.post("/series", json={"anchor_reference": anc["reference"], "count": 3, "interval_weeks": 1}, idempotency_key=new_key()).json(); sid = s["series_id"]
    a.patch(f"/reservations/{s['occurrences'][2]['reference']}", json={"party_size": 3}); before = a.get(f"/series/{sid}").json()
    day2 = (dt.date.fromisoformat(d) + dt.timedelta(days=7)).isoformat(); assert_status(apply(a, plan(a, d, h1=18, h2=23).json()["plan_id"]), 201)
    after = a.get(f"/series/{sid}").json(); assert after["revision"] == before["revision"] + 1 and [o["exception"] for o in after["occurrences"]] == [o["exception"] for o in before["occurrences"]]
    assert [o["reservation"]["starts_at_local"] for o in after["occurrences"]] == [o["reservation"]["starts_at_local"] for o in before["occurrences"]] and after["occurrences"][0]["reservation"]["table_ids"] != ["t_2"]
    assert after["occurrences"][1]["reservation"]["table_ids"] == ["t_2"] and [o["reference"] for o in after["occurrences"]] == [o["reference"] for o in before["occurrences"]]
    assert_status(apply(a, plan(a, day2, h1=18, h2=23).json()["plan_id"]), 201); assert a.get(f"/series/{sid}").json()["revision"] == after["revision"] + 1


def test_replay_of_a_plan_returns_the_original_after_later_changes(reset, api):
    d, a, b = setup(reset, api); r = book(b, d, "t_2", "19:00", 4).json(); p = plan(a, d).json(); k = new_key(); first = apply(a, p["plan_id"], k).json(); b.post(f"/reservations/{r['reference']}/cancel")
    again = apply(a, p["plan_id"], k); assert again.status_code == 200 and again.json() == first


def test_only_confirmed_overlapping_bookings_are_considered(reset, api):
    d, a, b = setup(reset, api); keep = book(b, d, "t_2", "21:30", 2).json(); gone = book(b, d, "t_2", "18:00", 2).json(); b.post(f"/reservations/{gone['reference']}/cancel")
    p = plan(a, d, h1=19, h2=21).json(); assert p["assignments"] == [] and p["moved_count"] == 0 and p["unused_seats"] == 0
    p = plan(a, d, h1=21, h2=23).json(); assert [x["reference"] for x in p["assignments"]] == [keep["reference"]]


def test_half_open_closure_interval(reset, api):
    d, a, b = setup(reset, api); r = b and book(b, d, "t_2", "19:00", 2).json()
    assert plan(a, d, h1=18, h2=19).json()["assignments"] == []
    assert [x["reference"] for x in plan(a, d, h1=18, h2=20).json()["assignments"]] == [r["reference"]]
    late = a.post(BASE, json={"table_id": "t_2", "from": instant(d, 20, minute=30), "to": instant(d, 22)}, idempotency_key=new_key()).json(); assert late["assignments"] == []
    edge = a.post(BASE, json={"table_id": "t_2", "from": instant(d, 20, minute=29), "to": instant(d, 22)}, idempotency_key=new_key()).json(); assert [x["reference"] for x in edge["assignments"]] == [r["reference"]]
