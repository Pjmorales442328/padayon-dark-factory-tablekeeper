"""DST / time zone checks (ledger 70, 82-86). Expected offsets are hard-coded from IANA rules."""
from common import Base, fixture, hours, table, WD

DE_SPRING, DE_FALL = "2026-03-29", "2026-10-25"
NY_SPRING, NY_FALL = "2026-03-08", "2026-11-01"
DE_SPRING27, DE_FALL27 = "2027-03-28", "2027-10-31"
NY_SPRING27, NY_FALL27 = "2027-03-14", "2027-11-07"


def times(slots):
    return [s["starts_at_local"][11:] for s in slots]


class Dst(Base):
    def slots(self, rest, date):
        return self.avail(rest, date)["slots"]

    def offs(self, rest, date):
        return {s["starts_at_local"][11:]: s["starts_at"][19:] for s in self.slots(rest, date)}

    def test_L082_L085_berlin_spring_availability(self):
        self.assertEqual(times(self.slots("r_dst_de", DE_SPRING)),
                         ["00:00", "00:30", "01:00", "01:30", "03:00", "03:30", "04:00", "04:30"])
        o = self.offs("r_dst_de", DE_SPRING)
        self.assertEqual([o[k] for k in ("00:00", "01:30")], ["+01:00", "+01:00"])
        self.assertEqual([o[k] for k in ("03:00", "04:30")], ["+02:00", "+02:00"])
        s = self.slot_map("r_dst_de", DE_SPRING)
        self.assertEqual(s[f"{DE_SPRING}T03:00"]["starts_at"], f"{DE_SPRING}T03:00:00+02:00")

    def test_L070_L082_berlin_spring_gap_rejected(self):
        for t in ("02:00", "02:30"):
            self.err(self.book(self.ada, f"{DE_SPRING}T{t}", rest="r_dst_de", table="t_1"), 422, "invalid_local_time")
        self.assertEqual(self.book(self.ada, f"{DE_SPRING}T03:00", rest="r_dst_de", table="t_1").status, 201)
        self.assertEqual(self.book(self.ada, f"{DE_SPRING}T01:30", rest="r_dst_de", table="t_2").status, 201)

    def test_L082_amend_into_gap_rejected_future_year(self):
        j = self.ok_book(self.ada, f"{DE_SPRING27}T01:00", rest="r_dst_de", table="t_1")
        r = self.api.call("PATCH", f"/reservations/{j['reference']}", {"starts_at_local": f"{DE_SPRING27}T02:30"},
                          token=self.ada)
        self.err(r, 422, "invalid_local_time")
        self.assertEqual(self.api.call("GET", f"/reservations/{j['reference']}", token=self.ada).json, j)
        r = self.api.call("POST", "/reservation-moves", {"moves": [{"reference": j["reference"],
                                                                   "starts_at_local": f"{DE_SPRING27}T02:00"}]},
                          token=self.ada, key="gap")
        self.err(r, 422, "invalid_local_time")
        self.assertEqual(times(self.slots("r_dst_de", DE_SPRING27))[:5], ["00:00", "00:30", "01:00", "01:30", "03:00"])

    def test_L084_berlin_spring_duration_is_absolute(self):
        j = self.ok_book(self.ada, f"{DE_SPRING}T01:30", rest="r_dst_de", table="t_1")
        self.assertEqual(j["starts_at"], f"{DE_SPRING}T01:30:00+01:00")
        self.assertEqual(j["ends_at"], f"{DE_SPRING}T04:00:00+02:00")
        m = self.slot_map("r_dst_de", DE_SPRING)
        free = lambda k: "t_1" in m[f"{DE_SPRING}T{k}"]["available_table_ids"]
        # occupies [00:30Z, 02:00Z): 03:00 local is 01:00Z, 03:30 is 01:30Z -> still busy; 04:00 is 02:00Z -> free
        self.assertFalse(free("03:00"))
        self.assertFalse(free("03:30"))
        self.assertTrue(free("04:00"))
        self.assertFalse(free("00:30"))     # [23:30Z, 01:00Z) overlaps
        self.assertTrue(free("00:00"))      # [23:00Z, 00:30Z) adjacent
        self.err(self.book(self.bob, f"{DE_SPRING}T03:30", rest="r_dst_de", table="t_1"), 409, "table_unavailable")
        self.assertEqual(self.book(self.bob, f"{DE_SPRING}T04:00", rest="r_dst_de", table="t_1").status, 201)

    def test_L084_berlin_spring_closing_uses_absolute_time(self):
        f = fixture()
        f["restaurants"][2]["opening_hours"] = hours("00:00", "03:30")
        self.reset(f)
        self.assertEqual(times(self.slots("r_dst_de", DE_SPRING)), ["00:00", "00:30", "01:00"])
        self.err(self.book(self.ada, f"{DE_SPRING}T01:30", rest="r_dst_de"), 422, "outside_opening_hours")
        self.assertEqual(self.book(self.ada, f"{DE_SPRING}T01:00", rest="r_dst_de").status, 201)   # ends 03:30 exactly

    def test_L083_L085_berlin_fall_availability(self):
        sl = self.slots("r_dst_de", DE_FALL)
        t = times(sl)
        self.assertEqual(t, ["00:00", "00:30", "01:00", "01:30", "02:00", "02:30", "03:00", "03:30", "04:00", "04:30"])
        self.assertEqual(len(set(t)), len(t))
        o = self.offs("r_dst_de", DE_FALL)
        for k in ("00:00", "01:30", "02:00", "02:30"):
            self.assertEqual(o[k], "+02:00", k)       # first occurrence
        for k in ("03:00", "04:30"):
            self.assertEqual(o[k], "+01:00", k)

    def test_L083_L084_berlin_fall_booking_fold(self):
        j = self.ok_book(self.ada, f"{DE_FALL}T02:00", rest="r_dst_de", table="t_1")
        self.assertEqual(j["starts_at"], f"{DE_FALL}T02:00:00+02:00")
        self.assertEqual(j["ends_at"], f"{DE_FALL}T02:30:00+01:00")      # 90 real minutes later
        j2 = self.ok_book(self.ada, f"{DE_FALL}T01:30", rest="r_dst_de", table="t_2")
        self.assertEqual(j2["starts_at"], f"{DE_FALL}T01:30:00+02:00")
        self.assertEqual(j2["ends_at"], f"{DE_FALL}T02:00:00+01:00")     # reads 02:00, not 03:00
        self.reset()
        j3 = self.ok_book(self.ada, f"{DE_FALL}T02:30", rest="r_dst_de", table="t_2", party=1)
        self.assertEqual(j3["ends_at"], f"{DE_FALL}T03:00:00+01:00")

    def test_L084_berlin_fall_occupancy_absolute(self):
        self.ok_book(self.ada, f"{DE_FALL}T02:30", rest="r_dst_de", table="t_1")      # [00:30Z, 02:00Z)
        m = self.slot_map("r_dst_de", DE_FALL)
        free = lambda k: "t_1" in m[f"{DE_FALL}T{k}"]["available_table_ids"]
        self.assertTrue(free("03:00"))      # 03:00 CET = 02:00Z adjacent (wall-clock arithmetic would call it busy)
        self.assertTrue(free("03:30"))
        self.assertFalse(free("02:00"))
        self.assertFalse(free("02:30"))
        self.assertFalse(free("01:30"))     # [23:30Z, 01:00Z) overlaps
        self.assertTrue(free("01:00"))      # [23:00Z, 00:30Z) adjacent
        self.assertEqual(self.book(self.bob, f"{DE_FALL}T03:00", rest="r_dst_de", table="t_1").status, 201)

    def test_L084_berlin_fall_closing_uses_absolute_time(self):
        f = fixture()
        f["restaurants"][2]["opening_hours"] = hours("00:00", "03:30")
        self.reset(f)
        self.assertEqual(times(self.slots("r_dst_de", DE_FALL)), ["00:00", "00:30", "01:00", "01:30", "02:00", "02:30"])

    def test_L085_berlin_future_year_fall_amend(self):
        j = self.ok_book(self.ada, f"{DE_FALL27}T01:00", rest="r_dst_de", table="t_1")
        r = self.api.call("PATCH", f"/reservations/{j['reference']}", {"starts_at_local": f"{DE_FALL27}T02:30"},
                          token=self.ada)
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json["starts_at"], f"{DE_FALL27}T02:30:00+02:00")
        self.assertEqual(r.json["ends_at"], f"{DE_FALL27}T03:00:00+01:00")

    def test_L086_ny_spring(self):
        self.assertEqual(times(self.slots("r_dst_ny", NY_SPRING)),
                         ["00:00", "00:30", "01:00", "01:30", "03:00", "03:30", "04:00", "04:30"])
        o = self.offs("r_dst_ny", NY_SPRING)
        self.assertEqual((o["01:30"], o["03:00"]), ("-05:00", "-04:00"))
        for t in ("02:00", "02:30"):
            self.err(self.book(self.ada, f"{NY_SPRING}T{t}", rest="r_dst_ny"), 422, "invalid_local_time")
        j = self.ok_book(self.ada, f"{NY_SPRING}T01:30", rest="r_dst_ny", table="t_1")
        self.assertEqual(j["starts_at"], f"{NY_SPRING}T01:30:00-05:00")
        self.assertEqual(j["ends_at"], f"{NY_SPRING}T04:00:00-04:00")
        m = self.slot_map("r_dst_ny", NY_SPRING)
        self.assertNotIn("t_1", m[f"{NY_SPRING}T03:30"]["available_table_ids"])
        self.assertIn("t_1", m[f"{NY_SPRING}T04:00"]["available_table_ids"])

    def test_L083_L086_ny_fall(self):
        t = times(self.slots("r_dst_ny", NY_FALL))
        self.assertEqual(t, ["00:00", "00:30", "01:00", "01:30", "02:00", "02:30", "03:00", "03:30", "04:00", "04:30"])
        o = self.offs("r_dst_ny", NY_FALL)
        for k in ("00:00", "01:00", "01:30"):
            self.assertEqual(o[k], "-04:00", k)
        for k in ("02:00", "02:30", "04:30"):
            self.assertEqual(o[k], "-05:00", k)
        j = self.ok_book(self.ada, f"{NY_FALL}T01:30", rest="r_dst_ny", table="t_1")
        self.assertEqual(j["starts_at"], f"{NY_FALL}T01:30:00-04:00")
        self.assertEqual(j["ends_at"], f"{NY_FALL}T02:00:00-05:00")
        j = self.ok_book(self.ada, f"{NY_FALL}T01:00", rest="r_dst_ny", table="t_2")
        self.assertEqual(j["starts_at"], f"{NY_FALL}T01:00:00-04:00")
        self.assertEqual(j["ends_at"], f"{NY_FALL}T01:30:00-05:00")

    def test_L086_ny_future_years(self):
        self.assertEqual(times(self.slots("r_dst_ny", NY_SPRING27))[3:5], ["01:30", "03:00"])
        self.err(self.book(self.ada, f"{NY_SPRING27}T02:00", rest="r_dst_ny"), 422, "invalid_local_time")
        j = self.ok_book(self.ada, f"{NY_FALL27}T01:30", rest="r_dst_ny", table="t_1")
        self.assertEqual((j["starts_at"], j["ends_at"]), (f"{NY_FALL27}T01:30:00-04:00", f"{NY_FALL27}T02:00:00-05:00"))

    def test_L085_L086_ordinary_days_offsets(self):
        o = self.offs("r_dst_de", "2026-07-01")["00:00"]
        self.assertEqual(o, "+02:00")
        self.assertEqual(self.offs("r_dst_de", "2026-01-15")["00:00"], "+01:00")
        self.assertEqual(self.offs("r_dst_ny", "2026-07-01")["00:00"], "-04:00")
        self.assertEqual(self.offs("r_dst_ny", "2026-01-15")["00:00"], "-05:00")
        # the day before / after the transitions
        self.assertEqual(self.offs("r_dst_de", "2026-03-28")["00:00"], "+01:00")
        self.assertEqual(self.offs("r_dst_de", "2026-03-30")["00:00"], "+02:00")
        self.assertEqual(self.offs("r_dst_de", "2026-10-24")["00:00"], "+02:00")
        self.assertEqual(self.offs("r_dst_de", "2026-10-26")["00:00"], "+01:00")
        self.assertEqual(self.offs("r_dst_ny", "2026-03-07")["00:00"], "-05:00")
        self.assertEqual(self.offs("r_dst_ny", "2026-03-09")["00:00"], "-04:00")
        self.assertEqual(self.offs("r_dst_ny", "2026-10-31")["00:00"], "-04:00")
        self.assertEqual(self.offs("r_dst_ny", "2026-11-02")["00:00"], "-05:00")

    def test_L084_cross_zone_same_instant_no_interference(self):
        # same table id in different restaurants never conflict even at the same instant
        a = self.ok_book(self.ada, "2026-07-01T01:00", rest="r_dst_de", table="t_1")
        b = self.ok_book(self.ada, "2026-07-01T01:00", rest="r_dst_ny", table="t_1")
        self.assertEqual(a["starts_at"][-6:], "+02:00")
        self.assertEqual(b["starts_at"][-6:], "-04:00")
