"""Stage 3: recurring reservations."""
import datetime as dt, pytest
from kit import *
pytestmark = pytest.mark.s3


def adopt(c, ref, count=4, weeks=1, key=None, raw_body=None):
    return c.post("/series", json=raw_body or {"anchor_reference": ref, "count": count, "interval_weeks": weeks}, idempotency_key=key or new_key())


def setup(reset, api, tz="Europe/Berlin", **kw):
    d = date(14); world(reset, api, restaurants=[rest(managers=["u_ada"], timezone=tz, **kw)]); a = ada(api)
    return d, a, book(a, d, "t_2", "19:00", 2).json()


def test_series_shape_dates_and_independent_references(reset, api):
    d, a, anchor = setup(reset, api); s = assert_status(adopt(a, anchor["reference"], 4, 2), 201).json()
    assert s["series_id"] and s["revision"] == 1 and s["interval_weeks"] == 2 and [o["index"] for o in s["occurrences"]] == [0, 1, 2, 3]
    assert s["occurrences"][0]["reference"] == anchor["reference"] and s["occurrences"][0]["reservation"] == a.get(f"/reservations/{anchor['reference']}").json() and all(o["exception"] is False for o in s["occurrences"])
    base = dt.date.fromisoformat(d)
    for i, o in enumerate(s["occurrences"]):
        assert o["reservation"]["starts_at_local"] == at((base + dt.timedelta(days=14 * i)).isoformat(), "19:00") and o["reservation"]["party_size"] == 2 and o["reservation"]["table_id"] == "t_2"
    assert len({o["reference"] for o in s["occurrences"]}) == 4 and a.get(f"/series/{s['series_id']}").json() == s
    assert len(a.get("/reservations").json()["reservations"]) == 4
    assert "t_2" not in slot(avail(a, (base + dt.timedelta(days=14)).isoformat()), "19:00")["available_table_ids"]


def test_anchor_is_untouched_and_occurrences_have_histories(reset, api):
    d, a, anchor = setup(reset, api); h = a.get(f"/reservations/{anchor['reference']}/history").json(); s = adopt(a, anchor["reference"], 3).json()
    assert a.get(f"/reservations/{anchor['reference']}").json() == anchor and a.get(f"/reservations/{anchor['reference']}/history").json() == h
    ref1 = s["occurrences"][1]["reference"]; e = a.get(f"/reservations/{ref1}/history").json()["entries"]; assert len(e) == 1 and e[0]["event"] == "created" and a.get(f"/reservations/{ref1}").json()["revision"] == 1


@pytest.mark.parametrize("count,weeks", [(1, 1), (13, 1), (0, 1), (3, 0), (3, 5), ("3", 1), (3, "1"), (True, 1), (3, True), (2.5, 1), (None, 1)])
def test_invalid_count_or_interval_is_422(reset, api, count, weeks):
    d, a, anchor = setup(reset, api); assert_error(adopt(a, anchor["reference"], raw_body={"anchor_reference": anchor["reference"], "count": count, "interval_weeks": weeks}), 422, "validation_failed")


@pytest.mark.parametrize("count,weeks", [(2, 1), (12, 4)])
def test_boundaries_are_accepted(reset, api, count, weeks):
    d, a, anchor = setup(reset, api, tables=[{"id": "t_2", "label": "2", "capacity": 4}]); assert len(assert_status(adopt(a, anchor["reference"], count, weeks), 201).json()["occurrences"]) == count


def test_ownership_state_and_auth(reset, api):
    d, a, anchor = setup(reset, api); ref = anchor["reference"]
    assert_error(api().post("/series", json={"anchor_reference": ref, "count": 3, "interval_weeks": 1}, idempotency_key=new_key()), 401, "unauthenticated")
    assert_error(bob(api).post("/series", json={"anchor_reference": ref, "count": 3, "interval_weeks": 1}, idempotency_key=new_key()), 404, "not_found"); assert_error(adopt(a, "NOPE12"), 404, "not_found")
    assert_error(a.post("/series", json={"anchor_reference": ref, "count": 3, "interval_weeks": 1}), 400, "missing_idempotency_key")
    assert_status(adopt(a, ref), 201); assert_error(adopt(a, ref), 409, "already_in_series")
    r2 = book(a, d, "t_3", "19:00", 2).json()["reference"]; a.post(f"/reservations/{r2}/cancel"); assert_error(adopt(a, r2), 409, "reservation_cancelled")
    past = book(a, date(-2), "t_1", "19:00", 2).json()["reference"]; assert_error(adopt(a, past), 409, "cutoff_passed")


def test_series_is_owner_only(reset, api):
    d, a, anchor = setup(reset, api); s = adopt(a, anchor["reference"]).json(); sid = s["series_id"]
    assert_error(bob(api).get(f"/series/{sid}"), 404, "not_found"); assert_error(api().get(f"/series/{sid}"), 404, "not_found"); assert_error(a.get("/series/nope"), 404, "not_found")


def test_conflict_rejects_the_whole_adoption(reset, api):
    d, a, anchor = setup(reset, api); b = bob(api); blocker = book(b, (dt.date.fromisoformat(d) + dt.timedelta(days=21)).isoformat(), "t_2", "19:30", 2); assert blocker.status_code == 201
    k = new_key(); assert_error(adopt(a, anchor["reference"], 5, 1, key=k), 409, "table_unavailable")
    assert len(a.get("/reservations").json()["reservations"]) == 1 and len(a.get(f"/reservations/{anchor['reference']}/history").json()["entries"]) == 1
    assert "t_2" in slot(avail(a, (dt.date.fromisoformat(d) + dt.timedelta(days=7)).isoformat()), "19:00")["available_table_ids"]
    b.post(f"/reservations/{blocker.json()['reference']}/cancel"); assert_status(adopt(a, anchor["reference"], 5, 1, key=k), 201)


def test_each_occurrence_uses_its_own_date_policy(reset, api):
    d, a, anchor = setup(reset, api); third = (dt.date.fromisoformat(d) + dt.timedelta(days=14)).isoformat()
    assert_status(a.post("/restaurants/r_anker/policies", json=fx.policy(third, reservation_duration_minutes=60), idempotency_key=new_key()), 201)
    s = adopt(a, anchor["reference"], 4).json(); terms = [o["reservation"]["accepted_terms"] for o in s["occurrences"]]
    assert [t["policy_version"] for t in terms] == [0, 0, 1, 1] and s["occurrences"][2]["reservation"]["ends_at"][11:16] == "20:00"
    p4 = (dt.date.fromisoformat(d) + dt.timedelta(days=7)).isoformat()
    d2, a2, anc2 = setup(reset, api); assert_status(a2.post("/restaurants/r_anker/policies", json=fx.policy(third, capacities={"t_1": 2, "t_2": 1, "t_3": 6}), idempotency_key=new_key()), 201)
    assert_error(adopt(a2, anc2["reference"], 4), 422, "party_exceeds_capacity"); assert len(a2.get("/reservations").json()["reservations"]) == 1


def test_dst_keeps_local_clock_time_and_rejects_nonexistent_times(reset, api):
    world(reset, api, restaurants=[rest(timezone="Europe/Berlin", opening_hours=[{"weekday": w, "opens": "00:00", "closes": "06:00"} for w in fx.WEEKDAYS])]); a = ada(api)
    ok = book(a, "2027-03-14", "t_2", "03:30", 2).json(); s = assert_status(adopt(a, ok["reference"], 3), 201).json()
    assert [o["reservation"]["starts_at_local"][-5:] for o in s["occurrences"]] == ["03:30"] * 3 and [o["reservation"]["starts_at"][-6:] for o in s["occurrences"]] == ["+01:00", "+01:00", "+02:00"]
    bad = book(a, "2027-03-21", "t_1", "02:30", 2).json(); n = len(a.get("/reservations").json()["reservations"])
    assert_error(adopt(a, bad["reference"], 2), 422, "invalid_local_time"); assert len(a.get("/reservations").json()["reservations"]) == n


def test_repeated_fall_back_time_uses_the_first_occurrence(reset, api):
    world(reset, api, restaurants=[rest(timezone="Europe/Berlin", opening_hours=[{"weekday": w, "opens": "00:00", "closes": "06:00"} for w in fx.WEEKDAYS])]); a = ada(api)
    anc = book(a, "2027-10-24", "t_2", "02:30", 2).json(); s = assert_status(adopt(a, anc["reference"], 2), 201).json()
    assert s["occurrences"][1]["reservation"]["starts_at_local"] == "2027-10-31T02:30" and s["occurrences"][1]["reservation"]["starts_at"].endswith("+02:00")


def test_exceptions_and_revisions(reset, api):
    d, a, anchor = setup(reset, api); s = adopt(a, anchor["reference"], 4).json(); sid = s["series_id"]; refs = [o["reference"] for o in s["occurrences"]]; rev = lambda: a.get(f"/series/{sid}").json()
    a.patch(f"/reservations/{refs[1]}", json={"party_size": 3}); cur = rev(); assert cur["revision"] == 2 and [o["exception"] for o in cur["occurrences"]] == [False, True, False, False]
    a.patch(f"/reservations/{refs[1]}", json={"party_size": 3}); a.patch(f"/reservations/{refs[2]}", json={"party_size": 9}); assert rev()["revision"] == 2
    a.post(f"/reservations/{refs[2]}/cancel"); cur = rev(); assert cur["revision"] == 3 and cur["occurrences"][2]["exception"] is False and cur["occurrences"][2]["reservation"]["status"] == "cancelled"
    a.post(f"/reservations/{refs[2]}/cancel"); assert rev()["revision"] == 3
    a.post(f"/reservations/{refs[0]}/cancel"); cur = rev(); assert cur["revision"] == 4 and cur["occurrences"][1]["reservation"]["status"] == "confirmed" and cur["occurrences"][3]["reservation"]["status"] == "confirmed"
    assert [o["reference"] for o in cur["occurrences"]] == refs


def test_replay_returns_the_original_and_changes_nothing(reset, api):
    d, a, anchor = setup(reset, api); k = new_key(); s = adopt(a, anchor["reference"], 3, key=k).json(); a.patch(f"/reservations/{s['occurrences'][1]['reference']}", json={"party_size": 3})
    again = adopt(a, anchor["reference"], 3, key=k); assert again.status_code == 200 and again.json() == s
    assert a.get(f"/series/{s['series_id']}").json()["revision"] == 2 and len(a.get("/reservations").json()["reservations"]) == 3


def test_series_with_a_combined_table_anchor(reset, api):
    d = date(14); world(reset, api, restaurants=[rest(combinable=PAIRS)]); a = ada(api); anc = book(a, d, ["t_1", "t_2"], "19:00", 6).json()
    s = assert_status(adopt(a, anc["reference"], 3), 201).json(); assert all(o["reservation"]["table_ids"] == ["t_1", "t_2"] for o in s["occurrences"])
