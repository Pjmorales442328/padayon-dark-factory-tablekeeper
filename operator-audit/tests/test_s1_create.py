"""Stage 1 §8: POST /reservations."""
import re, pytest
from kit import *
pytestmark = pytest.mark.s1

def test_created_reservation_shape(reset, api):
    d = date(); world(reset, api); r = assert_status(book(ada(api), d, "t_2", "19:00", 4), 201).json()
    assert re.fullmatch(r"[A-Z0-9]{6,12}", r["reference"]) and r["reservation_id"] and r["status"] == "confirmed"
    assert (r["restaurant_id"], r["table_id"], r["party_size"], r["starts_at_local"]) == ("r_anker", "t_2", 4, f"{d}T19:00")
    assert r["starts_at"][:19] == f"{d}T19:00:00" and r["ends_at"][:19] == f"{d}T20:30:00"
    assert re.search(r"[+-]\d\d:\d\d$|Z$", r["created_at"]) and r["starts_at"][-6:] == r["ends_at"][-6:]

def test_references_are_unique_and_ids_distinct(reset, api):
    d = date(); world(reset, api, restaurants=[rest(tables=[{"id": f"t{i}", "label": str(i), "capacity": 4} for i in range(12)])]); a = ada(api)
    rs = [assert_status(book(a, d, f"t{i}", "19:00", 2), 201).json() for i in range(12)]
    assert len({r["reference"] for r in rs}) == 12 and len({r["reservation_id"] for r in rs}) == 12

@pytest.mark.parametrize("hhmm,code", [("19:15", "not_on_slot_grid"), ("19:01", "not_on_slot_grid"), ("17:30", "outside_opening_hours"), ("22:00", "outside_opening_hours"), ("23:00", "outside_opening_hours"), ("03:00", "outside_opening_hours")])
def test_time_rules(reset, api, hhmm, code):
    world(reset, api); assert_error(book(ada(api), date(), "t_2", hhmm), 422, code)

def test_last_slot_that_ends_exactly_at_closing_is_ok(reset, api):
    world(reset, api); assert_status(book(ada(api), date(), "t_2", "21:30"), 201)

def test_grid_is_counted_from_opening_time(reset, api):
    d = date(); world(reset, api, restaurants=[rest(opening_hours=[{"weekday": fx.weekday_of(d), "opens": "18:10", "closes": "23:00"}])]); a = ada(api)
    assert_status(book(a, d, "t_2", "18:40"), 201); assert_error(book(a, d, "t_2", "19:00"), 422, "not_on_slot_grid")

def test_closed_day_is_outside_opening_hours(reset, api):
    d = date(); world(reset, api, restaurants=[rest(opening_hours=[])]); assert_error(book(ada(api), d), 422, "outside_opening_hours")

@pytest.mark.parametrize("party,code", [(5, "party_exceeds_capacity"), (0, "validation_failed"), (-1, "validation_failed"), ("4", "validation_failed"), (True, "validation_failed"), (2.5, "validation_failed"), (None, "validation_failed")])
def test_party_size_rules(reset, api, party, code):
    world(reset, api); assert_error(book(ada(api), date(), "t_2", "19:00", party), 422, code)

@pytest.mark.parametrize("val", ["2026-09-24T19:00:00", "2026-09-24T19:00Z", "2026-09-24T19:00+02:00", "2026-09-24 19:00", "2026-09-24", "19:00", "", "2026-9-24T19:00"])
def test_starts_at_local_must_be_bare_local_time(reset, api, val):
    world(reset, api); r = ada(api).post("/reservations", json={"restaurant_id": "r_anker", "table_id": "t_2", "starts_at_local": val, "party_size": 2}, idempotency_key=new_key())
    assert_error(r, 422, "validation_failed")

def test_missing_field_is_422_and_wrong_type_is_400(reset, api):
    world(reset, api); a = ada(api); d = date()
    assert_error(a.post("/reservations", json={"restaurant_id": "r_anker", "table_id": "t_2", "party_size": 2}, idempotency_key=new_key()), 422, "validation_failed")
    assert_error(a.post("/reservations", json={"restaurant_id": 5, "table_id": "t_2", "starts_at_local": at(d, "19:00"), "party_size": 2}, idempotency_key=new_key()), 400, "malformed_request")
    assert_error(a.post("/reservations", content=b"[1,2", idempotency_key=new_key()), 400, "malformed_request")

def test_unknown_restaurant_table_or_foreign_table_is_404(reset, api):
    d = date(); world(reset, api, restaurants=[rest(), rest("r_b", tables=[{"id": "t_x", "label": "X", "capacity": 4}])]); a = ada(api)
    assert_error(book(a, d, rid="nope"), 404, "not_found"); assert_error(book(a, d, "nope"), 404, "not_found"); assert_error(book(a, d, "t_x"), 404, "not_found")

def test_overlap_is_409_and_adjacent_is_fine(reset, api):
    d = date(); world(reset, api); a = ada(api); b = bob(api)
    assert_status(book(a, d, "t_2", "19:00"), 201)
    for h in ("18:00", "18:30", "19:00", "20:00"): assert_error(book(b, d, "t_2", h), 409, "table_unavailable")
    assert_status(book(b, d, "t_2", "20:30"), 201); assert_status(book(b, d, "t_3", "19:00"), 201)

def test_rejected_requests_leave_nothing_behind(reset, api):
    d = date(); world(reset, api); a = ada(api); b = bob(api); book(a, d, "t_2", "19:00")
    for r in (book(b, d, "t_2", "19:30"), book(b, d, "t_2", "19:15"), book(b, d, "t_1", "19:00", 5)): assert r.status_code >= 400
    assert b.get("/reservations").json()["reservations"] == []; assert slot(avail(b, d), "19:00")["available_table_ids"] == ["t_1", "t_3"]

def test_past_starts_are_allowed(reset, api):
    world(reset, api); assert_status(book(ada(api), date(-30)), 201)

def test_missing_key_is_400_and_auth_comes_first(reset, api):
    d = date(); world(reset, api)
    assert_error(ada(api).post("/reservations", json=body(d)), 400, "missing_idempotency_key")
    assert_error(api().post("/reservations", json=body(d), idempotency_key=new_key()), 401, "unauthenticated")
