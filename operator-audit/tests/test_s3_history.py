"""Stage 3: history, revisions, decisions, expected_revision."""
import pytest
from harness.concurrent import burst, no_5xx, tally
from kit import *
pytestmark = pytest.mark.s3
TERMS = {"policy_version", "slot_minutes", "reservation_duration_minutes", "cancellation_cutoff_minutes", "opening_hours", "capacities"}


def one(reset, api, **kw):
    d = date(); world(reset, api, restaurants=[rest(**kw)]); a = ada(api)
    return d, a, book(a, d, "t_2", "19:00", 2).json()


def hist(c, ref, **kw): return c.get(f"/reservations/{ref}/history", **kw)


def test_reservation_carries_revision_and_accepted_terms(reset, api):
    d, a, r = one(reset, api)
    assert r["revision"] == 1 and set(r["accepted_terms"]) == TERMS and r["accepted_terms"]["policy_version"] == 0
    assert r["accepted_terms"]["capacities"] == {"t_1": 2, "t_2": 4, "t_3": 6} and r["accepted_terms"]["slot_minutes"] == 30 and r["accepted_terms"]["reservation_duration_minutes"] == 90
    assert a.get(f"/reservations/{r['reference']}").json()["accepted_terms"] == r["accepted_terms"] and a.get("/reservations").json()["reservations"][0]["revision"] == 1


def test_created_entry_names_all_three_fields(reset, api):
    d, a, r = one(reset, api); h = hist(a, r["reference"]).json(); e = h["entries"][0]
    assert h["reference"] == r["reference"] and len(h["entries"]) == 1 and e["seq"] == 1 and e["event"] == "created" and e["revision"] == 1 and set(e["accepted_terms"]) == TERMS
    assert e["changes"] == [{"field": "table_id", "from": None, "to": "t_2"}, {"field": "starts_at_local", "from": None, "to": at(d, "19:00")}, {"field": "party_size", "from": None, "to": 2}]
    assert isinstance(e["at"], str) and e["at"][-6:] in ("+01:00", "+02:00", "+00:00") or e["at"].endswith("Z")


def test_changed_entry_lists_only_real_changes_in_field_order(reset, api):
    d, a, r = one(reset, api); ref = r["reference"]
    a.patch(f"/reservations/{ref}", json={"party_size": 4, "table_id": "t_3"}); a.patch(f"/reservations/{ref}", json={"starts_at_local": at(d, "20:00")})
    es = hist(a, ref).json()["entries"]
    assert [x["seq"] for x in es] == [1, 2, 3] and [x["event"] for x in es] == ["created", "changed", "changed"]
    assert es[1]["changes"] == [{"field": "table_id", "from": "t_2", "to": "t_3"}, {"field": "party_size", "from": 2, "to": 4}]
    assert es[2]["changes"] == [{"field": "starts_at_local", "from": at(d, "19:00"), "to": at(d, "20:00")}] and [x["revision"] for x in es] == [1, 2, 3]


def test_noop_patch_records_nothing_and_keeps_revision(reset, api):
    d, a, r = one(reset, api); ref = r["reference"]
    p = assert_status(a.patch(f"/reservations/{ref}", json={"party_size": 2, "table_id": "t_2", "starts_at_local": at(d, "19:00")}), 200).json()
    assert p["revision"] == 1 and p["accepted_terms"] == r["accepted_terms"] and len(hist(a, ref).json()["entries"]) == 1
    assert_status(a.patch(f"/reservations/{ref}", json={}), 200)
    assert len(hist(a, ref).json()["entries"]) == 1


def test_cancel_entry_and_revision_rules(reset, api):
    d, a, r = one(reset, api); ref = r["reference"]
    c1 = assert_status(a.post(f"/reservations/{ref}/cancel"), 200).json(); c2 = a.post(f"/reservations/{ref}/cancel").json()
    assert c1["revision"] == 2 == c2["revision"]
    es = hist(a, ref).json()["entries"]; assert [x["event"] for x in es] == ["created", "cancelled"] and es[1]["changes"] == [] and es[1]["revision"] == 2


def test_replay_of_create_records_nothing(reset, api):
    d = date(); world(reset, api); a = ada(api); k = new_key(); r = book(a, d, key=k).json(); book(a, d, key=k); book(a, d, key=k)
    assert len(hist(a, r["reference"]).json()["entries"]) == 1 and a.get(f"/reservations/{r['reference']}").json()["revision"] == 1


def test_history_and_decision_are_owner_only_even_unauthenticated(reset, api):
    d, a, r = one(reset, api); ref = r["reference"]
    for path in (f"/reservations/{ref}/history", f"/reservations/{ref}/decision"):
        assert_error(api().get(path), 404, "not_found"); assert_error(bob(api).get(path), 404, "not_found"); assert_error(a.get(path.replace(ref, "NOPE12")), 404, "not_found")
    dec = a.get(f"/reservations/{ref}/decision").json(); assert dec == {"reference": ref, "revision": 1, "accepted_terms": r["accepted_terms"]}
    a.post(f"/reservations/{ref}/cancel"); assert a.get(f"/reservations/{ref}/decision").json()["revision"] == 2 and len(hist(a, ref).json()["entries"]) == 2


def test_a_manager_does_not_gain_access_to_other_diners_history(reset, api):
    d = date(); world(reset, api, restaurants=[rest(managers=["u_bob"])]); r = book(ada(api), d).json(); assert_error(bob(api).get(f"/reservations/{r['reference']}/history"), 404, "not_found")


def test_expected_revision_rules(reset, api):
    d, a, r = one(reset, api); ref = r["reference"]
    assert_status(a.patch(f"/reservations/{ref}", json={"party_size": 3, "expected_revision": 1}), 200)
    assert_error(a.patch(f"/reservations/{ref}", json={"party_size": 4, "expected_revision": 1}), 409, "stale_revision")
    assert_error(a.patch(f"/reservations/{ref}", json={"party_size": 99, "starts_at_local": "junk", "expected_revision": 1}), 409, "stale_revision")
    for bad in (0, -1, "2", True, 1.5, None):
        r_ = a.patch(f"/reservations/{ref}", json={"party_size": 4, "expected_revision": bad}); assert r_.status_code in (422, 400), (bad, r_.text)
    assert_status(a.patch(f"/reservations/{ref}", json={"party_size": 4, "expected_revision": 2}), 200); assert a.get(f"/reservations/{ref}").json()["revision"] == 3


def test_stale_revision_beats_cutoff(reset, api):
    d = date(-2); world(reset, api); a = ada(api); r = book(a, d).json()
    assert_error(a.patch(f"/reservations/{r['reference']}", json={"party_size": 3, "expected_revision": 7}), 409, "stale_revision")
    assert_error(a.patch(f"/reservations/{r['reference']}", json={"party_size": 3, "expected_revision": 1}), 409, "cutoff_passed")


def test_concurrent_amendments_from_one_revision_allow_one(reset, api):
    d, a, r = one(reset, api); ref = r["reference"]
    rs = burst(lambda i: a.patch(f"/reservations/{ref}", json={"party_size": 3 + (i % 2), "expected_revision": 1}), 10); no_5xx(rs)
    assert tally(rs)[200] == 1 and a.get(f"/reservations/{ref}").json()["revision"] == 2


def test_combined_table_history_uses_table_ids(reset, api):
    d = date(); world(reset, api, restaurants=[rest(combinable=PAIRS)]); a = ada(api)
    r = book(a, d, ["t_2", "t_1"], "19:00", 6).json(); ref = r["reference"]
    c = hist(a, ref).json()["entries"][0]["changes"]; assert c[0] == {"field": "table_ids", "from": None, "to": ["t_1", "t_2"]} and {x["field"] for x in c} == {"table_ids", "starts_at_local", "party_size"}
    assert len(hist(a, ref).json()["entries"]) == 1
    a.patch(f"/reservations/{ref}", json={"table_ids": ["t_2", "t_1"]}); assert len(hist(a, ref).json()["entries"]) == 1 and a.get(f"/reservations/{ref}").json()["revision"] == 1
    a.patch(f"/reservations/{ref}", json={"table_id": "t_3", "party_size": 5}); ch = hist(a, ref).json()["entries"][1]["changes"]
    assert ch[0] == {"field": "table_ids", "from": ["t_1", "t_2"], "to": ["t_3"]} and ch[1]["field"] == "party_size"
