"""Stage 1 §7: idempotency."""
import json, pytest
from harness.concurrent import burst
from kit import *
pytestmark = pytest.mark.s1

def test_key_presence_and_length(reset, api):
    d = date(); world(reset, api); a = ada(api)
    assert_error(a.post("/reservations", json=body(d)), 400, "missing_idempotency_key")
    assert_error(a.post("/reservations", json=body(d), headers={"Idempotency-Key": ""}), 400, "missing_idempotency_key")
    assert_error(book(a, d, key="k" * 256), 422, "validation_failed")
    assert_status(book(a, d, "t_1", key="k" * 255), 201); assert_status(book(a, d, "t_3", key="x"), 201)

def test_replay_returns_the_original_with_200(reset, api):
    d = date(); world(reset, api); a = ada(api); k = new_key()
    first = assert_status(book(a, d, key=k), 201).json(); again = assert_status(book(a, d, key=k), 200).json()
    assert again == first and len(a.get("/reservations").json()["reservations"]) == 1

def test_json_equivalence_ignores_key_order_and_whitespace(reset, api):
    d = date(); world(reset, api); a = ada(api); k = new_key(); b = body(d)
    assert_status(a.post("/reservations", content=json.dumps(b), idempotency_key=k), 201)
    shuffled = json.dumps(dict(reversed(list(b.items()))), indent=3)
    assert_status(a.post("/reservations", content=shuffled, idempotency_key=k), 200)

def test_different_body_is_409_even_if_invalid(reset, api):
    d = date(); world(reset, api); a = ada(api); k = new_key(); book(a, d, key=k)
    assert_error(book(a, d, "t_2", "20:00", key=k), 409, "idempotency_key_reuse")
    assert_error(a.post("/reservations", json={"restaurant_id": "r_anker", "party_size": "banana"}, idempotency_key=k), 409, "idempotency_key_reuse")

def test_key_is_scoped_to_the_user(reset, api):
    d = date(); world(reset, api); k = new_key()
    assert_status(book(ada(api), d, "t_2", key=k), 201); assert_status(book(bob(api), d, "t_3", key=k), 201)

def test_same_key_on_another_path_is_a_new_request(reset, api):
    d = date(); world(reset, api); a = ada(api); k = new_key(); ref = book(a, d, key=k).json()["reference"]
    assert_status(a.post("/reservation-moves", json={"moves": [{"reference": ref, "table_id": "t_3"}]}, idempotency_key=k), 201)

def test_key_after_a_4xx_is_a_first_use(reset, api):
    d = date(); world(reset, api); a = ada(api); k = new_key()
    assert_error(book(a, d, "t_2", "19:15", key=k), 422, "not_on_slot_grid")
    assert_status(book(a, d, "t_2", "19:00", key=k), 201)

def test_replay_after_cancel_is_still_the_original(reset, api):
    d = date(); world(reset, api); a = ada(api); k = new_key(); first = book(a, d, key=k).json(); a.post(f"/reservations/{first['reference']}/cancel")
    again = assert_status(book(a, d, key=k), 200).json(); assert again == first and again["status"] == "confirmed"
    assert "t_2" in slot(avail(a, d), "19:00")["available_table_ids"]

def test_concurrent_identical_requests_take_effect_once(reset, api):
    d = date(); world(reset, api); a = ada(api); k = new_key(); b = body(d)
    rs = burst(lambda i: ada(api).post("/reservations", json=b, idempotency_key=k), 12)
    assert sorted(r.status_code for r in rs) == [200] * 11 + [201] and len({r.text for r in rs}) == 1
    assert len(a.get("/reservations").json()["reservations"]) == 1

def test_concurrent_different_keys_same_slot_only_one_wins(reset, api):
    d = date(); world(reset, api)
    rs = burst(lambda i: (ada(api) if i % 2 else bob(api)).post("/reservations", json=body(d), idempotency_key=new_key()), 20)
    assert sorted(set(r.status_code for r in rs)) == [201, 409] and [r.status_code for r in rs].count(201) == 1
