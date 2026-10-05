"""Stage 1 §4, §8: restaurants and availability."""
import pytest
from kit import *
pytestmark = pytest.mark.s1

def hours_for(d, opens, closes):
    return [{"weekday": fx.weekday_of(d), "opens": opens, "closes": closes}]

def test_restaurant_list_and_detail_shape(reset, api):
    world(reset, api, restaurants=[rest(), rest("r_two", name="Two", timezone="America/New_York")]); c = api()
    lst = c.get("/restaurants").json()["restaurants"]
    assert [r["id"] for r in lst] == ["r_anker", "r_two"] and set(lst[0]) >= {"id", "name", "timezone"}
    det = c.get("/restaurants/r_anker").json()
    for k in ("slot_minutes", "reservation_duration_minutes", "cancellation_cutoff_minutes", "opening_hours", "tables"):
        assert k in det, k
    assert [t["id"] for t in det["tables"]] == ["t_1", "t_2", "t_3"]
    assert_error(c.get("/restaurants/zzz"), 404, "not_found")

@pytest.mark.parametrize("opens,closes,slot,dur", [("18:00", "23:00", 30, 90), ("17:30", "22:45", 15, 60), ("12:00", "15:00", 20, 100), ("18:00", "19:30", 30, 90), ("18:00", "19:00", 30, 90)])
def test_slot_grid_matches_opening_hours(reset, api, opens, closes, slot, dur):
    d = date(); world(reset, api, restaurants=[rest(slot_minutes=slot, reservation_duration_minutes=dur, opening_hours=hours_for(d, opens, closes))])
    got = [s["starts_at_local"][-5:] for s in avail(api(), d).json()["slots"]]
    assert got == fx.expected_slots(opens, closes, slot, dur)

def test_closed_day_has_no_slots_and_other_days_do(reset, api):
    d = date(); other = date(8)
    world(reset, api, restaurants=[rest(opening_hours=hours_for(d, "18:00", "23:00"))])
    assert avail(api(), other).json()["slots"] == [] and avail(api(), d).json()["slots"]

def test_availability_body_shape_and_offsets(reset, api):
    d = date(); world(reset, api); b = avail(api(), d, 4).json()
    assert b["restaurant_id"] == "r_anker" and b["date"] == d and b["timezone"] == "Europe/Berlin"
    s = b["slots"][0]; assert s["starts_at_local"] == f"{d}T18:00" and s["starts_at"].startswith(f"{d}T18:00:00") and s["starts_at"][-6:] in ("+01:00", "+02:00")

def test_available_tables_filter_by_capacity_in_fixture_order(reset, api):
    d = date(); world(reset, api, restaurants=[rest(tables=[{"id": "t_b", "label": "B", "capacity": 6}, {"id": "t_a", "label": "A", "capacity": 2}, {"id": "t_c", "label": "C", "capacity": 4}])])
    for party, want in ((1, ["t_b", "t_a", "t_c"]), (3, ["t_b", "t_c"]), (5, ["t_b"]), (7, [])):
        assert slot(avail(api(), d, party), "19:00")["available_table_ids"] == want

def test_a_slot_with_no_table_still_appears(reset, api):
    d = date(); world(reset, api); r = avail(api(), d, 99)
    assert len(r.json()["slots"]) == len(fx.expected_slots()) and all(s["available_table_ids"] == [] for s in r.json()["slots"])

def test_occupancy_is_half_open(reset, api):
    d = date(); world(reset, api); a = ada(api); assert book(a, d, "t_2", "19:00").status_code == 201
    free = lambda h: "t_2" in slot(avail(api(), d), h)["available_table_ids"]
    assert not free("18:00") and not free("18:30") and not free("19:00") and not free("20:00") and free("20:30") and free("21:00")

def test_cancelled_booking_frees_the_slot(reset, api):
    d = date(); world(reset, api); a = ada(api); ref = book(a, d).json()["reference"]
    assert "t_2" not in slot(avail(api(), d), "19:00")["available_table_ids"]
    assert_status(a.post(f"/reservations/{ref}/cancel"), 200)
    assert "t_2" in slot(avail(api(), d), "19:00")["available_table_ids"]

@pytest.mark.parametrize("q", [{"date": "2026-10-12", "party_size": 2}, {"restaurant_id": "r_anker", "party_size": 2}, {"restaurant_id": "r_anker", "date": "2026-10-12"}])
def test_missing_parameter_is_422(reset, api, q):
    world(reset, api); assert_error(api().get("/availability", params=q), 422, "validation_failed")

@pytest.mark.parametrize("bad", ["4.0", "+4", "1e9", "abc", "0", "-1", "", "٤"])
def test_bad_party_size_is_422(reset, api, bad):
    world(reset, api); assert_error(api().get("/availability", params={"restaurant_id": "r_anker", "date": date(), "party_size": bad}), 422, "validation_failed")

@pytest.mark.parametrize("bad", ["2026-02-30", "2026-13-01", "24-09-2026", "2026-9-4", "tomorrow", ""])
def test_bad_date_is_422(reset, api, bad):
    world(reset, api); assert_error(api().get("/availability", params={"restaurant_id": "r_anker", "date": bad, "party_size": 2}), 422, "validation_failed")

def test_unknown_restaurant_is_404(reset, api):
    world(reset, api); assert_error(api().get("/availability", params={"restaurant_id": "nope", "date": date(), "party_size": 2}), 404, "not_found")

def test_availability_is_per_restaurant(reset, api):
    d = date(); world(reset, api, restaurants=[rest(), rest("r_b", tables=[{"id": "t_9", "label": "9", "capacity": 8}])])
    assert slot(avail(api(), d, 2, "r_b"), "19:00")["available_table_ids"] == ["t_9"]
