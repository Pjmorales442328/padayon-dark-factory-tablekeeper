"""Stage 3: collective moves under policies, revisions and agreements."""
import datetime as dt, pytest
from kit import *
pytestmark = pytest.mark.s3


def mv(c, moves, key=None): return c.post("/reservation-moves", json={"moves": moves}, idempotency_key=key or new_key())
def entries(c, ref): return c.get(f"/reservations/{ref}/history").json()["entries"]
def rev(c, ref): return c.get(f"/reservations/{ref}").json()["revision"]


def setup(reset, api):
    d = date(14); world(reset, api, restaurants=[rest(managers=["u_ada"])]); a = ada(api)
    r = [book(a, d, t, "19:00", 2).json()["reference"] for t in ("t_1", "t_2", "t_3")]
    return d, a, r


def test_real_changes_add_one_revision_and_one_history_entry_each(reset, api):
    d, a, (r1, r2, r3) = setup(reset, api)
    res = assert_status(mv(a, [{"reference": r1, "table_id": "t_2"}, {"reference": r2, "table_id": "t_1"}, {"reference": r3}]), 201).json()["reservations"]
    assert [x["revision"] for x in res] == [2, 2, 1] and rev(a, r1) == 2 and rev(a, r3) == 1
    assert [e["event"] for e in entries(a, r1)] == ["created", "changed"] and entries(a, r1)[1]["changes"] == [{"field": "table_id", "from": "t_1", "to": "t_2"}]
    assert len(entries(a, r3)) == 1


def test_noop_batch_changes_nothing(reset, api):
    d, a, (r1, r2, r3) = setup(reset, api)
    res = assert_status(mv(a, [{"reference": r1, "table_id": "t_1"}, {"reference": r2, "party_size": 2, "starts_at_local": at(d, "19:00")}]), 201).json()["reservations"]
    assert [x["revision"] for x in res] == [1, 1] and len(entries(a, r1)) == 1 and len(entries(a, r2)) == 1


def test_failed_batch_changes_no_revision_history_or_flag(reset, api):
    d, a, (r1, r2, r3) = setup(reset, api); s = a.post("/series", json={"anchor_reference": r1, "count": 3, "interval_weeks": 1}, idempotency_key=new_key()).json()
    assert_error(mv(a, [{"reference": r1, "party_size": 2, "table_id": "t_2"}, {"reference": r2, "party_size": 99}]), 422, "party_exceeds_capacity")
    assert rev(a, r1) == 1 and a.get(f"/series/{s['series_id']}").json()["revision"] == 1 and all(not o["exception"] for o in a.get(f"/series/{s['series_id']}").json()["occurrences"])


def test_series_revision_moves_once_and_members_become_exceptions(reset, api):
    d, a, (r1, r2, r3) = setup(reset, api); s = a.post("/series", json={"anchor_reference": r1, "count": 4, "interval_weeks": 1}, idempotency_key=new_key()).json(); sid = s["series_id"]
    members = [o["reference"] for o in s["occurrences"]]
    assert_status(mv(a, [{"reference": members[0], "party_size": 1}, {"reference": members[1], "party_size": 1}]), 201)
    cur = a.get(f"/series/{sid}").json(); assert cur["revision"] == 2 and [o["exception"] for o in cur["occurrences"]] == [True, True, False, False]
    assert_status(mv(a, [{"reference": members[2], "party_size": 1}, {"reference": r2}]), 201); assert a.get(f"/series/{sid}").json()["revision"] == 3


def test_replay_changes_nothing(reset, api):
    d, a, (r1, r2, r3) = setup(reset, api); k = new_key(); moves = [{"reference": r1, "table_id": "t_2"}, {"reference": r2, "table_id": "t_1"}]
    first = mv(a, moves, k).json(); again = mv(a, moves, k); assert again.status_code == 200 and again.json() == first and rev(a, r1) == 2 and len(entries(a, r1)) == 2


def test_per_move_expected_revision(reset, api):
    d, a, (r1, r2, r3) = setup(reset, api); a.patch(f"/reservations/{r2}", json={"party_size": 1})
    assert_error(mv(a, [{"reference": r1, "party_size": 1}, {"reference": r2, "party_size": 2, "expected_revision": 1}]), 409, "stale_revision"); assert rev(a, r1) == 1
    assert_status(mv(a, [{"reference": r1, "party_size": 1, "expected_revision": 1}, {"reference": r2, "party_size": 2, "expected_revision": 2}]), 201)
    for bad in (0, "1", True):
        r = mv(a, [{"reference": r1, "party_size": 2, "expected_revision": bad}]); assert r.status_code in (422, 400), (bad, r.text)


def test_a_move_across_dates_adopts_the_target_policy(reset, api):
    d, a, (r1, r2, r3) = setup(reset, api); later = (dt.date.fromisoformat(d) + dt.timedelta(days=7)).isoformat()
    assert_status(a.post("/restaurants/r_anker/policies", json=fx.policy(later, reservation_duration_minutes=120), idempotency_key=new_key()), 201)
    res = assert_status(mv(a, [{"reference": r1, "starts_at_local": at(later, "19:00")}]), 201).json()["reservations"][0]
    assert res["accepted_terms"]["policy_version"] == 1 and res["ends_at"][11:16] == "21:00" and res["revision"] == 2


def test_old_cutoff_applies_to_each_changed_booking(reset, api):
    d = date(); world(reset, api); a = ada(api); old = book(a, date(-2), "t_1", "19:00", 2).json()["reference"]; fut = book(a, d, "t_2", "19:00", 2).json()["reference"]
    assert_error(mv(a, [{"reference": fut, "party_size": 3}, {"reference": old, "party_size": 1}]), 409, "cutoff_passed"); assert rev(a, fut) == 1
