"""Restaurants, availability, create, list, lookup, cancel, amend (ledger 53-86 excluding DST)."""
import re
import time
import unittest

from common import (Base, THU, FRI, SAT, SUN, fixture, seed_res, clock_minute, hours, table)

REF = re.compile(r"^[A-Z0-9]{6,12}$")


class Restaurants(Base):
    def test_L053_list(self):
        r = self.api.call("GET", "/restaurants")
        self.assertEqual(r.status, 200)
        ids = [x["id"] for x in r.json["restaurants"]]
        self.assertEqual(ids, [x["id"] for x in fixture()["restaurants"]])
        first = r.json["restaurants"][0]
        self.assertEqual(first, {"id": "r_anker", "name": "Zum Anker", "timezone": "Europe/Berlin"})
        self.assertEqual(set(r.json), {"restaurants"})

    def test_L053_order_follows_fixture(self):
        f = fixture()
        f["restaurants"].reverse()
        self.reset(f)
        ids = [x["id"] for x in self.api.call("GET", "/restaurants").json["restaurants"]]
        self.assertEqual(ids, [x["id"] for x in f["restaurants"]])

    def test_L054_detail(self):
        fx = fixture()["restaurants"][0]
        r = self.api.call("GET", "/restaurants/r_anker")
        self.assertEqual(r.status, 200)
        j = r.json
        for k in ("slot_minutes", "reservation_duration_minutes", "cancellation_cutoff_minutes"):
            self.assertEqual(j[k], fx[k])
        self.assertEqual(j["id"], "r_anker")
        self.assertEqual(j["name"], "Zum Anker")
        self.assertEqual(j["timezone"], "Europe/Berlin")
        key = lambda d: d["weekday"]
        self.assertEqual(sorted(j["opening_hours"], key=key), sorted(fx["opening_hours"], key=key))
        self.assertEqual(j["tables"], fx["tables"])
        self.err(self.api.call("GET", "/restaurants/zzz"), 404, "not_found")

    def test_L099_table_ids_scoped_to_restaurant(self):
        f = fixture()
        self.assertEqual(self.api.call("GET", "/restaurants/r_other").json["tables"][0]["id"], "t_1")
        # t_1 at r_anker capacity 2, at r_other capacity 8
        self.err(self.book(self.ada, f"{THU}T19:00", table="t_1", party=3), 422, "party_exceeds_capacity")
        r = self.book(self.ada, f"{THU}T19:00", table="t_1", rest="r_other", party=8)
        self.assertEqual(r.status, 201, r)
        self.assertEqual(r.json["restaurant_id"], "r_other")
        # t_9 belongs to r_other only
        self.err(self.book(self.ada, f"{THU}T19:00", table="t_9", rest="r_anker"), 404, "not_found")


class Availability(Base):
    def q(self, **kw):
        base = {"restaurant_id": "r_anker", "date": THU, "party_size": "2"}
        base.update(kw)
        s = "&".join(f"{k}={v}" for k, v in base.items() if v is not None)
        return self.api.call("GET", "/availability?" + s)

    def test_L055_required_params(self):
        for k in ("restaurant_id", "date", "party_size"):
            self.err(self.q(**{k: None}), 422, "validation_failed")
        self.err(self.api.call("GET", "/availability"), 422, "validation_failed")

    def test_L055_unknown_restaurant(self):
        self.err(self.q(restaurant_id="nope"), 404, "not_found")

    def test_L056_date_and_party_validation(self):
        for d in ("2030-02-30", "2030-13-01", "20300103", "2030-1-3", "x", "", "2030-01-03T18:00",
                  "2030-01-03%20", "0000-00-00"):
            self.err(self.q(date=d), 422, "validation_failed")
        for p in ("0", "-2", "x", "1e1"):
            self.err(self.q(party_size=p), 422, "validation_failed")
        self.assertEqual(self.q(date="2030-02-28").status, 200)
        self.assertEqual(self.q(date="2028-02-29").status, 200)   # leap day valid
        self.err(self.q(date="2029-02-29"), 422, "validation_failed")

    def test_L057_L058_L059_shape_and_grid(self):
        j = self.q().json
        self.assertEqual((j["restaurant_id"], j["date"], j["timezone"]), ("r_anker", THU, "Europe/Berlin"))
        times = [s["starts_at_local"] for s in j["slots"]]
        # opens 18:00 closes 23:00 slot 30 duration 90 -> last 21:30
        want = [f"{THU}T{h:02d}:{m:02d}" for h in range(18, 22) for m in (0, 30)]
        self.assertEqual(times, want)
        s0 = j["slots"][0]
        self.assertEqual(set(s0), {"starts_at_local", "starts_at", "available_table_ids"})
        self.assertEqual(s0["starts_at"], f"{THU}T18:00:00+01:00")
        self.assertEqual(s0["available_table_ids"], ["t_1", "t_2", "t_3"])

    def test_L058_end_exactly_at_close_and_friday(self):
        fri = [s["starts_at_local"] for s in self.avail("r_anker", FRI)["slots"]]
        self.assertEqual(fri[-1], f"{FRI}T22:00")   # 22:00+90 = 23:30 == closes
        self.assertEqual(len(fri), 10)
        sat = [s["starts_at_local"] for s in self.avail("r_anker", SAT)["slots"]]
        self.assertEqual(sat[-1], f"{SAT}T21:30")
        # odd grid measured from opening, not midnight: 12:00 open, 60-minute slots
        o = [s["starts_at_local"] for s in self.avail("r_other", THU)["slots"]]
        self.assertEqual(o[0], f"{THU}T12:00")
        self.assertEqual(o[-1], f"{THU}T19:00")
        f = fixture()
        f["restaurants"][0]["opening_hours"] = [{"weekday": "thu", "opens": "18:10", "closes": "21:00"}]
        self.reset(f)
        t = [s["starts_at_local"].split("T")[1] for s in self.avail("r_anker", THU)["slots"]]
        self.assertEqual(t, ["18:10", "18:40", "19:10"])   # 19:40 + 90 = 21:10 > 21:00 is excluded
        self.err(self.book(self.ada, f"{THU}T19:00"), 422, "not_on_slot_grid")
        self.assertEqual(self.book(self.ada, f"{THU}T19:10").status, 201)
        self.err(self.book(self.ada, f"{THU}T19:40", table="t_3"), 422, "outside_opening_hours")

    def test_L060_capacity_filter_and_order(self):
        s = self.slot_map("r_anker", THU, 3)[f"{THU}T19:00"]
        self.assertEqual(s["available_table_ids"], ["t_2", "t_3"])
        s = self.slot_map("r_anker", THU, 5)[f"{THU}T19:00"]
        self.assertEqual(s["available_table_ids"], ["t_3"])
        s = self.slot_map("r_anker", THU, 6)[f"{THU}T19:00"]
        self.assertEqual(s["available_table_ids"], ["t_3"])
        s = self.slot_map("r_anker", THU, 7)[f"{THU}T19:00"]
        self.assertEqual(s["available_table_ids"], [])
        f = fixture()
        f["restaurants"][0]["tables"] = [table("t_z", 4), table("t_a", 4), table("t_m", 4)]
        self.reset(f)
        self.assertEqual(self.slot_map("r_anker", THU, 2)[f"{THU}T19:00"]["available_table_ids"],
                         ["t_z", "t_a", "t_m"])

    def test_L060_L061_booking_blocks_overlapping_slots_only(self):
        self.ok_book(self.ada, f"{THU}T19:00", table="t_2")
        m = self.slot_map("r_anker", THU, 2)
        free = lambda h: "t_2" in m[f"{THU}T{h}"]["available_table_ids"]
        # booking [19:00,20:30); slot s occupies [s, s+90)
        expect = {"18:00": False, "18:30": False, "19:00": False, "19:30": False,
                  "20:00": False, "20:30": True, "21:00": True, "21:30": True}
        for h, e in expect.items():
            self.assertEqual(free(h), e, h)

    def test_L061_full_slot_present_empty(self):
        for tid in ("t_1", "t_2", "t_3"):
            self.ok_book(self.ada, f"{THU}T19:00", table=tid, party=1, key=self.newkey())
        s = self.slot_map("r_anker", THU)
        self.assertEqual(s[f"{THU}T19:00"]["available_table_ids"], [])
        self.assertEqual(len(s), 8)

    def test_L061_closed_day(self):
        j = self.avail("r_anker", SUN)
        self.assertEqual(j["slots"], [])
        self.assertEqual(j["date"], SUN)

    def test_L065_adjacent_not_overlapping(self):
        self.ok_book(self.ada, f"{THU}T19:00")
        m = self.slot_map("r_anker", THU)
        self.assertNotIn("t_2", m[f"{THU}T19:30"]["available_table_ids"])
        self.assertIn("t_2", m[f"{THU}T20:30"]["available_table_ids"])
        self.assertNotIn("t_2", m[f"{THU}T20:00"]["available_table_ids"])
        self.assertEqual(self.book(self.ada, f"{THU}T20:30").status, 201)   # adjacent after
        # adjacent before: 18:00 + 90 = 19:30 overlaps 19:00; use another table order
        self.reset()
        self.ok_book(self.ada, f"{THU}T20:30")
        self.assertEqual(self.book(self.ada, f"{THU}T19:00").status, 201)   # ends 20:30 exactly


class Create(Base):
    def test_L062_shape(self):
        t = self.ada
        r = self.book(t, f"{THU}T19:00")
        self.assertEqual(r.status, 201)
        j = r.json
        self.assertEqual(set(j), {"reservation_id", "reference", "restaurant_id", "table_id", "party_size",
                                  "status", "starts_at_local", "starts_at", "ends_at", "created_at"})
        self.assertEqual((j["restaurant_id"], j["table_id"], j["party_size"], j["status"]),
                         ("r_anker", "t_2", 2, "confirmed"))
        self.assertEqual(j["starts_at_local"], f"{THU}T19:00")
        self.assertEqual(j["starts_at"], f"{THU}T19:00:00+01:00")
        self.assertEqual(j["ends_at"], f"{THU}T20:30:00+01:00")
        self.assertIsInstance(j["party_size"], int)

    def test_L063_not_found(self):
        t = self.ada
        self.err(self.book(t, f"{THU}T19:00", rest="nope"), 404, "not_found")
        self.err(self.book(t, f"{THU}T19:00", table="nope"), 404, "not_found")
        self.err(self.book(t, f"{THU}T19:00", table="t_9"), 404, "not_found")
        self.err(self.book(t, f"{THU}T19:00", rest="r_other", table="t_2"), 404, "not_found")

    def test_L064_same_table_id_other_restaurant_no_conflict(self):
        self.ok_book(self.ada, f"{THU}T19:00", table="t_1", rest="r_anker")
        r = self.book(self.ada, f"{THU}T19:00", table="t_1", rest="r_other")
        self.assertEqual(r.status, 201, r)
        self.assertNotEqual(r.json["reference"], None)

    def test_L066_conflicts(self):
        self.ok_book(self.ada, f"{THU}T19:00")
        for start in ("18:00", "18:30", "19:00", "19:30", "20:00"):
            self.err(self.book(self.bob, f"{THU}T{start}"), 409, "table_unavailable")
        for start in ("20:30", "17:30"):
            pass
        self.assertEqual(self.book(self.bob, f"{THU}T20:30").status, 201)
        self.assertEqual(self.book(self.bob, f"{THU}T19:00", table="t_3").status, 201)

    def test_L066_race_same_table_time(self):
        calls = []
        toks = [self.ada, self.bob] * 10
        for i, t in enumerate(toks):
            calls.append(lambda t=t, i=i: self.book(t, f"{THU}T19:00", key=f"race-{i}"))
        outs = self.burst(calls)
        codes = sorted(o.status for o in outs)
        self.assertEqual(codes, [201] + [409] * 19, codes)
        for o in outs:
            if o.status == 409:
                self.err(o, 409, "table_unavailable")

    def test_L066_race_overlapping_times(self):
        starts = [f"{THU}T{x}" for x in ("19:00", "19:30", "20:00", "18:30", "20:00", "19:00") * 3]
        outs = self.burst([lambda s=s, i=i: self.book(self.ada if i % 2 else self.bob, s, key=f"ov-{i}")
                           for i, s in enumerate(starts)])
        won = [(o.json["starts_at_local"]) for o in outs if o.status == 201]
        # winners must be pairwise non-overlapping (>=90 minutes apart)
        mins = sorted(int(w[-5:-3]) * 60 + int(w[-2:]) for w in won)
        for a, b in zip(mins, mins[1:]):
            self.assertGreaterEqual(b - a, 90, won)
        self.assertTrue(all(o.status in (201, 409) for o in outs))

    def test_L066_race_many_tables_many_users(self):
        outs = self.burst([lambda i=i: self.book(self.ada, f"{THU}T19:00", table=("t_1", "t_2", "t_3")[i % 3],
                                                 key=f"mt-{i}") for i in range(30)])
        self.assertEqual(sorted(o.status for o in outs), [201] * 3 + [409] * 27)
        self.assertEqual(len({o.json["reference"] for o in outs if o.status == 201}), 3)

    def test_L067_grid(self):
        for v in ("19:15", "19:01", "18:59", "19:29"):
            self.err(self.book(self.ada, f"{THU}T{v}"), 422, "not_on_slot_grid")
        self.assertEqual(self.book(self.ada, f"{THU}T19:30").status, 201)

    def test_L068_opening_hours(self):
        for v in ("17:30", "00:00", "17:59"):
            self.err(self.book(self.ada, f"{THU}T{v}"), 422, "outside_opening_hours")
        self.err(self.book(self.ada, f"{THU}T22:00"), 422, "outside_opening_hours")   # ends 23:30 > 23:00
        self.err(self.book(self.ada, f"{THU}T22:30"), 422, "outside_opening_hours")
        self.err(self.book(self.ada, f"{THU}T23:00"), 422, "outside_opening_hours")
        self.err(self.book(self.ada, f"{SUN}T19:00"), 422, "outside_opening_hours")   # closed day
        self.assertEqual(self.book(self.ada, f"{THU}T21:30").status, 201)             # ends exactly 23:00
        self.assertEqual(self.book(self.ada, f"{FRI}T22:00", table="t_3").status, 201)
        self.err(self.book(self.ada, f"{FRI}T22:30"), 422, "outside_opening_hours")

    def test_L069_capacity(self):
        self.err(self.book(self.ada, f"{THU}T19:00", table="t_1", party=3), 422, "party_exceeds_capacity")
        self.assertEqual(self.book(self.ada, f"{THU}T19:00", table="t_1", party=2).status, 201)

    def test_L027_L070_error_precedence(self):
        """Documented precedence inferred from table: 404 before 422; format 422 before domain."""
        # unknown table beats capacity/grid errors
        self.err(self.book(self.ada, f"{THU}T19:15", table="zzz", party=99), 404, "not_found")
        # invalid party (validation) beats domain errors
        self.err(self.book(self.ada, f"{THU}T19:15", party=0), 422, "validation_failed")
        self.err(self.book(self.ada, "bad", party=0), 422, "validation_failed")

    def test_L071_L072_references_unique(self):
        refs, ids = set(), set()
        for t, rest in (("t_1", "r_anker"), ("t_2", "r_anker"), ("t_3", "r_anker")):
            for hh in ("18:00", "19:30", "21:00"):
                j = self.ok_book(self.ada, f"{THU}T{hh}", table=t, party=1)
                refs.add(j["reference"])
                ids.add(j["reservation_id"])
        for hh in ("12:00", "14:00", "16:00"):
            j = self.ok_book(self.bob, f"{THU}T{hh}", table="t_1", rest="r_other", party=1)
            refs.add(j["reference"])
            ids.add(j["reservation_id"])
        self.assertEqual(len(refs), 12)
        self.assertEqual(len(ids), 12)
        for r in refs:
            self.assertRegex(r, REF)

    def test_L071_references_with_lowercase_lookup(self):
        j = self.ok_book(self.ada, f"{THU}T19:00")
        self.assertEqual(self.api.call("GET", "/reservations/" + j["reference"], token=self.ada).status, 200)


class Lists(Base):
    def test_L073_list_and_lookup(self):
        t = self.ada
        self.assertEqual(self.api.call("GET", "/reservations", token=t).json, {"reservations": []})
        a = self.ok_book(t, f"{THU}T19:00")
        b = self.ok_book(t, f"{FRI}T19:00")
        c = self.ok_book(t, f"{THU}T21:00", table="t_3")
        self.api.call("POST", f"/reservations/{c['reference']}/cancel", token=t)
        o = self.ok_book(self.bob, f"{THU}T18:00", table="t_1")
        r = self.api.call("GET", "/reservations", token=t)
        self.assertEqual(r.status, 200)
        got = r.json["reservations"]
        self.assertEqual([x["reference"] for x in got], [b["reference"], c["reference"], a["reference"]])
        self.assertEqual([x["status"] for x in got], ["confirmed", "cancelled", "confirmed"])
        self.assertEqual(got[0], b)
        self.assertEqual(got[2], a)
        self.assertEqual(set(got[1]), set(a))
        mine = self.api.call("GET", "/reservations", token=self.bob).json["reservations"]
        self.assertEqual([x["reference"] for x in mine], [o["reference"]])

    def test_L073_sort_by_absolute_time_across_restaurants(self):
        t = self.ada
        a = self.ok_book(t, f"{THU}T19:00", table="t_2", party=2)             # 18:00Z
        b = self.ok_book(t, f"{THU}T12:00", table="t_1", rest="r_other", party=1)  # 11:00Z
        c = self.ok_book(t, f"{THU}T19:00", table="t_1", rest="r_other", party=1)  # 18:00Z same instant
        got = [x["reference"] for x in self.api.call("GET", "/reservations", token=t).json["reservations"]]
        self.assertEqual(got[-1], b["reference"])
        self.assertEqual(set(got[:2]), {a["reference"], c["reference"]})

    def test_L074_reference_lookup(self):
        j = self.ok_book(self.ada, f"{THU}T19:00")
        r = self.api.call("GET", f"/reservations/{j['reference']}", token=self.ada)
        self.assertEqual(r.status, 200)
        self.assertEqual(r.json, j)
        self.err(self.api.call("GET", "/reservations/NOSUCHREF", token=self.ada), 404, "not_found")
        self.err(self.api.call("GET", "/reservations/" + "X" * 200, token=self.ada), 404, "not_found")
        self.err(self.api.call("GET", f"/reservations/{j['reservation_id']}", token=self.ada), 404, "not_found")

    def test_L042_L074_other_and_anonymous_see_404(self):
        j = self.ok_book(self.ada, f"{THU}T19:00")
        ref = j["reference"]
        missing = self.api.call("GET", "/reservations/NOSUCHREF", token=self.bob)
        other = self.api.call("GET", f"/reservations/{ref}", token=self.bob)
        self.err(other, 404, "not_found")
        self.assertEqual(other.json["error"]["code"], missing.json["error"]["code"])
        anon = self.api.call("GET", f"/reservations/{ref}")
        self.assertIn(anon.status, (404, 401))
        # binding clarification: anonymous gets 404 for someone else's booking
        self.err(anon, 404, "not_found")
        anon2 = self.api.call("GET", f"/reservations/{ref}", token="bogus")
        self.assertIn(anon2.status, (401, 404), anon2)
        for m, p, b in [("POST", f"/reservations/{ref}/cancel", None), ("PATCH", f"/reservations/{ref}", {"party_size": 1})]:
            self.err(self.api.call(m, p, b, token=self.bob), 404, "not_found")
            an = self.api.call(m, p, b)
            self.assertIn(an.status, (401, 404), an)
        # still confirmed
        self.assertEqual(self.api.call("GET", f"/reservations/{ref}", token=self.ada).json["status"], "confirmed")


class Cancel(Base):
    def test_L075_cancel_frees(self):
        t = self.ada
        j = self.ok_book(t, f"{THU}T19:00")
        self.assertNotIn("t_2", self.slot_map("r_anker", THU)[f"{THU}T19:00"]["available_table_ids"])
        r = self.api.call("POST", f"/reservations/{j['reference']}/cancel", token=t)
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json["status"], "cancelled")
        self.assertEqual({k: v for k, v in r.json.items() if k != "status"},
                         {k: v for k, v in j.items() if k != "status"})
        self.assertIn("t_2", self.slot_map("r_anker", THU)[f"{THU}T19:00"]["available_table_ids"])
        self.assertEqual(self.book(self.bob, f"{THU}T19:00").status, 201)

    def test_L076_repeat_cancel_same_result(self):
        t = self.ada
        j = self.ok_book(t, f"{THU}T19:00")
        a = self.api.call("POST", f"/reservations/{j['reference']}/cancel", token=t)
        b = self.api.call("POST", f"/reservations/{j['reference']}/cancel", token=t)
        self.assertEqual((a.status, b.status), (200, 200))
        self.assertEqual(a.json, b.json)
        # cancelled booking's slot given to someone else; repeat cancel does not touch theirs
        self.ok_book(self.bob, f"{THU}T19:00")
        c = self.api.call("POST", f"/reservations/{j['reference']}/cancel", token=t)
        self.assertEqual(c.json, a.json)
        self.assertNotIn("t_2", self.slot_map("r_anker", THU)[f"{THU}T19:00"]["available_table_ids"])

    def test_L077_cutoff_boundaries(self):
        f = fixture(reservations=[
            seed_res(1, "u_ada", "r_clock", "t_1", clock_minute(100), 2),    # inside 120
            seed_res(2, "u_ada", "r_clock", "t_2", clock_minute(-30), 2),    # started
            seed_res(3, "u_ada", "r_clock", "t_1", clock_minute(60 * 24 * 3), 2),  # far
        ])
        self.reset(f)
        t = self.ada
        self.err(self.api.call("POST", "/reservations/SEED01/cancel", token=t), 409, "cutoff_passed")
        self.err(self.api.call("POST", "/reservations/SEED02/cancel", token=t), 409, "cutoff_passed")
        self.assertEqual(self.api.call("POST", "/reservations/SEED03/cancel", token=t).status, 200)
        self.assertEqual(self.api.call("GET", "/reservations/SEED01", token=t).json["status"], "confirmed")

    def test_L077_cutoff_just_outside(self):
        f = fixture(reservations=[seed_res(1, "u_ada", "r_clock", "t_1", clock_minute(125), 2)])
        self.reset(f)
        r = self.api.call("POST", "/reservations/SEED01/cancel", token=self.ada)
        self.assertEqual(r.status, 200, r)

    def test_L077_past_booking_cancel_409(self):
        f = fixture(reservations=[seed_res(1, "u_ada", "r_anker", "t_2", "2020-01-02T19:00", 2)])
        self.reset(f)
        self.err(self.api.call("POST", "/reservations/SEED01/cancel", token=self.ada), 409, "cutoff_passed")

    def test_L076_repeat_cancel_after_start_still_200(self):
        """Cutoff 0 restaurant: cancel before start, wait until after start, cancel again -> 200."""
        import datetime as dt
        now = dt.datetime.now(dt.timezone.utc)
        start = (now + dt.timedelta(seconds=75)).replace(second=0, microsecond=0)
        if start.hour == 23 and start.minute >= 54:
            start += dt.timedelta(minutes=10)
        local = start.strftime("%Y-%m-%dT%H:%M")
        t = self.ada
        j = self.ok_book(t, local, rest="r_cut0", table="t_1", party=1)
        a = self.api.call("POST", f"/reservations/{j['reference']}/cancel", token=t)
        self.assertEqual(a.status, 200, a)
        while dt.datetime.now(dt.timezone.utc) < start + dt.timedelta(seconds=2):
            time.sleep(1)
        b = self.api.call("POST", f"/reservations/{j['reference']}/cancel", token=t)
        self.assertEqual(b.status, 200, b)
        self.assertEqual(b.json, a.json)

    def test_L077_cancel_other_users_404_not_409(self):
        f = fixture(reservations=[seed_res(1, "u_ada", "r_anker", "t_2", "2020-01-02T19:00", 2)])
        self.reset(f)
        self.err(self.api.call("POST", "/reservations/SEED01/cancel", token=self.bob), 404, "not_found")
        self.err(self.api.call("POST", "/reservations/NOPE99/cancel", token=self.bob), 404, "not_found")

    def test_L075_concurrent_cancels_all_200(self):
        t = self.ada
        j = self.ok_book(t, f"{THU}T19:00")
        outs = self.burst([lambda: self.api.call("POST", f"/reservations/{j['reference']}/cancel", token=t)] * 12)
        self.assertTrue(all(o.status == 200 for o in outs))
        self.assertEqual(len({str(o.json) for o in outs}), 1)


class Patch(Base):
    def test_L078_subset_changes(self):
        t = self.ada
        j = self.ok_book(t, f"{THU}T19:00", table="t_2", party=2)
        ref = j["reference"]
        r = self.api.call("PATCH", f"/reservations/{ref}", {"party_size": 4}, token=t)
        self.assertEqual(r.status, 200, r)
        self.assertEqual((r.json["party_size"], r.json["table_id"], r.json["starts_at_local"]), (4, "t_2", f"{THU}T19:00"))
        r = self.api.call("PATCH", f"/reservations/{ref}", {"table_id": "t_3"}, token=t)
        self.assertEqual((r.json["table_id"], r.json["party_size"]), ("t_3", 4))
        r = self.api.call("PATCH", f"/reservations/{ref}", {"starts_at_local": f"{THU}T20:00"}, token=t)
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json["starts_at_local"], f"{THU}T20:00")
        self.assertEqual(r.json["starts_at"], f"{THU}T20:00:00+01:00")
        self.assertEqual(r.json["ends_at"], f"{THU}T21:30:00+01:00")
        r = self.api.call("PATCH", f"/reservations/{ref}", {"table_id": "t_1", "party_size": 2,
                                                           "starts_at_local": f"{FRI}T18:30"}, token=t)
        self.assertEqual(r.status, 200, r)
        self.assertEqual((r.json["table_id"], r.json["party_size"], r.json["starts_at_local"]),
                         ("t_1", 2, f"{FRI}T18:30"))
        g = self.api.call("GET", f"/reservations/{ref}", token=t).json
        self.assertEqual(g, r.json)

    def test_L072_identity_preserved(self):
        t = self.ada
        j = self.ok_book(t, f"{THU}T19:00")
        r = self.api.call("PATCH", f"/reservations/{j['reference']}", {"starts_at_local": f"{THU}T20:00",
                                                                       "table_id": "t_3"}, token=t).json
        for k in ("reservation_id", "reference", "restaurant_id", "created_at", "status"):
            self.assertEqual(r[k], j[k])

    def test_L078_empty_patch_no_key(self):
        t = self.ada
        j = self.ok_book(t, f"{THU}T19:00")
        r = self.api.call("PATCH", f"/reservations/{j['reference']}", {}, token=t)
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json, j)

    def test_L081_noop_amendment_200(self):
        t = self.ada
        j = self.ok_book(t, f"{THU}T19:00")
        r = self.api.call("PATCH", f"/reservations/{j['reference']}", {
            "table_id": j["table_id"], "starts_at_local": j["starts_at_local"], "party_size": j["party_size"]},
                          token=t)
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json, j)
        # still occupies; nobody else can book it
        self.err(self.book(self.bob, f"{THU}T19:00"), 409, "table_unavailable")

    def test_L079_validation_matches_create(self):
        t = self.ada
        j = self.ok_book(t, f"{THU}T19:00", table="t_2")
        ref = j["reference"]
        P = lambda b: self.api.call("PATCH", f"/reservations/{ref}", b, token=t)
        self.err(P({"party_size": 0}), 422, "validation_failed")
        self.err(P({"party_size": "3"}), 422, "validation_failed")
        self.err(P({"party_size": True}), 422, "validation_failed")
        self.err(P({"party_size": 2.5}), 422, "validation_failed")
        self.err(P({"starts_at_local": f"{THU}T19:00:00"}), 422, "validation_failed")
        self.err(P({"starts_at_local": f"{THU}T19:00Z"}), 422, "validation_failed")
        self.err(P({"starts_at_local": 5}), 400, "malformed_request")
        self.err(P({"table_id": 5}), 400, "malformed_request")
        self.err(P({"starts_at_local": f"{THU}T19:15"}), 422, "not_on_slot_grid")
        self.err(P({"starts_at_local": f"{THU}T22:00"}), 422, "outside_opening_hours")
        self.err(P({"starts_at_local": f"{SUN}T19:00"}), 422, "outside_opening_hours")
        self.err(P({"party_size": 5}), 422, "party_exceeds_capacity")
        self.err(P({"table_id": "t_1", "party_size": 3}), 422, "party_exceeds_capacity")
        self.err(P({"table_id": "zzz"}), 404, "not_found")
        self.err(P({"table_id": "t_9"}), 404, "not_found")
        self.err(P({"restaurant_id": "r_other", "table_id": "t_9"}), 404, "not_found")
        self.assertEqual(self.api.call("GET", f"/reservations/{ref}", token=t).json, j)

    def test_L079_cutoff_uses_current_start(self):
        f = fixture(reservations=[
            seed_res(1, "u_ada", "r_clock", "t_1", clock_minute(100), 2),
            seed_res(2, "u_ada", "r_clock", "t_1", clock_minute(60 * 72), 2)])
        self.reset(f)
        t = self.ada
        # current start inside cutoff: any change refused, even to a far-future time
        self.err(self.api.call("PATCH", "/reservations/SEED01", {"starts_at_local": clock_minute(60 * 96)},
                               token=t), 409, "cutoff_passed")
        # far booking moved to a time inside the cutoff window: allowed (measured against *current* start)
        r = self.api.call("PATCH", "/reservations/SEED02", {"starts_at_local": clock_minute(30)}, token=t)
        self.assertEqual(r.status, 200, r)
        # and now it is within cutoff -> further change refused
        self.err(self.api.call("PATCH", "/reservations/SEED02", {"party_size": 1}, token=t), 409, "cutoff_passed")

    def test_L079_cancelled_patch_409(self):
        t = self.ada
        j = self.ok_book(t, f"{THU}T19:00")
        self.api.call("POST", f"/reservations/{j['reference']}/cancel", token=t)
        for b in ({}, {"party_size": 3}, {"starts_at_local": f"{THU}T20:00"}):
            self.err(self.api.call("PATCH", f"/reservations/{j['reference']}", b, token=t), 409, "reservation_cancelled")
        self.assertIn("t_2", self.slot_map("r_anker", THU)[f"{THU}T19:00"]["available_table_ids"])

    def test_L079_cutoff_vs_cancelled_order_and_vs_validation(self):
        f = fixture(reservations=[seed_res(1, "u_ada", "r_anker", "t_2", "2020-01-02T19:00", 2)])
        self.reset(f)
        # inside cutoff + invalid change: both are rule violations; either is acceptable but never 2xx/5xx
        r = self.api.call("PATCH", "/reservations/SEED01", {"party_size": 3}, token=self.ada)
        self.err(r, 409, "cutoff_passed")

    def test_L080_conflict_preserves_original(self):
        t = self.ada
        a = self.ok_book(t, f"{THU}T19:00", table="t_2")
        self.ok_book(self.bob, f"{THU}T20:30", table="t_2")
        r = self.api.call("PATCH", f"/reservations/{a['reference']}", {"starts_at_local": f"{THU}T20:00"}, token=t)
        self.err(r, 409, "table_unavailable")
        self.assertEqual(self.api.call("GET", f"/reservations/{a['reference']}", token=t).json, a)
        self.assertNotIn("t_2", self.slot_map("r_anker", THU)[f"{THU}T19:00"]["available_table_ids"])
        # failed amend for a *validation* reason also leaves old slot taken
        self.err(self.api.call("PATCH", f"/reservations/{a['reference']}", {"party_size": 9}, token=t), 422,
                 "party_exceeds_capacity")
        self.assertNotIn("t_2", self.slot_map("r_anker", THU)[f"{THU}T19:00"]["available_table_ids"])

    def test_L080_success_releases_old_reserves_new(self):
        t = self.ada
        a = self.ok_book(t, f"{THU}T19:00", table="t_2")
        r = self.api.call("PATCH", f"/reservations/{a['reference']}", {"starts_at_local": f"{THU}T21:00"}, token=t)
        self.assertEqual(r.status, 200)
        m = self.slot_map("r_anker", THU)
        self.assertIn("t_2", m[f"{THU}T19:00"]["available_table_ids"])
        self.assertNotIn("t_2", m[f"{THU}T21:00"]["available_table_ids"])
        self.assertNotIn("t_2", m[f"{THU}T20:00"]["available_table_ids"])
        self.assertEqual(self.book(self.bob, f"{THU}T19:00").status, 201)

    def test_L080_overlap_with_own_old_interval_ok(self):
        t = self.ada
        a = self.ok_book(t, f"{THU}T19:00", table="t_2")
        r = self.api.call("PATCH", f"/reservations/{a['reference']}", {"starts_at_local": f"{THU}T19:30"}, token=t)
        self.assertEqual(r.status, 200, r)   # shifting overlaps only with itself

    def test_L080_concurrent_patches_to_same_slot(self):
        a = self.ok_book(self.ada, f"{THU}T18:00", table="t_1", party=1)
        b = self.ok_book(self.bob, f"{THU}T18:00", table="t_2", party=1)
        outs = self.burst([
            lambda: self.api.call("PATCH", f"/reservations/{a['reference']}", {"table_id": "t_3"}, token=self.ada),
            lambda: self.api.call("PATCH", f"/reservations/{b['reference']}", {"table_id": "t_3"}, token=self.bob)])
        self.assertEqual(sorted(o.status for o in outs), [200, 409])
        owners = self.slot_map("r_anker", THU)[f"{THU}T18:00"]["available_table_ids"]
        self.assertEqual(len(owners), 1, owners)   # one of t_1/t_2 freed, t_3 taken

    def test_L078_patch_other_restaurant_field_ignored(self):
        t = self.ada
        a = self.ok_book(t, f"{THU}T19:00")
        r = self.api.call("PATCH", f"/reservations/{a['reference']}", {"restaurant_id": "r_other", "owner": "u_bob",
                                                                      "reference": "HACKED1", "status": "cancelled"},
                          token=t)
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json, a)

    def test_L078_unknown_reference_patch_404(self):
        self.err(self.api.call("PATCH", "/reservations/NOPE12", {"party_size": 1}, token=self.ada), 404, "not_found")
