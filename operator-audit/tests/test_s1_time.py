"""Stage 1 §9: time zones and daylight saving."""
import pytest
from kit import *
pytestmark = pytest.mark.s1

def night(tz, d, weekday, dur=60):
    return rest(timezone=tz, slot_minutes=30, reservation_duration_minutes=dur, opening_hours=[{"weekday": weekday, "opens": "00:00", "closes": "06:00"}])

def times(resp): return {s["starts_at_local"][-5:]: s["starts_at"][-6:] for s in resp.json()["slots"]}

CASES = {"berlin_spring": ("Europe/Berlin", "2026-03-29", "sun"), "berlin_fall": ("Europe/Berlin", "2026-10-25", "sun"),
         "ny_spring": ("America/New_York", "2026-03-08", "sun"), "ny_fall": ("America/New_York", "2026-11-01", "sun")}

def setup(reset, api, key, dur=60):
    tz, d, wd = CASES[key]; world(reset, api, restaurants=[night(tz, d, wd, dur)]); return d, tz

def test_berlin_spring_forward_hides_the_skipped_hour(reset, api):
    d, _ = setup(reset, api, "berlin_spring"); t = times(avail(api(), d, 2))
    assert "02:00" not in t and "02:30" not in t and t["01:30"] == "+01:00" and t["03:00"] == "+02:00" and t["00:00"] == "+01:00" and t["05:00"] == "+02:00"
    assert_error(book(ada(api), d, "t_2", "02:30"), 422, "invalid_local_time"); assert_error(book(ada(api), d, "t_2", "02:00"), 422, "invalid_local_time")

def test_ny_spring_forward(reset, api):
    d, _ = setup(reset, api, "ny_spring"); t = times(avail(api(), d, 2))
    assert "02:00" not in t and "02:30" not in t and t["01:30"] == "-05:00" and t["03:00"] == "-04:00"
    assert_error(book(ada(api), d, "t_2", "02:30"), 422, "invalid_local_time")

def test_berlin_fall_back_uses_first_occurrence_once(reset, api):
    d, _ = setup(reset, api, "berlin_fall"); r = avail(api(), d, 2); t = times(r)
    assert [s["starts_at_local"][-5:] for s in r.json()["slots"]].count("02:00") == 1 and t["02:00"] == "+02:00" and t["02:30"] == "+02:00" and t["03:00"] == "+01:00" and t["01:30"] == "+02:00"
    b = assert_status(book(ada(api), d, "t_2", "02:00"), 201).json(); assert b["starts_at"].endswith("+02:00") and b["starts_at"][11:16] == "02:00"

def test_ny_fall_back_first_occurrence(reset, api):
    d, _ = setup(reset, api, "ny_fall"); t = times(avail(api(), d, 2))
    assert t["01:00"] == "-04:00" and t["01:30"] == "-04:00" and t["02:00"] == "-05:00" and t["00:30"] == "-04:00"

def test_duration_is_absolute_time_across_fall_back(reset, api):
    d, _ = setup(reset, api, "berlin_fall", dur=90); b = assert_status(book(ada(api), d, "t_2", "01:30"), 201).json()
    assert b["starts_at"] == f"{d}T01:30:00+02:00" and b["ends_at"] == f"{d}T02:00:00+01:00"
    # 01:30 CEST + 90 min = 02:00 CET (second 02:00); a booking starting at the first 02:00 CEST overlaps it
    assert "t_2" not in slot(avail(api(), d, 2), "02:30")["available_table_ids"] and "t_2" in slot(avail(api(), d, 2), "03:00")["available_table_ids"]

def test_duration_is_absolute_time_across_spring_forward(reset, api):
    d, _ = setup(reset, api, "berlin_spring", dur=90); b = assert_status(book(ada(api), d, "t_2", "01:30"), 201).json()
    assert b["ends_at"] == f"{d}T04:00:00+02:00"
    d2, _ = setup(reset, api, "ny_spring", dur=60); b = assert_status(book(ada(api), d2, "t_2", "01:30"), 201).json()
    assert b["starts_at"] == f"{d2}T01:30:00-05:00" and b["ends_at"] == f"{d2}T03:30:00-04:00"

@pytest.mark.parametrize("tz,off_summer,off_winter", [("Europe/Berlin", "+02:00", "+01:00"), ("America/New_York", "-04:00", "-05:00"), ("Asia/Tokyo", "+09:00", "+09:00")])
def test_ordinary_offsets_follow_the_zone(reset, api, tz, off_summer, off_winter):
    world(reset, api, restaurants=[rest(timezone=tz)]); c = api()
    assert slot(avail(c, "2026-07-15"), "19:00")["starts_at"].endswith(off_summer) and slot(avail(c, "2026-01-15"), "19:00")["starts_at"].endswith(off_winter)

def test_a_booking_before_the_gap_and_one_after_do_not_collide(reset, api):
    d, _ = setup(reset, api, "berlin_spring", dur=60); a = ada(api)
    assert_status(book(a, d, "t_2", "01:00"), 201); assert_status(book(a, d, "t_2", "03:00"), 201)
