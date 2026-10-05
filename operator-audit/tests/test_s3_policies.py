"""Stage 3: dated booking policies and accepted terms."""
import copy, pytest
from kit import *
pytestmark = pytest.mark.s3
POL = "/restaurants/r_anker/policies"


def setup(reset, api, **kw):
    d = date(); world(reset, api, restaurants=[rest(managers=["u_ada"], **kw), rest("r_b", managers=["u_bob"])]); return d, ada(api)


def pub(c, p, key=None, path=POL): return c.post(path, json=p, idempotency_key=key or new_key())


def test_publishing_permissions(reset, api):
    d, a = setup(reset, api); p = fx.policy(d)
    assert_error(api().post(POL, json=p, idempotency_key=new_key()), 401, "unauthenticated")
    assert_error(bob(api).post(POL, json=p, idempotency_key=new_key()), 403, "forbidden")
    assert_error(a.post("/restaurants/nope/policies", json=p, idempotency_key=new_key()), 404, "not_found")
    assert_error(a.post(POL, json=p), 400, "missing_idempotency_key")
    assert_error(a.post("/restaurants/r_b/policies", json=p, idempotency_key=new_key()), 403, "forbidden")


def test_versions_count_per_restaurant_and_are_returned_with_the_policy(reset, api):
    d, a = setup(reset, api); b = bob(api)
    r1 = assert_status(pub(a, fx.policy(d, slot_minutes=15)), 201).json(); r2 = assert_status(pub(a, fx.policy(date(9))), 201).json()
    assert r1["policy_version"] == 1 and r2["policy_version"] == 2 and r1["slot_minutes"] == 15 and r1["effective_from"] == d and r1["capacities"] == {"t_1": 2, "t_2": 4, "t_3": 6}
    assert assert_status(pub(b, fx.policy(d), path="/restaurants/r_b/policies"), 201).json()["policy_version"] == 1


def test_replay_and_key_reuse_allocate_nothing(reset, api):
    d, a = setup(reset, api); k = new_key(); first = pub(a, fx.policy(d), key=k).json(); again = pub(a, fx.policy(d), key=k)
    assert again.status_code == 200 and again.json() == first
    assert_error(pub(a, fx.policy(d, slot_minutes=15), key=k), 409, "idempotency_key_reuse")
    assert pub(a, fx.policy(date(9))).json()["policy_version"] == 2


@pytest.mark.parametrize("name,mut", [
    ("no effective_from", lambda p: p.pop("effective_from")), ("bad date", lambda p: p.update(effective_from="2026-02-30")), ("date format", lambda p: p.update(effective_from="10/12/2026")),
    ("slot 0", lambda p: p.update(slot_minutes=0)), ("slot 1441", lambda p: p.update(slot_minutes=1441)), ("slot bool", lambda p: p.update(slot_minutes=True)), ("slot str", lambda p: p.update(slot_minutes="30")),
    ("dur 0", lambda p: p.update(reservation_duration_minutes=0)), ("dur 1441", lambda p: p.update(reservation_duration_minutes=1441)), ("cutoff -1", lambda p: p.update(cancellation_cutoff_minutes=-1)),
    ("cutoff 10081", lambda p: p.update(cancellation_cutoff_minutes=10081)), ("cutoff bool", lambda p: p.update(cancellation_cutoff_minutes=False)),
    ("dup weekday", lambda p: p.update(opening_hours=fx.all_week()[:1] * 2)), ("closes<=opens", lambda p: p.update(opening_hours=[{"weekday": "mon", "opens": "20:00", "closes": "19:00"}])),
    ("bad weekday", lambda p: p.update(opening_hours=[{"weekday": "xyz", "opens": "18:00", "closes": "20:00"}])), ("missing table", lambda p: p["capacities"].pop("t_3")),
    ("extra table", lambda p: p["capacities"].update(t_9=2)), ("cap 0", lambda p: p["capacities"].update(t_1=0)), ("cap 101", lambda p: p["capacities"].update(t_1=101)), ("cap bool", lambda p: p["capacities"].update(t_1=True)),
    ("cap str", lambda p: p["capacities"].update(t_1="2")), ("no capacities", lambda p: p.pop("capacities")), ("no hours", lambda p: p.pop("opening_hours"))])
def test_invalid_policies_are_422_and_allocate_no_version(reset, api, name, mut):
    d, a = setup(reset, api); p = fx.policy(d); mut(p)
    r = pub(a, p); assert r.status_code in (422, 400), (name, r.text)
    if r.status_code == 422: assert r.json()["error"]["code"] == "validation_failed"
    assert pub(a, fx.policy(d)).json()["policy_version"] == 1 and a.get(POL).json()["policies"].__len__() == 1


def test_unknown_policy_fields_are_ignored_and_listing_is_public(reset, api):
    d, a = setup(reset, api); pub(a, fx.policy(d, junk="x")); pub(a, fx.policy(date(9)))
    got = api().get(POL).json()["policies"]; assert [p["policy_version"] for p in got] == [1, 2] and got[0]["effective_from"] == d
    assert_error(api().get("/restaurants/nope/policies"), 404, "not_found")
    det = api().get("/restaurants/r_anker").json(); assert det["reservation_duration_minutes"] == 90 and det["slot_minutes"] == 30


def test_policy_selection_by_effective_date_ties_and_publication_order(reset, api):
    d, a = setup(reset, api); later = date(9)
    pub(a, fx.policy(later, reservation_duration_minutes=120)); pub(a, fx.policy(d, reservation_duration_minutes=60)); pub(a, fx.policy(d, reservation_duration_minutes=45))
    t_d = book(a, d, "t_1", "19:00", 2).json()["accepted_terms"]; t_l = book(a, later, "t_1", "19:00", 2).json()["accepted_terms"]; t_mid = book(a, date(8), "t_1", "19:00", 2).json()["accepted_terms"]
    assert t_d["policy_version"] == 3 and t_d["reservation_duration_minutes"] == 45 and t_l["policy_version"] == 1 and t_l["reservation_duration_minutes"] == 120 and t_mid["policy_version"] == 3
    assert book(a, date(4), "t_1", "19:00", 2).json()["accepted_terms"]["policy_version"] == 0


def test_policy_changes_availability_and_booking_rules(reset, api):
    d, a = setup(reset, api); pub(a, fx.policy(d, slot_minutes=60, reservation_duration_minutes=120, opening_hours=[{"weekday": fx.weekday_of(d), "opens": "18:00", "closes": "21:00"}], capacities={"t_1": 2, "t_2": 8, "t_3": 6}))
    hh = [s["starts_at_local"][-5:] for s in avail(a, d, 2).json()["slots"]]; assert hh == ["18:00", "19:00"]
    assert slot(avail(a, d, 7), "18:00")["available_table_ids"] == ["t_2"]
    b = assert_status(book(a, d, "t_2", "19:00", 7), 201).json(); assert b["ends_at"][11:16] == "21:00" and b["accepted_terms"]["slot_minutes"] == 60
    assert_error(book(a, d, "t_3", "18:30", 2), 422, "not_on_slot_grid"); assert_error(book(a, d, "t_3", "20:00", 2), 422, "outside_opening_hours")


def test_publication_never_changes_existing_bookings(reset, api):
    d, a = setup(reset, api); r = book(a, d, "t_2", "19:00", 2).json(); h0 = a.get(f"/reservations/{r['reference']}/history").json()
    pub(a, fx.policy(d, reservation_duration_minutes=30, cancellation_cutoff_minutes=5, capacities={"t_1": 1, "t_2": 1, "t_3": 1}))
    now = a.get(f"/reservations/{r['reference']}").json(); assert now == r and a.get(f"/reservations/{r['reference']}/history").json() == h0
    assert a.get(f"/reservations/{r['reference']}/decision").json()["accepted_terms"]["policy_version"] == 0


def test_amendment_adopts_the_new_policy_atomically(reset, api):
    d, a = setup(reset, api); r = book(a, d, "t_2", "19:00", 2).json(); ref = r["reference"]
    pub(a, fx.policy(d, reservation_duration_minutes=120, capacities={"t_1": 2, "t_2": 4, "t_3": 6}))
    p = assert_status(a.patch(f"/reservations/{ref}", json={"party_size": 3}), 200).json()
    assert p["revision"] == 2 and p["accepted_terms"]["policy_version"] == 1 and p["accepted_terms"]["reservation_duration_minutes"] == 120 and p["ends_at"][11:16] == "21:00"
    es = a.get(f"/reservations/{ref}/history").json()["entries"]; assert es[0]["accepted_terms"]["policy_version"] == 0 and es[1]["accepted_terms"]["policy_version"] == 1


def test_amendment_into_a_different_policy_validates_against_that_policy(reset, api):
    d, a = setup(reset, api); later = date(9); r = book(a, d, "t_2", "19:00", 4).json()
    pub(a, fx.policy(later, capacities={"t_1": 2, "t_2": 2, "t_3": 6}))
    assert_error(a.patch(f"/reservations/{r['reference']}", json={"starts_at_local": at(later, "19:00")}), 422, "party_exceeds_capacity")
    assert a.get(f"/reservations/{r['reference']}").json()["revision"] == 1
    ok = assert_status(a.patch(f"/reservations/{r['reference']}", json={"starts_at_local": at(later, "19:00"), "table_id": "t_3"}), 200).json(); assert ok["accepted_terms"]["policy_version"] == 1


def test_cancel_and_amend_use_the_old_accepted_cutoff(reset, api):
    d, a = setup(reset, api); r = book(a, d, "t_2", "19:00", 2).json()
    pub(a, fx.policy(d, cancellation_cutoff_minutes=10080 * 2 // 2))
    assert a.get(f"/reservations/{r['reference']}/decision").json()["accepted_terms"]["cancellation_cutoff_minutes"] == 120
    assert_status(a.post(f"/reservations/{r['reference']}/cancel"), 200)


def test_noop_amendment_retains_terms_even_after_a_new_policy(reset, api):
    d, a = setup(reset, api); r = book(a, d, "t_2", "19:00", 2).json(); pub(a, fx.policy(d, reservation_duration_minutes=45))
    p = assert_status(a.patch(f"/reservations/{r['reference']}", json={"party_size": 2}), 200).json(); assert p["accepted_terms"]["policy_version"] == 0 and p["revision"] == 1 and p["ends_at"] == r["ends_at"]
    a.post(f"/reservations/{r['reference']}/cancel"); assert_error(a.patch(f"/reservations/{r['reference']}", json={"party_size": 2}), 409, "reservation_cancelled")


def test_old_idempotent_responses_keep_original_revision_and_terms(reset, api):
    d, a = setup(reset, api); k = new_key(); first = book(a, d, "t_2", "19:00", 2, key=k).json(); pub(a, fx.policy(d)); a.patch(f"/reservations/{first['reference']}", json={"party_size": 3})
    again = book(a, d, "t_2", "19:00", 2, key=k); assert again.status_code == 200 and again.json() == first and again.json()["revision"] == 1
