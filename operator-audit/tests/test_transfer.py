"""Upgrades: a newer stage must accept exports produced by every older stage (stage 1-4 specs, 'existing clients after an upgrade')."""
import os, httpx, pytest
from kit import *

SOURCES = {int(k): v for k, v in (p.split("=") for p in os.environ.get("AUDIT_SOURCES", "").split(",") if p)}
TARGET = int(os.environ.get("AUDIT_TARGET", "0"))
pytestmark = [pytest.mark.s2, pytest.mark.s3, pytest.mark.s4]
pairs = [(s, TARGET) for s in sorted(SOURCES) if s < TARGET]


def client(url, token=None): return Api(url, token=token)


def populate(src, stage, d):
    """Build realistic history on the old service; return everything a client could still hold."""
    c = client(src); c.post("/_test/reset", json=fx.fixture(users=[fx.ADA], restaurants=[rest(managers=["u_ada"], tables=[{"id": "t_1", "label": "1", "capacity": 2}, {"id": "t_2", "label": "2", "capacity": 4}, {"id": "t_3", "label": "3", "capacity": 6}])]))
    a = c.authenticate(fx.ADA["email"], fx.ADA["password"]); new = c.signup("newbie@example.com", "newbie password", "Newbie").json(); n = client(src, new["token"])
    rec = {"token": a.token, "new": new, "receipts": [], "refs": {}}
    def keep(key, path, body_, resp): rec["receipts"].append((key, path, body_, resp))
    k1 = new_key(); b1 = body(d, "t_2", "19:00", 4); r1 = a.post("/reservations", json=b1, idempotency_key=k1); keep(k1, "/reservations", b1, r1)
    k2 = new_key(); b2 = body(d, "t_3", "19:00", 5); r2 = n.post("/reservations", json=b2, idempotency_key=k2); keep(k2, "/reservations", b2, r2)
    k3 = new_key(); r3 = a.post("/reservations", json=body(d, "t_1", "21:00", 2), idempotency_key=k3); a.post(f"/reservations/{r3.json()['reference']}/cancel")
    rec["failed_key"] = new_key(); assert a.post("/reservations", json=body(d, "t_2", "19:15", 2), idempotency_key=rec["failed_key"]).status_code == 422
    rec["refs"] = {"a": r1.json()["reference"], "n": r2.json()["reference"], "cancelled": r3.json()["reference"]}
    if stage >= 2:
        k4 = new_key(); b4 = body(d, "t_1", "18:00", 2); keep(k4, "/reservations", b4, a.post("/reservations", json=b4, idempotency_key=k4))
    if stage >= 3:
        pk = new_key(); pb = fx.policy(d, reservation_duration_minutes=60); keep(pk, "/restaurants/r_anker/policies", pb, a.post("/restaurants/r_anker/policies", json=pb, idempotency_key=pk))
        anchor = a.post("/reservations", json=body(date(21), "t_2", "19:00", 3), idempotency_key=new_key()).json(); sk = new_key(); sb = {"anchor_reference": anchor["reference"], "count": 3, "interval_weeks": 1}
        sr = a.post("/series", json=sb, idempotency_key=sk); keep(sk, "/series", sb, sr); rec["series"] = sr.json(); rec["anchor"] = anchor["reference"]
        a.patch(f"/reservations/{sr.json()['occurrences'][1]['reference']}", json={"party_size": 2}); a.post(f"/reservations/{sr.json()['occurrences'][2]['reference']}/cancel")
    rec["export"] = httpx.get(src + "/_test/export", timeout=10).json()
    rec["before"] = {k: a.get(f"/reservations/{v}").json() if k != "n" else n.get(f"/reservations/{v}").json() for k, v in rec["refs"].items()}
    return rec


@pytest.fixture(params=pairs, ids=[f"s{s}-to-s{t}" for s, t in pairs])
def upgraded(request, reset, api, base_url):
    s, t = request.param; d = date(14); rec = populate(SOURCES[s], s, d); world(reset, api, users=[fx.BOB])
    assert httpx.post(base_url + "/_test/import", json=rec["export"], timeout=10).status_code == 204
    rec["d"], rec["stage"] = d, s; return rec


def test_sessions_and_logins_survive(upgraded, api):
    assert api(upgraded["token"]).get("/reservations").status_code == 200 and api(upgraded["new"]["token"]).get("/reservations").status_code == 200
    assert_status(api().login("newbie@example.com", "newbie password"), 200); assert_status(api().login(fx.ADA["email"], fx.ADA["password"]), 200); assert api().login(fx.BOB["email"], fx.BOB["password"]).status_code == 401


def test_bookings_keep_identity_and_status(upgraded, api):
    a = api(upgraded["token"]); n = api(upgraded["new"]["token"])
    for k, c in (("a", a), ("n", n), ("cancelled", a)):
        now = c.get(f"/reservations/{upgraded['refs'][k]}").json(); old = upgraded["before"][k]
        for f in ("reference", "reservation_id", "status", "starts_at_local", "starts_at", "ends_at", "party_size", "created_at"): assert now[f] == old[f], (k, f)
        assert now["table_ids"] == [old["table_id"]] if "table_ids" in now else now["table_id"] == old["table_id"]
    assert_error(n.get(f"/reservations/{upgraded['refs']['a']}"), 404, "not_found")


def test_old_receipts_replay_exactly_and_failed_keys_are_reusable(upgraded, api):
    a = api(upgraded["token"]); n = api(upgraded["new"]["token"])
    for key, path, b, resp in upgraded["receipts"]:
        who = n if resp.json().get("reference") == upgraded["refs"]["n"] else a; r = who.post(path, json=b, idempotency_key=key)
        assert r.status_code == 200 and r.json() == resp.json(), (path, r.text[:200])
        assert_error(who.post(path, json={**b, "party_size": 1} if "party_size" in b else {**b, "count": 2}, idempotency_key=key), 409, "idempotency_key_reuse")
    assert_status(a.post("/reservations", json=body(upgraded["d"], "t_1", "21:00", 2), idempotency_key=upgraded["failed_key"]), 201)


def test_occupancy_and_cancellations_carry_over(upgraded, api):
    a = api(upgraded["token"]); d = upgraded["d"]
    assert_error(a.post("/reservations", json=body(d, "t_2", "19:00", 2), idempotency_key=new_key()), 409, "table_unavailable")
    assert "t_1" in slot(avail(a, d), "21:00")["available_table_ids"]; assert_status(a.post(f"/reservations/{upgraded['refs']['a']}/cancel"), 200)
    assert_status(book(a, d, "t_2", "19:00", 2), 201)


def test_new_features_work_on_imported_data(upgraded, api, base_url):
    if upgraded["stage"] >= 3: pytest.skip("covered by the series tests below")
    a = api(upgraded["token"]); d = upgraded["d"]
    h = assert_status(a.get(f"/reservations/{upgraded['refs']['a']}/history"), 200).json() if TARGET >= 3 else None
    if h: assert [e["event"] for e in h["entries"]] == ["created"] and h["entries"][0]["revision"] == 1
    if TARGET >= 3:
        anchor = book(a, date(30), "t_3", "19:00", 3).json(); s = assert_status(a.post("/series", json={"anchor_reference": anchor["reference"], "count": 3, "interval_weeks": 1}, idempotency_key=new_key()), 201).json()
        assert len(s["occurrences"]) == 3
        imp = a.post("/series", json={"anchor_reference": upgraded["refs"]["a"], "count": 2, "interval_weeks": 1}, idempotency_key=new_key()); assert imp.status_code in (201, 409), imp.text


def test_imported_series_and_policies_keep_working(upgraded, api):
    if upgraded["stage"] < 3 or TARGET < 4: pytest.skip("needs a stage 3 source and a stage 4 target")
    a = api(upgraded["token"]); s = upgraded["series"]; cur = a.get(f"/series/{s['series_id']}").json()
    assert cur["revision"] == 3 and [o["exception"] for o in cur["occurrences"]] == [False, True, False] and cur["occurrences"][2]["reservation"]["status"] == "cancelled"
    out = assert_status(a.post(f"/series/{s['series_id']}/amend", json={"expected_revision": 3, "from_index": 0, "local_time": "20:00"}, idempotency_key=new_key()), 201).json()
    assert [o["reservation"]["starts_at_local"][-5:] for o in out["occurrences"]] == ["20:00", "19:00", "19:00"] and out["revision"] == 4
    pols = api().get("/restaurants/r_anker/policies").json()["policies"]; assert [p["policy_version"] for p in pols] == [1] and pols[0]["reservation_duration_minutes"] == 60
    plan = assert_status(a.post("/restaurants/r_anker/replans", json={"table_id": "t_2", "from": instant(date(21), 18), "to": instant(date(21), 23)}, idempotency_key=new_key()), 201).json()
    assert any(x["reference"] == upgraded["anchor"] and x["table_ids"] == ["t_3"] for x in plan["assignments"])
    assert_status(a.post(f"/restaurants/r_anker/replans/{plan['plan_id']}/apply", json={}, idempotency_key=new_key()), 201)


def test_target_can_export_and_reimport_what_it_imported(upgraded, api, base_url):
    e = httpx.get(base_url + "/_test/export", timeout=10).json(); assert httpx.post(base_url + "/_test/import", json=e, timeout=10).status_code == 204
    assert api(upgraded["token"]).get(f"/reservations/{upgraded['refs']['a']}").status_code == 200
