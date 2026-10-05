"""Stage 1 §8: list, read, cancel, amend."""
import datetime as dt, pytest
from zoneinfo import ZoneInfo
from kit import *
pytestmark = pytest.mark.s1

def all_day(cutoff=120, tz="Europe/Berlin"):
    return rest(slot_minutes=1, reservation_duration_minutes=30, cancellation_cutoff_minutes=cutoff, timezone=tz,
                opening_hours=[{"weekday": w, "opens": "00:00", "closes": "23:59"} for w in fx.WEEKDAYS])

def local_in(minutes, tz="Europe/Berlin"):
    t = (dt.datetime.now(ZoneInfo(tz)) + dt.timedelta(minutes=minutes)).replace(second=0, microsecond=0)
    return t.strftime("%Y-%m-%d"), t.strftime("%H:%M")

def test_list_is_descending_includes_cancelled_and_is_private(reset, api):
    d = date(); world(reset, api); a = ada(api); b = bob(api)
    refs = [book(a, d, "t_2", h).json()["reference"] for h in ("18:00", "21:00", "19:30")]; book(b, d, "t_3", "19:00")
    a.post(f"/reservations/{refs[1]}/cancel")
    lst = a.get("/reservations").json()["reservations"]
    assert [x["starts_at_local"][-5:] for x in lst] == ["21:00", "19:30", "18:00"] and [x["status"] for x in lst] == ["cancelled", "confirmed", "confirmed"]
    assert len(b.get("/reservations").json()["reservations"]) == 1

def test_get_by_reference_owner_only(reset, api):
    d = date(); world(reset, api); a = ada(api); ref = book(a, d).json()["reference"]
    assert a.get(f"/reservations/{ref}").json()["reference"] == ref
    assert_error(bob(api).get(f"/reservations/{ref}"), 404, "not_found"); assert_error(a.get("/reservations/NOPE12"), 404, "not_found")

def test_cancel_twice_and_other_user(reset, api):
    d = date(); world(reset, api); a = ada(api); ref = book(a, d).json()["reference"]
    assert_error(bob(api).post(f"/reservations/{ref}/cancel"), 404, "not_found")
    r1 = assert_status(a.post(f"/reservations/{ref}/cancel"), 200).json(); r2 = assert_status(a.post(f"/reservations/{ref}/cancel"), 200).json()
    assert r1["status"] == r2["status"] == "cancelled" and r1["reference"] == ref
    assert_error(a.post("/reservations/NOPE12/cancel"), 404, "not_found")

def test_cancel_cutoff_boundary(reset, api):
    world(reset, api, restaurants=[all_day(120)]); a = ada(api)
    d1, h1 = local_in(110); d2, h2 = local_in(135)
    r1 = assert_status(book(a, d1, "t_2", h1), 201).json(); r2 = assert_status(book(a, d2, "t_3", h2), 201).json()
    assert_error(a.post(f"/reservations/{r1['reference']}/cancel"), 409, "cutoff_passed")
    assert_status(a.post(f"/reservations/{r2['reference']}/cancel"), 200)

def test_cutoff_for_past_booking(reset, api):
    world(reset, api); a = ada(api); ref = book(a, date(-3)).json()["reference"]
    assert_error(a.post(f"/reservations/{ref}/cancel"), 409, "cutoff_passed"); assert_error(a.patch(f"/reservations/{ref}", json={"party_size": 3}), 409, "cutoff_passed")

def test_cancelled_and_cutoff_booking_cannot_be_amended(reset, api):
    d = date(); world(reset, api); a = ada(api); ref = book(a, d).json()["reference"]; a.post(f"/reservations/{ref}/cancel")
    assert_error(a.patch(f"/reservations/{ref}", json={"party_size": 3}), 409, "reservation_cancelled")

def test_patch_each_field_keeps_identity(reset, api):
    d = date(); world(reset, api); a = ada(api); orig = book(a, d, "t_2", "19:00", 2).json(); ref = orig["reference"]
    r = assert_status(a.patch(f"/reservations/{ref}", json={"table_id": "t_3"}), 200).json(); assert r["table_id"] == "t_3" and r["reference"] == ref and r["reservation_id"] == orig["reservation_id"]
    r = a.patch(f"/reservations/{ref}", json={"starts_at_local": at(d, "20:30")}).json(); assert r["starts_at_local"] == at(d, "20:30") and r["ends_at"][:19] == f"{d}T22:00:00"
    r = a.patch(f"/reservations/{ref}", json={"party_size": 5}).json(); assert r["party_size"] == 5 and r["table_id"] == "t_3" and r["created_at"] == orig["created_at"]

def test_patch_releases_old_slot_and_takes_new(reset, api):
    d = date(); world(reset, api); a = ada(api); ref = book(a, d, "t_2", "19:00").json()["reference"]
    a.patch(f"/reservations/{ref}", json={"starts_at_local": at(d, "21:00")})
    assert "t_2" in slot(avail(a, d), "19:00")["available_table_ids"] and "t_2" not in slot(avail(a, d), "21:00")["available_table_ids"]
    assert_status(book(bob(api), d, "t_2", "19:00"), 201)

def test_failed_patch_changes_nothing(reset, api):
    d = date(); world(reset, api); a = ada(api); b = bob(api); ref = book(a, d, "t_2", "19:00").json()["reference"]; book(b, d, "t_3", "19:00")
    for patch, code, st in (({"table_id": "t_3"}, "table_unavailable", 409), ({"party_size": 5}, "party_exceeds_capacity", 422), ({"starts_at_local": at(d, "19:15")}, "not_on_slot_grid", 422), ({"starts_at_local": at(d, "22:30")}, "outside_opening_hours", 422), ({"table_id": "zzz"}, "not_found", 404)):
        assert_error(a.patch(f"/reservations/{ref}", json=patch), st, code)
    cur = a.get(f"/reservations/{ref}").json(); assert (cur["table_id"], cur["starts_at_local"], cur["party_size"]) == ("t_2", at(d, "19:00"), 2)
    assert "t_2" not in slot(avail(a, d), "19:00")["available_table_ids"]

def test_patch_can_overlap_itself_and_noop_is_ok(reset, api):
    d = date(); world(reset, api); a = ada(api); ref = book(a, d, "t_2", "19:00").json()["reference"]
    assert_status(a.patch(f"/reservations/{ref}", json={"starts_at_local": at(d, "19:30")}), 200)
    assert_status(a.patch(f"/reservations/{ref}", json={"starts_at_local": at(d, "19:30"), "party_size": 2}), 200)
    assert_error(bob(api).patch(f"/reservations/{ref}", json={"party_size": 1}), 404, "not_found")
    assert_error(a.patch("/reservations/NOPE12", json={"party_size": 1}), 404, "not_found")

def test_patch_to_foreign_restaurant_table_is_404(reset, api):
    d = date(); world(reset, api, restaurants=[rest(), rest("r_b", tables=[{"id": "t_x", "label": "X", "capacity": 4}])]); a = ada(api); ref = book(a, d).json()["reference"]
    assert_error(a.patch(f"/reservations/{ref}", json={"table_id": "t_x"}), 404, "not_found")
