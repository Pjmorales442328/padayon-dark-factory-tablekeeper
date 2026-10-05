"""Stage 2: combined tables."""
import pytest
from harness.concurrent import burst, no_5xx, tally
from kit import *
pytestmark = pytest.mark.s2
R = lambda **kw: rest(combinable=PAIRS, **kw)
def setup(reset, api, **kw): d = date(); world(reset, api, restaurants=[R(**kw)]); return d, ada(api)
def opts(c, d, party, hhmm="19:00"): return [(tuple(o["table_ids"]), o["capacity"]) for o in slot(avail(c, d, party), hhmm)["available_options"]]

def test_options_list_singles_then_pairs_with_capacity(reset, api):
    d, a = setup(reset, api); assert opts(a, d, 1) == [(("t_1",), 2), (("t_2",), 4), (("t_3",), 6), (("t_1", "t_2"), 6), (("t_2", "t_3"), 10)]
    assert opts(a, d, 5) == [(("t_3",), 6), (("t_1", "t_2"), 6), (("t_2", "t_3"), 10)] and opts(a, d, 8) == [(("t_2", "t_3"), 10)] and opts(a, d, 11) == []
    assert slot(avail(a, d, 5), "19:00")["available_table_ids"] == ["t_3"]

def test_options_respect_occupancy_of_any_member(reset, api):
    d, a = setup(reset, api); book(a, d, "t_2", "19:00", 2)
    assert opts(a, d, 1) == [(("t_1",), 2), (("t_3",), 6)] and opts(a, d, 1, "21:00")[-1] == (("t_2", "t_3"), 10)

def test_pair_booking_shape_and_reversed_input(reset, api):
    d, a = setup(reset, api); r = assert_status(book(a, d, ["t_2", "t_1"], "19:00", 6), 201).json()
    assert r["table_ids"] == ["t_1", "t_2"] and "table_id" not in r and r["party_size"] == 6
    one = assert_status(book(a, d, ["t_3"], "19:00", 2), 201).json(); assert one["table_ids"] == ["t_3"] and one["table_id"] == "t_3"
    assert a.get(f"/reservations/{r['reference']}").json()["table_ids"] == ["t_1", "t_2"]

@pytest.mark.parametrize("tables,party,st,code", [(["t_1", "t_3"], 4, 422, "combination_not_allowed"), (["t_1", "t_2", "t_3"], 4, 422, "combination_not_allowed"), (["t_1", "t_2"], 7, 422, "party_exceeds_capacity"),
                                                  (["t_1", "t_1"], 2, 422, "validation_failed"), (["t_1", "zz"], 2, 404, "not_found"), ([], 2, 422, "validation_failed")])
def test_pair_errors(reset, api, tables, party, st, code):
    d, a = setup(reset, api); assert_error(book(a, d, tables, "19:00", party), st, code)

def test_table_id_and_table_ids_together_is_422(reset, api):
    d, a = setup(reset, api); assert_error(a.post("/reservations", json={**body(d, ["t_1", "t_2"], party=4), "table_id": "t_1"}, idempotency_key=new_key()), 422, "validation_failed")

def test_pair_occupies_both_tables_and_cancel_frees_both(reset, api):
    d, a = setup(reset, api); r = book(a, d, ["t_1", "t_2"], "19:00", 6).json(); b = bob(api)
    assert_error(book(b, d, "t_1", "19:00", 2), 409, "table_unavailable"); assert_error(book(b, d, "t_2", "19:30", 2), 409, "table_unavailable"); assert_error(book(b, d, ["t_2", "t_3"], "19:00", 8), 409, "table_unavailable")
    assert_status(book(b, d, "t_3", "19:00", 2), 201); a.post(f"/reservations/{r['reference']}/cancel")
    assert_status(book(b, d, "t_1", "19:00", 2), 201) and assert_status(book(b, d, "t_2", "19:00", 2), 201)

def test_single_blocks_a_pair_containing_it(reset, api):
    d, a = setup(reset, api); book(a, d, "t_2", "19:00", 2); assert_error(book(bob(api), d, ["t_1", "t_2"], "19:00", 5), 409, "table_unavailable")

def test_patch_between_single_and_pair(reset, api):
    d, a = setup(reset, api); ref = book(a, d, "t_3", "19:00", 5).json()["reference"]
    r = assert_status(a.patch(f"/reservations/{ref}", json={"table_ids": ["t_1", "t_2"]}), 200).json(); assert r["table_ids"] == ["t_1", "t_2"] and "table_id" not in r
    assert "t_3" in slot(avail(a, d, 1), "19:00")["available_table_ids"] and "t_1" not in slot(avail(a, d, 1), "19:00")["available_table_ids"]
    r = a.patch(f"/reservations/{ref}", json={"table_id": "t_3"}).json(); assert r["table_ids"] == ["t_3"] and r["table_id"] == "t_3"
    assert_error(a.patch(f"/reservations/{ref}", json={"table_ids": ["t_1", "t_3"]}), 422, "combination_not_allowed")
    assert_error(a.patch(f"/reservations/{ref}", json={"table_ids": ["t_1", "t_2"], "party_size": 11}), 422, "party_exceeds_capacity")

def test_seeded_reservations_accept_table_ids_and_status(reset, api):
    d = date(); seeded = [{"id": "res_a", "reference": "SEEDA1", "user_id": "u_ada", "restaurant_id": "r_anker", "table_ids": ["t_1", "t_2"], "starts_at_local": at(d, "19:00"), "party_size": 5},
                          {"id": "res_b", "reference": "SEEDB1", "user_id": "u_bob", "restaurant_id": "r_anker", "table_id": "t_3", "starts_at_local": at(d, "19:00"), "party_size": 5, "status": "cancelled"}]
    world(reset, api, restaurants=[R()], reservations=seeded); a = ada(api)
    assert opts(a, d, 1) == [(("t_3",), 6)] and a.get("/reservations/SEEDA1").json()["table_ids"] == ["t_1", "t_2"] and bob(api).get("/reservations/SEEDB1").json()["status"] == "cancelled"

def test_replay_of_a_pair_booking_is_identical(reset, api):
    d, a = setup(reset, api); k = new_key(); first = book(a, d, ["t_1", "t_2"], "19:00", 6, key=k).json(); assert assert_status(book(a, d, ["t_1", "t_2"], "19:00", 6, key=k), 200).json() == first

def test_moves_accept_table_ids_and_reject_overlaps(reset, api):
    d, a = setup(reset, api); r1 = book(a, d, "t_3", "19:00", 5).json()["reference"]; r2 = book(a, d, "t_1", "19:00", 2).json()["reference"]
    mvp = lambda ms: a.post("/reservation-moves", json={"moves": ms}, idempotency_key=new_key())
    assert_error(mvp([{"reference": r1, "table_ids": ["t_1", "t_2"]}]), 409, "table_unavailable")
    r = assert_status(mvp([{"reference": r1, "table_ids": ["t_1", "t_2"]}, {"reference": r2, "table_ids": ["t_3"]}]), 201).json()["reservations"]
    assert r[0]["table_ids"] == ["t_1", "t_2"] and r[1]["table_ids"] == ["t_3"]

def test_pair_and_single_racing_have_one_winner(reset, api):
    d, a = setup(reset, api)
    work = [lambda: ada(api).post("/reservations", json=body(d, ["t_1", "t_2"], party=5), idempotency_key=new_key()), lambda: bob(api).post("/reservations", json=body(d, "t_2", party=2), idempotency_key=new_key()),
            lambda: bob(api).post("/reservations", json=body(d, ["t_2", "t_3"], party=8), idempotency_key=new_key())]
    rs = burst(lambda i: work[i % 3](), 30); no_5xx(rs); assert tally(rs)[201] == 1
    taken = [r for r in ada(api).get("/reservations").json()["reservations"] + bob(api).get("/reservations").json()["reservations"]]; assert len(taken) == 1

def test_availability_for_party_with_pairs_stays_consistent_with_booking(reset, api):
    d, a = setup(reset, api)
    for opt, cap in opts(a, d, 3):
        if len(opt) == 2: assert cap >= 3 and book(a, d, list(opt), "19:00", 3).status_code in (201, 409)
