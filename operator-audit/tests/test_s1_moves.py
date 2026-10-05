"""Stage 1 §11: atomic reservation moves."""
import pytest
from kit import *
pytestmark = pytest.mark.s1

def mv(c, moves, key=None, **kw): return c.post("/reservation-moves", json={"moves": moves}, idempotency_key=key or new_key(), **kw)
def two(reset, api, **kw):
    d = date(); world(reset, api, **kw); a = ada(api); r1 = book(a, d, "t_2", "19:00", 2).json()["reference"]; r2 = book(a, d, "t_3", "19:00", 2).json()["reference"]; return d, a, r1, r2

def test_swap_two_bookings_atomically(reset, api):
    d, a, r1, r2 = two(reset, api); r = assert_status(mv(a, [{"reference": r1, "table_id": "t_3"}, {"reference": r2, "table_id": "t_2"}]), 201).json()
    assert [x["reference"] for x in r["reservations"]] == [r1, r2] and [x["table_id"] for x in r["reservations"]] == ["t_3", "t_2"]
    assert a.get(f"/reservations/{r1}").json()["table_id"] == "t_3"

def test_batch_with_one_conflict_changes_nothing_and_key_is_reusable(reset, api):
    d, a, r1, r2 = two(reset, api); book(bob(api), d, "t_1", "19:00", 2); k = new_key()
    assert_error(mv(a, [{"reference": r1, "table_id": "t_3"}, {"reference": r2, "table_id": "t_1"}], key=k), 409, "table_unavailable")
    assert a.get(f"/reservations/{r1}").json()["table_id"] == "t_2" and a.get(f"/reservations/{r2}").json()["table_id"] == "t_3"
    assert_status(mv(a, [{"reference": r1, "party_size": 2}], key=k), 201)

def test_overlap_between_resulting_bookings_is_409(reset, api):
    d, a, r1, r2 = two(reset, api); assert_error(mv(a, [{"reference": r1, "table_id": "t_3"}]), 409, "table_unavailable")
    assert_error(mv(a, [{"reference": r1, "table_id": "t_1"}, {"reference": r2, "table_id": "t_1"}]), 409, "table_unavailable")

@pytest.mark.parametrize("moves", [[], "x", None, {"reference": "A"}, [{"reference": 5}], [{}], [None], [{"reference": "A"}, {"reference": "A"}], [{"reference": f"R{i}"} for i in range(9)]])
def test_invalid_shapes_are_422(reset, api, moves):
    world(reset, api); body_ = {"moves": moves} if moves is not None else {}
    assert_error(ada(api).post("/reservation-moves", json=body_, idempotency_key=new_key()), 422, "validation_failed")

def test_eight_moves_are_allowed(reset, api):
    d = date(); world(reset, api, restaurants=[rest(tables=[{"id": f"t{i}", "label": str(i), "capacity": 4} for i in range(16)])]); a = ada(api)
    refs = [book(a, d, f"t{i}", "19:00").json()["reference"] for i in range(8)]
    r = assert_status(mv(a, [{"reference": x, "table_id": f"t{8 + i}"} for i, x in enumerate(refs)]), 201).json(); assert len(r["reservations"]) == 8

def test_auth_ownership_and_restaurants(reset, api):
    d = date(); world(reset, api, restaurants=[rest(), rest("r_b", tables=[{"id": "t_x", "label": "X", "capacity": 4}])]); a = ada(api)
    r1 = book(a, d, "t_2").json()["reference"]; r2 = book(a, d, "t_x", rid="r_b").json()["reference"]
    assert_error(api().post("/reservation-moves", json={"moves": [{"reference": r1}]}, idempotency_key=new_key()), 401, "unauthenticated")
    assert_error(mv(bob(api), [{"reference": r1}]), 404, "not_found"); assert_error(mv(a, [{"reference": "NOPE12"}]), 404, "not_found")
    assert_error(mv(a, [{"reference": r1}, {"reference": r2}]), 422, "validation_failed")

def test_other_patch_fields_and_noop_and_unknown_fields(reset, api):
    d, a, r1, r2 = two(reset, api); before = a.get(f"/reservations/{r1}").json()
    r = assert_status(mv(a, [{"reference": r1, "starts_at_local": at(d, "21:00"), "party_size": 4, "junk": 1}, {"reference": r2}]), 201).json()["reservations"]
    assert r[0]["starts_at_local"] == at(d, "21:00") and r[0]["party_size"] == 4 and r[0]["created_at"] == before["created_at"] and r[1]["table_id"] == "t_3" and r[1]["starts_at_local"] == at(d, "19:00")

def test_cancelled_booking_is_409_and_errors_follow_input_order(reset, api):
    d, a, r1, r2 = two(reset, api); a.post(f"/reservations/{r2}/cancel")
    assert_error(mv(a, [{"reference": r1, "party_size": 2}, {"reference": r2, "party_size": 2}]), 409, "reservation_cancelled")
    assert_error(mv(a, [{"reference": r1, "party_size": 99}, {"reference": r2}]), 422, "party_exceeds_capacity")

def test_cutoff_is_checked_per_booking(reset, api):
    d = date(-2); world(reset, api); a = ada(api); r1 = book(a, d, "t_2").json()["reference"]; fut = book(a, date(), "t_3").json()["reference"]
    assert_error(mv(a, [{"reference": fut, "party_size": 2}, {"reference": r1, "party_size": 2}]), 409, "cutoff_passed")
    assert a.get(f"/reservations/{fut}").json()["party_size"] == 2

def test_replay_is_200_and_identical_even_after_changes(reset, api):
    d, a, r1, r2 = two(reset, api); k = new_key(); moves = [{"reference": r1, "table_id": "t_3"}, {"reference": r2, "table_id": "t_2"}]
    first = assert_status(mv(a, moves, key=k), 201).json(); a.post(f"/reservations/{r1}/cancel"); again = assert_status(mv(a, moves, key=k), 200).json()
    assert again == first and a.get(f"/reservations/{r1}").json()["status"] == "cancelled"
    assert_error(mv(a, [{"reference": r1, "table_id": "t_3"}], key=k), 409, "idempotency_key_reuse")

def test_missing_key_is_400(reset, api):
    d, a, r1, r2 = two(reset, api); assert_error(a.post("/reservation-moves", json={"moves": [{"reference": r1}]}), 400, "missing_idempotency_key")
