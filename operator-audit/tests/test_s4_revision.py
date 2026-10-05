"""Stage 4: the restaurant revision counts successful real writes only."""
import pytest
from kit import *
pytestmark = pytest.mark.s4
PREVIEW = {"table_id": "t_1", "from": "2001-01-01T00:00:00+00:00", "to": "2001-01-01T01:00:00+00:00"}


def revision(c, rid="r_anker"):
    r = assert_status(c.post(f"/restaurants/{rid}/replans", json=PREVIEW, idempotency_key=new_key()), 201).json(); return r["restaurant_revision"]


def setup(reset, api, **kw):
    d = date(14); world(reset, api, restaurants=[rest(managers=["u_ada"], combinable=PAIRS, **kw)]); return d, ada(api)


def test_starts_at_zero_and_previews_do_not_count(reset, api):
    d, a = setup(reset, api); assert revision(a) == 0 and revision(a) == 0


def test_booking_amendment_and_cancel_each_count_once(reset, api):
    d, a = setup(reset, api); r = book(a, d, "t_2", "19:00", 2).json()["reference"]; assert revision(a) == 1
    a.patch(f"/reservations/{r}", json={"party_size": 3}); assert revision(a) == 2
    a.patch(f"/reservations/{r}", json={"party_size": 3}); a.patch(f"/reservations/{r}", json={}); assert revision(a) == 2
    a.post(f"/reservations/{r}/cancel"); assert revision(a) == 3; a.post(f"/reservations/{r}/cancel"); assert revision(a) == 3


def test_failures_and_replays_do_not_count(reset, api):
    d, a = setup(reset, api); k = new_key(); book(a, d, "t_2", "19:00", 2, key=k); assert revision(a) == 1
    book(a, d, "t_2", "19:00", 2, key=k); book(a, d, "t_2", "19:00", 2); book(a, d, "t_2", "19:15", 2); book(a, d, "t_1", "19:00", 9); book(a, d, "zz")
    assert revision(a) == 1


def test_policy_publication_counts_but_failures_and_replays_do_not(reset, api):
    d, a = setup(reset, api); k = new_key()
    a.post("/restaurants/r_anker/policies", json=fx.policy(d), idempotency_key=k); assert revision(a) == 1
    a.post("/restaurants/r_anker/policies", json=fx.policy(d), idempotency_key=k); a.post("/restaurants/r_anker/policies", json={}, idempotency_key=new_key()); assert revision(a) == 1


def test_series_adoption_counts_once_for_the_whole_operation(reset, api):
    d, a = setup(reset, api); r = book(a, d, "t_2", "19:00", 2).json()["reference"]; assert revision(a) == 1
    s = a.post("/series", json={"anchor_reference": r, "count": 5, "interval_weeks": 1}, idempotency_key=new_key()); assert s.status_code == 201 and revision(a) == 2


def test_moves_batch_counts_once_and_noop_batch_not_at_all(reset, api):
    d, a = setup(reset, api); r1 = book(a, d, "t_1", "19:00", 2).json()["reference"]; r2 = book(a, d, "t_2", "19:00", 2).json()["reference"]; assert revision(a) == 2
    assert_status(a.post("/reservation-moves", json={"moves": [{"reference": r1, "table_id": "t_2"}, {"reference": r2, "table_id": "t_1"}]}, idempotency_key=new_key()), 201); assert revision(a) == 3
    assert_status(a.post("/reservation-moves", json={"moves": [{"reference": r1, "table_id": "t_2"}]}, idempotency_key=new_key()), 201); assert revision(a) == 3


def test_series_member_patch_counts_like_any_amendment(reset, api):
    d, a = setup(reset, api); r = book(a, d, "t_2", "19:00", 2).json()["reference"]; s = a.post("/series", json={"anchor_reference": r, "count": 3, "interval_weeks": 1}, idempotency_key=new_key()).json()
    base = revision(a); a.patch(f"/reservations/{s['occurrences'][2]['reference']}", json={"party_size": 3}); assert revision(a) == base + 1
