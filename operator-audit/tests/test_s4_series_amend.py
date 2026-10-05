"""Stage 4: amending recurring reservations."""
import datetime as dt, pytest
from harness.concurrent import burst, no_5xx, tally
from kit import *
pytestmark = pytest.mark.s4
PREVIEW = {"table_id": "t_1", "from": "2001-01-01T00:00:00+00:00", "to": "2001-01-01T01:00:00+00:00"}


def setup(reset, api, count=4, **kw):
    d = date(14); world(reset, api, restaurants=[rest(managers=["u_ada"], **kw)]); a = ada(api)
    anc = book(a, d, "t_2", "19:00", 2).json(); s = a.post("/series", json={"anchor_reference": anc["reference"], "count": count, "interval_weeks": 1}, idempotency_key=new_key()).json()
    return d, a, s


def amend(c, s, rev=None, idx=0, t="20:00", key=None, **kw):
    sid = s["series_id"] if isinstance(s, dict) else s
    return c.post(f"/series/{sid}/amend", json={"expected_revision": rev if rev is not None else 1, "from_index": idx, "local_time": t, **kw}, idempotency_key=key or new_key())


def rv(a): return a.post("/restaurants/r_anker/replans", json=PREVIEW, idempotency_key=new_key()).json()["restaurant_revision"]
def hist(a, ref): return a.get(f"/reservations/{ref}/history").json()["entries"]


def test_success_changes_the_clock_time_from_the_index_on(reset, api):
    d, a, s = setup(reset, api); refs = [o["reference"] for o in s["occurrences"]]; before = [o["reservation"] for o in s["occurrences"]]; r0 = rv(a)
    out = assert_status(amend(a, s, 1, 2, "20:00"), 201).json()
    assert out["series_id"] == s["series_id"] and out["revision"] == 2 and [o["reference"] for o in out["occurrences"]] == refs and [o["index"] for o in out["occurrences"]] == [0, 1, 2, 3]
    got = [o["reservation"] for o in out["occurrences"]]
    assert [x["starts_at_local"][-5:] for x in got] == ["19:00", "19:00", "20:00", "20:00"] and [x["starts_at_local"][:10] for x in got] == [x["starts_at_local"][:10] for x in before]
    assert [x["revision"] for x in got] == [1, 1, 2, 2] and [x["ends_at"][11:16] for x in got] == ["20:30", "20:30", "21:30", "21:30"] and all(o["exception"] is False for o in out["occurrences"])
    for x, y in zip(got, before): assert (x["party_size"], x["table_ids"], x["reference"]) == (y["party_size"], y["table_ids"], y["reference"])
    assert [e["event"] for e in hist(a, refs[2])] == ["created", "changed"] and hist(a, refs[2])[1]["changes"] == [{"field": "starts_at_local", "from": before[2]["starts_at_local"], "to": got[2]["starts_at_local"]}]
    assert len(hist(a, refs[0])) == 1 and a.get(f"/series/{s['series_id']}").json() == out and rv(a) == r0 + 1


@pytest.mark.parametrize("patch", [{"expected_revision": 0}, {"expected_revision": -1}, {"expected_revision": "1"}, {"expected_revision": True}, {"expected_revision": 1.5}, {"from_index": -1}, {"from_index": 4}, {"from_index": "0"}, {"from_index": True},
                                   {"from_index": 1.5}, {"local_time": "7:00"}, {"local_time": "24:00"}, {"local_time": "20:00:00"}, {"local_time": "8pm"}, {"local_time": 2000}, {"local_time": "20:60"}])
def test_invalid_input_is_422(reset, api, patch):
    d, a, s = setup(reset, api); b = {"expected_revision": 1, "from_index": 0, "local_time": "20:00", **patch}
    assert_error(a.post(f"/series/{s['series_id']}/amend", json=b, idempotency_key=new_key()), 422, "validation_failed")


def test_missing_fields_are_422_and_unknown_fields_ignored(reset, api):
    d, a, s = setup(reset, api); sid = s["series_id"]
    for k in ("expected_revision", "from_index", "local_time"):
        b = {"expected_revision": 1, "from_index": 0, "local_time": "20:00"}; b.pop(k); assert_error(a.post(f"/series/{sid}/amend", json=b, idempotency_key=new_key()), 422, "validation_failed")
    assert_status(amend(a, s, 1, 0, "20:00", junk=[1]), 201)


def test_auth_ownership_and_key(reset, api):
    d, a, s = setup(reset, api); sid = s["series_id"]
    assert_error(amend(api(), s), 401, "unauthenticated"); assert_error(amend(bob(api), s), 404, "not_found"); assert_error(amend(a, "nope"), 404, "not_found")
    assert_error(a.post(f"/series/{sid}/amend", json={"expected_revision": 1, "from_index": 0, "local_time": "20:00"}), 400, "missing_idempotency_key")


def test_stale_revision_wins_over_booking_validation(reset, api):
    d, a, s = setup(reset, api); assert_error(amend(a, s, 5, 0, "23:30"), 409, "stale_revision"); assert_error(amend(a, s, 5, 0, "19:15"), 409, "stale_revision")


def test_cancelled_and_exception_occurrences_are_skipped(reset, api):
    d, a, s = setup(reset, api, 5); refs = [o["reference"] for o in s["occurrences"]]; a.post(f"/reservations/{refs[1]}/cancel"); a.patch(f"/reservations/{refs[3]}", json={"party_size": 1})
    cur = a.get(f"/series/{s['series_id']}").json(); out = assert_status(amend(a, s, cur["revision"], 0, "20:00"), 201).json(); t = [o["reservation"]["starts_at_local"][-5:] for o in out["occurrences"]]
    assert t == ["20:00", "19:00", "20:00", "19:00", "20:00"] and [o["exception"] for o in out["occurrences"]] == [False, False, False, True, False] and out["occurrences"][1]["reservation"]["status"] == "cancelled"


def test_noop_and_empty_amendments_change_no_revision(reset, api):
    d, a, s = setup(reset, api); r0 = rv(a)
    same = assert_status(amend(a, s, 1, 0, "19:00"), 201).json(); assert same["revision"] == 1 and all(o["reservation"]["revision"] == 1 for o in same["occurrences"]) and rv(a) == r0
    for o in s["occurrences"]: a.post(f"/reservations/{o['reference']}/cancel")
    cur = a.get(f"/series/{s['series_id']}").json(); r1 = rv(a); e = assert_status(amend(a, s, cur["revision"], 0, "20:00"), 201).json(); assert e["revision"] == cur["revision"] and rv(a) == r1
    assert all(len(hist(a, o["reference"])) == 2 for o in s["occurrences"])


def test_mixed_noop_and_real_changes(reset, api):
    d, a, s = setup(reset, api); out = assert_status(amend(a, s, 1, 0, "19:00"), 201).json()
    a.patch(f"/reservations/{s['occurrences'][2]['reference']}", json={"starts_at_local": at((dt.date.fromisoformat(d) + dt.timedelta(days=14)).isoformat(), "20:00")})
    cur = a.get(f"/series/{s['series_id']}").json(); out = assert_status(amend(a, s, cur["revision"], 0, "20:00"), 201).json(); assert [o["reservation"]["revision"] for o in out["occurrences"]] == [2, 2, 2, 2] and out["revision"] == cur["revision"] + 1


@pytest.mark.parametrize("t,code", [("23:30", "outside_opening_hours"), ("19:15", "not_on_slot_grid"), ("06:00", "outside_opening_hours")])
def test_booking_rule_failures_change_nothing_and_the_key_stays_usable(reset, api, t, code):
    d, a, s = setup(reset, api); r0 = rv(a); k = new_key(); assert_error(amend(a, s, 1, 1, t, key=k), 422, code)
    cur = a.get(f"/series/{s['series_id']}").json(); assert cur["revision"] == 1 and all(o["reservation"]["revision"] == 1 for o in cur["occurrences"]) and rv(a) == r0 and len(hist(a, s["occurrences"][2]["reference"])) == 1
    assert_status(amend(a, s, 1, 1, "20:00", key=k), 201)


def test_occupancy_conflict_is_409_and_atomic(reset, api):
    d, a, s = setup(reset, api); b = bob(api); third = (dt.date.fromisoformat(d) + dt.timedelta(days=21)).isoformat(); assert book(b, third, "t_2", "20:30", 2).status_code == 201; r0 = rv(a)
    assert_error(amend(a, s, 1, 0, "20:00"), 409, "table_unavailable"); cur = a.get(f"/series/{s['series_id']}").json()
    assert cur["revision"] == 1 and all(o["reservation"]["starts_at_local"].endswith("19:00") for o in cur["occurrences"]) and rv(a) == r0


def test_non_occupancy_errors_beat_occupancy_in_index_order(reset, api):
    d, a, s = setup(reset, api); b = bob(api); second = (dt.date.fromisoformat(d) + dt.timedelta(days=7)).isoformat(); third = (dt.date.fromisoformat(d) + dt.timedelta(days=14)).isoformat()
    assert book(b, second, "t_2", "20:30", 2).status_code == 201
    assert_status(a.post("/restaurants/r_anker/policies", json=fx.policy(third, opening_hours=fx.all_week("18:00", "20:30")), idempotency_key=new_key()), 201)
    assert_error(amend(a, s, 1, 0, "20:00"), 422, "outside_opening_hours")


def test_each_change_adopts_the_policy_of_its_resulting_date(reset, api):
    d, a, s = setup(reset, api); third = (dt.date.fromisoformat(d) + dt.timedelta(days=14)).isoformat()
    assert_status(a.post("/restaurants/r_anker/policies", json=fx.policy(third, reservation_duration_minutes=60), idempotency_key=new_key()), 201)
    cur = a.get(f"/series/{s['series_id']}").json(); out = assert_status(amend(a, s, cur["revision"], 1, "20:00"), 201).json(); got = [o["reservation"] for o in out["occurrences"]]
    assert [x["accepted_terms"]["policy_version"] for x in got] == [0, 0, 1, 1] and [x["ends_at"][11:16] for x in got] == ["20:30", "21:30", "21:00", "21:00"]


def test_replay_is_original_even_after_edits(reset, api):
    d, a, s = setup(reset, api); k = new_key(); first = amend(a, s, 1, 1, "20:00", key=k).json(); a.post(f"/reservations/{s['occurrences'][1]['reference']}/cancel"); r0 = rv(a)
    again = amend(a, s, 1, 1, "20:00", key=k); assert again.status_code == 200 and again.json() == first and rv(a) == r0
    assert_error(amend(a, s, 1, 1, "21:00", key=k), 409, "idempotency_key_reuse")


def test_amendments_do_not_mark_exceptions_and_individual_patch_after_is_exception(reset, api):
    d, a, s = setup(reset, api); out = amend(a, s, 1, 0, "20:00").json(); assert all(not o["exception"] for o in out["occurrences"])
    a.patch(f"/reservations/{s['occurrences'][1]['reference']}", json={"party_size": 3}); assert a.get(f"/series/{s['series_id']}").json()["occurrences"][1]["exception"] is True


def test_concurrent_amendments_from_one_revision_make_one_change(reset, api):
    d, a, s = setup(reset, api); rs = burst(lambda i: ada(api).post(f"/series/{s['series_id']}/amend", json={"expected_revision": 1, "from_index": 0, "local_time": ["20:00", "20:30", "21:00"][i % 3]}, idempotency_key=new_key()), 12)
    no_5xx(rs); t = tally(rs); assert t == {201: 1, 409: 11}, t
    cur = a.get(f"/series/{s['series_id']}").json(); assert cur["revision"] == 2 and len({o["reservation"]["starts_at_local"][-5:] for o in cur["occurrences"]}) == 1


def test_dst_nonexistent_clock_time_fails_whole_amendment(reset, api):
    world(reset, api, restaurants=[rest(managers=["u_ada"], opening_hours=[{"weekday": w, "opens": "00:00", "closes": "06:00"} for w in fx.WEEKDAYS])]); a = ada(api)
    anc = book(a, "2027-03-21", "t_2", "03:30", 2).json(); s = a.post("/series", json={"anchor_reference": anc["reference"], "count": 3, "interval_weeks": 1}, idempotency_key=new_key()).json()
    assert_error(amend(a, s, 1, 0, "02:30"), 422, "invalid_local_time"); cur = a.get(f"/series/{s['series_id']}").json(); assert cur["revision"] == 1 and all(o["reservation"]["starts_at_local"].endswith("03:30") for o in cur["occurrences"])
    ok = assert_status(amend(a, s, 1, 0, "04:30"), 201).json(); assert [o["reservation"]["starts_at"][-6:] for o in ok["occurrences"]] == ["+01:00", "+02:00", "+02:00"]
