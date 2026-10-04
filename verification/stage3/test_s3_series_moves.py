"""Stage 3: recurring reservations and collective moves under policies (ledger 105, 110, 243-260, 265-270, 274-277, 290)."""
import datetime as dt
import json

from s3common import (Base3, THU, FRI, T, TERMS_KEYS, add_days, fixture3, policy, hours, seed_res, table, clock_minute)

BODY = lambda ref, count=4, interval=1: {"anchor_reference": ref, "count": count, "interval_weeks": interval}
OCC_KEYS = {"index", "reference", "exception", "reservation"}
SERIES_KEYS = {"series_id", "revision", "interval_weeks", "occurrences"}


class SeriesBase(Base3):
    def anchor(self, local=T, table_id="t_2", party=2, token=None, rest="r_anker"):
        return self.ok_book(token or self.bob, local, table=table_id, party=party, rest=rest)

    def series(self, count=4, interval=1, token=None, **kw):
        a = self.anchor(**kw)
        s = self.ok_adopt(a["reference"], count, interval, token or self.bob)
        return a, s

    def sget(self, s, token=None):
        return self.get_series(s["series_id"], token or self.bob)


class Adoption(SeriesBase):
    def test_L243_L252_response_shape_and_dates(self):
        a = self.anchor()
        before = self.get_res(a["reference"], self.bob)
        hb = self.history(a["reference"], self.bob)
        r = self.adopt(a["reference"], 4, 1, self.bob)
        self.assertEqual(r.status, 201, r)
        s = r.json
        self.assertEqual(set(s), SERIES_KEYS)
        self.assertIsInstance(s["series_id"], str)
        self.assertTrue(0 < len(s["series_id"]) <= 64)
        self.assertEqual((s["revision"], s["interval_weeks"], len(s["occurrences"])), (1, 1, 4))
        self.assertEqual([o["index"] for o in s["occurrences"]], [0, 1, 2, 3])
        for i, o in enumerate(s["occurrences"]):
            self.assertEqual(set(o), OCC_KEYS)
            self.assertEqual(o["exception"], False)
            self.assertEqual(o["reservation"]["reference"], o["reference"])
            self.assertEqual(o["reservation"]["starts_at_local"], f"{add_days(THU, 7 * i)}T19:00")
            self.assertEqual((o["reservation"]["status"], o["reservation"]["table_ids"], o["reservation"]["party_size"],
                              o["reservation"]["revision"]), ("confirmed", ["t_2"], 2, 1))
            self.assertEqual(self.get_res(o["reference"], self.bob), o["reservation"])
        self.assertEqual(len({o["reference"] for o in s["occurrences"]}), 4)
        self.assertEqual(len({o["reservation"]["reservation_id"] for o in s["occurrences"]}), 4)
        self.assertEqual(s["occurrences"][0]["reference"], a["reference"])
        self.assertEqual(s["occurrences"][0]["reservation"], before, "occurrence zero is the anchor, unchanged")
        self.assertEqual(self.history(a["reference"], self.bob), hb)

    def test_L247_interval_and_count_boundaries(self):
        for count, interval in ((2, 1), (3, 2), (12, 4), (5, 3)):
            self.reset()
            a, s = self.series(count, interval, local=f"{THU}T18:30", table_id="t_3", party=3)
            self.assertEqual(len(s["occurrences"]), count)
            for i, o in enumerate(s["occurrences"]):
                self.assertEqual(o["reservation"]["starts_at_local"], f"{add_days(THU, 7 * interval * i)}T18:30", (count, interval, i))

    def test_L254_occurrences_are_ordinary_reservations(self):
        a, s = self.series(4)
        lst = self.api.call("GET", "/reservations", token=self.bob).json["reservations"]
        self.assertEqual([x["reference"] for x in lst], [o["reference"] for o in reversed(s["occurrences"])])
        for o in s["occurrences"]:
            d = o["reservation"]["starts_at_local"][:10]
            self.assertNotIn("t_2", self.options("r_anker", d, 1)[f"{d}T19:00"]["available_table_ids"])
            self.err(self.book(self.ada, f"{d}T19:00", table="t_2", party=2, key=f"c-{d}"), 409, "table_unavailable")
            h = self.history(o["reference"], self.bob)["entries"]
            self.assertEqual([(e["seq"], e["event"], e["revision"]) for e in h], [(1, "created", 1)])
            self.assertEqual(h[0]["changes"][1], {"field": "starts_at_local", "from": None, "to": o["reservation"]["starts_at_local"]})
        self.assertEqual(len(self.api.call("GET", "/reservations", token=self.ada).json["reservations"]), 0)

    def test_L246_anchor_keeps_identity_receipt_and_history(self):
        body = {"restaurant_id": "r_anker", "table_id": "t_2", "starts_at_local": T, "party_size": 2}
        first = self.api.call("POST", "/reservations", body, token=self.bob, key="anchor-k")
        self.ok_adopt(first.json["reference"], 3, 1, self.bob)
        again = self.api.call("POST", "/reservations", body, token=self.bob, key="anchor-k")
        self.assertEqual((again.status, again.json), (200, first.json))
        self.assertEqual(len(self.history(first.json["reference"], self.bob)["entries"]), 1)
        self.assertEqual(self.get_res(first.json["reference"], self.bob), first.json)

    def test_L248_each_occurrence_selects_its_own_dates_policy(self):
        caps = {"t_1": 2, "t_2": 5, "t_3": 6}
        p1 = self.ok_publish(policy("2030-01-15", duration=60, slot=30, cutoff=30, capacities=caps))
        a, s = self.series(4, 1, table_id="t_2", party=4)
        v = [o["reservation"]["accepted_terms"]["policy_version"] for o in s["occurrences"]]
        self.assertEqual(v, [0, 0, 1, 1])
        ends = [o["reservation"]["ends_at"][11:16] for o in s["occurrences"]]
        self.assertEqual(ends, ["20:30", "20:30", "20:00", "20:00"])
        self.assert_terms(s["occurrences"][3]["reservation"]["accepted_terms"], 1, reservation_duration_minutes=60,
                          cancellation_cutoff_minutes=30, capacities=caps)
        self.assert_terms(s["occurrences"][0]["reservation"]["accepted_terms"], 0, reservation_duration_minutes=90)

    def test_L250_first_failing_occurrence_decides_and_failure_is_atomic(self):
        self.ok_publish(policy("2030-01-15", capacities={"t_1": 2, "t_2": 2, "t_3": 6}))          # t_2 shrinks for 01-17 on
        a = self.anchor(table_id="t_2", party=4)
        snap = lambda: (self.api.call("GET", "/reservations", token=self.bob).json, self.options("r_anker", "2030-01-17", 1),
                        self.history(a["reference"], self.bob))
        before = snap()
        r = self.adopt(a["reference"], 4, 1, self.bob, key="fail-1")
        self.err(r, 422, "party_exceeds_capacity")                                    # index 2
        self.assertEqual(snap(), before)
        self.ok_book(self.ada, "2030-01-10T19:00", table="t_2", party=2)              # an earlier index now conflicts
        r = self.adopt(a["reference"], 4, 1, self.bob, key="fail-2")
        self.err(r, 409, "table_unavailable")                                          # index 1 outranks index 2
        self.assertEqual(len(self.api.call("GET", "/reservations", token=self.bob).json["reservations"]), 1)
        self.assertEqual(snap()[1], before[1])

    def test_L250_opening_hours_and_grid_of_the_occurrence_dates_policy(self):
        self.ok_publish(policy("2030-01-15", slot=60, opening=hours("18:00", "23:00", ["mon", "tue", "wed", "fri", "sat"])))
        a = self.anchor()
        self.err(self.adopt(a["reference"], 3, 1, self.bob), 422, "outside_opening_hours")        # P1 closes Thursdays
        self.reset()
        self.ok_publish(policy("2030-01-15", slot=60))
        b = self.anchor(local=f"{THU}T19:30")
        self.err(self.adopt(b["reference"], 3, 1, self.bob), 422, "not_on_slot_grid")

    def test_L251_L284_L290_failure_leaves_no_series_membership_or_key_claim(self):
        a = self.anchor()
        self.ok_book(self.ada, "2030-01-17T19:00", table="t_2", party=2)
        self.err(self.adopt(a["reference"], 4, 1, self.bob, key="reuse-key"), 409, "table_unavailable")
        # the anchor is still not adopted, the key is still unused
        r = self.adopt(a["reference"], 2, 1, self.bob, key="reuse-key")
        self.assertEqual(r.status, 201, r)
        self.err(self.adopt(a["reference"], 2, 1, self.bob), 409, "already_in_series")

    def test_L249_nonexistent_local_time_rejects_the_whole_adoption(self):
        for local, count, interval in (("2030-03-24T02:30", 4, 1), ("2030-03-17T02:30", 2, 2), ("2030-03-10T02:00", 4, 3)):
            self.reset()
            a = self.anchor(local=local, rest="r_dst_de", table_id="t_1", party=2)
            n = len(self.api.call("GET", "/reservations", token=self.bob).json["reservations"])
            self.err(self.adopt(a["reference"], count, interval, self.bob), 422, "invalid_local_time")
            self.assertEqual(len(self.api.call("GET", "/reservations", token=self.bob).json["reservations"]), n)
            self.assertEqual(len(self.history(a["reference"], self.bob)["entries"]), 1)

    def test_L247_L249_L290_local_clock_is_kept_across_dst_and_folds_resolve_first(self):
        a, s = self.series(4, 1, local="2030-03-17T01:30", rest="r_dst_de", table_id="t_1", party=2)
        got = [(o["reservation"]["starts_at_local"], o["reservation"]["starts_at"][19:]) for o in s["occurrences"]]
        self.assertEqual(got, [("2030-03-17T01:30", "+01:00"), ("2030-03-24T01:30", "+01:00"),
                               ("2030-03-31T01:30", "+01:00"), ("2030-04-07T01:30", "+02:00")])
        self.assertEqual(s["occurrences"][2]["reservation"]["ends_at"], "2030-03-31T04:00:00+02:00")      # absolute 90 minutes
        self.reset()
        a, s = self.series(2, 1, local="2030-10-20T02:30", rest="r_dst_de", table_id="t_1", party=2)
        o = s["occurrences"][1]["reservation"]
        self.assertEqual((o["starts_at_local"], o["starts_at"], o["ends_at"]),
                         ("2030-10-27T02:30", "2030-10-27T02:30:00+02:00", "2030-10-27T03:00:00+01:00"))

    def test_L250_pair_anchor_repeats_the_same_table_selection(self):
        a = self.ok_pair(self.bob, T, ["t_1", "t_2"], 6)
        s = self.ok_adopt(a["reference"], 3, 1, self.bob)
        for o in s["occurrences"]:
            self.assertEqual(o["reservation"]["table_ids"], ["t_1", "t_2"])
            self.assertNotIn("table_id", o["reservation"])
        h = self.history(s["occurrences"][2]["reference"], self.bob)["entries"][0]
        self.assertEqual(h["changes"][0], {"field": "table_ids", "from": None, "to": ["t_1", "t_2"]})
        self.ok_book(self.ada, "2030-01-24T19:00", table="t_2", party=2)
        b = self.ok_pair(self.bob, f"{THU}T21:00", ["t_2", "t_3"], 8)
        self.ok_book(self.ada, "2030-01-24T21:00", table="t_3", party=2)
        self.err(self.adopt(b["reference"], 4, 1, self.bob), 409, "table_unavailable")           # one member blocked at index 3

    def test_L244_anchor_rules(self):
        a = self.anchor()
        self.err(self.adopt("NOSUCH99", 3, 1, self.bob), 404, "not_found")
        self.err(self.adopt(a["reference"], 3, 1, self.ada), 404, "not_found")                   # another owner (and a manager)
        c = self.anchor(local=f"{THU}T21:00", table_id="t_3")
        self.api.call("POST", f"/reservations/{c['reference']}/cancel", token=self.bob)
        self.err(self.adopt(c["reference"], 3, 1, self.bob), 409, "reservation_cancelled")
        self.ok_adopt(a["reference"], 3, 1, self.bob)
        self.err(self.adopt(a["reference"], 3, 1, self.bob), 409, "already_in_series")
        sid_ref = self.sget(self.ok_adopt(self.anchor(local=f"{THU}T18:00", table_id="t_1")["reference"], 2, 1, self.bob))["occurrences"][1]
        self.err(self.adopt(sid_ref["reference"], 2, 1, self.bob), 409, "already_in_series")        # any occurrence is already a member

    def test_L244_anchor_within_its_accepted_cutoff_is_refused(self):
        f = fixture3(reservations=[seed_res(1, "u_bob", "r_clock", "t_1", clock_minute(100), 2, "INCUTOFF")])
        self.reset(f)
        self.err(self.adopt("INCUTOFF", 3, 1, self.bob), 409, "cutoff_passed")
        a = self.ok_book(self.bob, clock_minute(60 * 24 * 3), rest="r_clock", table="t_2", party=2)
        self.assertEqual(self.adopt(a["reference"], 3, 1, self.bob).status, 201)

    def test_L245_count_and_interval_validation_and_auth(self):
        a = self.anchor()
        for c in (1, 0, -1, 13, 100, True, False, "4", 4.5, 4.0, None, [4], {}):
            self.err(self.api.call("POST", "/series", {"anchor_reference": a["reference"], "count": c, "interval_weeks": 1},
                                    token=self.bob, key=self.newkey()), 422, "validation_failed")
        for i in (0, -1, 5, 100, True, False, "1", 1.5, 1.0, None, [1]):
            self.err(self.api.call("POST", "/series", {"anchor_reference": a["reference"], "count": 3, "interval_weeks": i},
                                   token=self.bob, key=self.newkey()), 422, "validation_failed")
        for body in ({"anchor_reference": a["reference"], "count": 3}, {"anchor_reference": a["reference"], "interval_weeks": 1},
                     {"count": 3, "interval_weeks": 1}):
            r = self.api.call("POST", "/series", body, token=self.bob, key=self.newkey())
            self.assertEqual(r.status, 422, (body, r))
        self.err(self.api.call("POST", "/series", BODY(a["reference"]), key="k"), 401, "unauthenticated")
        self.err(self.api.call("POST", "/series", BODY(a["reference"]), token="bogus", key="k"), 401, "unauthenticated")
        self.err(self.api.call("POST", "/series", BODY(a["reference"]), token=self.bob), 400, "missing_idempotency_key")
        self.err(self.api.call("POST", "/series", BODY(a["reference"]), token=self.bob, key="k" * 256), 422, "validation_failed")
        for raw in ("{x", "", "[]", "7"):
            self.err(self.api.call("POST", "/series", raw=raw, token=self.bob, key=self.newkey()), 400, "malformed_request")
        self.assertEqual(self.api.call("GET", "/reservations", token=self.bob).json["reservations"][0]["reference"], a["reference"])
        r = self.api.call("POST", "/series", dict(BODY(a["reference"], 2), junk={"x": 1}), token=self.bob, key=self.newkey())
        self.assertEqual(r.status, 201, r)

    def test_L274_series_ids_are_unique_opaque_and_bounded(self):
        ids = set()
        for i in range(6):
            a = self.anchor(local=f"{THU}T{18 + i // 2}:{'00' if i % 2 == 0 else '30'}", table_id=("t_1", "t_2", "t_3")[i % 3], party=1)
            ids.add(self.ok_adopt(a["reference"], 2, 1, self.bob)["series_id"])
        self.assertEqual(len(ids), 6)
        self.assertTrue(all(isinstance(x, str) and 0 < len(x) <= 64 for x in ids))


class Lifecycle(SeriesBase):
    def test_L255_L242_series_read_is_owner_only(self):
        a, s = self.series(3)
        got = self.sget(s)
        self.assertEqual(got, s)
        for tok in (self.ada, None, "bogus"):
            r = self.api.call("GET", f"/series/{s['series_id']}", token=tok)
            self.assertIn(r.status, (404,) if tok != "bogus" else (401, 404), tok)
        self.err(self.api.call("GET", f"/series/{s['series_id']}", token=self.ada), 404, "not_found")
        self.err(self.api.call("GET", f"/series/{s['series_id']}"), 404, "not_found")
        self.err(self.api.call("GET", "/series/nosuchseries", token=self.bob), 404, "not_found")
        self.err(self.api.call("GET", "/series/nosuchseries"), 404, "not_found")

    def test_L256_L275_real_patch_marks_exception_and_bumps_series_revision_once(self):
        a, s = self.series(4)
        o2 = s["occurrences"][2]["reference"]
        r = self.patch(o2, {"party_size": 3}, self.bob)
        self.assertEqual((r.status, r.json["revision"]), (200, 2))
        g = self.sget(s)
        self.assertEqual(g["revision"], 2)
        self.assertEqual([o["exception"] for o in g["occurrences"]], [False, False, True, False])
        self.assertEqual(g["occurrences"][2]["reservation"]["party_size"], 3)
        self.assertEqual([o["reference"] for o in g["occurrences"]], [o["reference"] for o in s["occurrences"]])
        # no-op and failures change nothing
        self.assertEqual(self.patch(o2, {"party_size": 3}, self.bob).status, 200)
        self.err(self.patch(o2, {"party_size": 99}, self.bob), 422, "party_exceeds_capacity")
        self.err(self.patch(o2, {"expected_revision": 9, "party_size": 2}, self.bob), 409, "stale_revision")
        self.err(self.patch(s["occurrences"][1]["reference"], {"starts_at_local": f"{THU}T19:15"}, self.bob), 422, "not_on_slot_grid")
        g2 = self.sget(s)
        self.assertEqual((g2["revision"], [o["exception"] for o in g2["occurrences"]]), (2, [False, False, True, False]))
        self.assertEqual(self.patch(o2, {"party_size": 4}, self.bob).status, 200)
        self.assertEqual(self.sget(s)["revision"], 3, "every real change increments once")
        self.assertTrue(self.sget(s)["occurrences"][2]["exception"], "an exception is permanent")

    def test_L253_references_and_indices_never_change_when_dates_or_tables_change(self):
        a, s = self.series(3)
        o1 = s["occurrences"][1]["reference"]
        self.assertEqual(self.patch(o1, {"starts_at_local": f"{add_days(THU, 8)}T20:00", "table_id": "t_3"}, self.bob).status, 200)
        g = self.sget(s)
        self.assertEqual([o["index"] for o in g["occurrences"]], [0, 1, 2])
        self.assertEqual(g["occurrences"][1]["reference"], o1)
        self.assertEqual(g["occurrences"][1]["reservation"]["table_id"], "t_3")
        self.assertEqual(g["occurrences"][1]["reservation"]["reservation_id"], s["occurrences"][1]["reservation"]["reservation_id"])

    def test_L257_cancel_bumps_series_revision_once_without_an_exception_flag(self):
        a, s = self.series(4)
        o3 = s["occurrences"][3]["reference"]
        c = self.api.call("POST", f"/reservations/{o3}/cancel", token=self.bob)
        self.assertEqual((c.status, c.json["status"], c.json["revision"]), (200, "cancelled", 2))
        g = self.sget(s)
        self.assertEqual(g["revision"], 2)
        self.assertEqual([o["exception"] for o in g["occurrences"]], [False] * 4)
        self.assertEqual(len(g["occurrences"]), 4, "the cancelled occurrence is retained")
        self.assertEqual(g["occurrences"][3]["reservation"]["status"], "cancelled")
        for _ in range(2):
            self.api.call("POST", f"/reservations/{o3}/cancel", token=self.bob)
        self.assertEqual(self.sget(s)["revision"], 2, "repeated cancel does nothing")
        self.patch(s["occurrences"][1]["reference"], {"party_size": 3}, self.bob)
        self.api.call("POST", f"/reservations/{s['occurrences'][1]['reference']}/cancel", token=self.bob)
        g = self.sget(s)
        self.assertEqual((g["revision"], [o["exception"] for o in g["occurrences"]]), (4, [False, True, False, False]))

    def test_L258_cancelling_the_anchor_leaves_the_siblings(self):
        a, s = self.series(4)
        self.api.call("POST", f"/reservations/{a['reference']}/cancel", token=self.bob)
        g = self.sget(s)
        self.assertEqual([o["reservation"]["status"] for o in g["occurrences"]], ["cancelled", "confirmed", "confirmed", "confirmed"])
        self.assertEqual(g["revision"], 2)
        self.assertFalse(g["occurrences"][0]["exception"])
        self.err(self.patch(a["reference"], {"party_size": 3}, self.bob), 409, "reservation_cancelled")
        self.assertEqual(self.sget(s)["revision"], 2)

    def test_L258_anchor_amendment_is_an_exception_and_obeys_revision_checks(self):
        a, s = self.series(3)
        self.err(self.patch(a["reference"], {"expected_revision": 4, "party_size": 3}, self.bob), 409, "stale_revision")
        self.assertEqual(self.patch(a["reference"], {"expected_revision": 1, "party_size": 3}, self.bob).status, 200)
        g = self.sget(s)
        self.assertEqual((g["revision"], [o["exception"] for o in g["occurrences"]]), (2, [True, False, False]))

    def test_L260_replay_returns_the_original_series_and_changes_no_counter(self):
        a = self.anchor()
        r1 = self.adopt(a["reference"], 3, 1, self.bob, key="sr-1")
        self.assertEqual(r1.status, 201)
        sid = r1.json["series_id"]
        self.patch(r1.json["occurrences"][1]["reference"], {"party_size": 3}, self.bob)
        self.api.call("POST", f"/reservations/{r1.json['occurrences'][2]['reference']}/cancel", token=self.bob)
        rev = self.get_series(sid, self.bob)["revision"]
        for _ in range(3):
            r = self.adopt(a["reference"], 3, 1, self.bob, key="sr-1")
            self.assertEqual((r.status, r.json), (200, r1.json))
        g = self.get_series(sid, self.bob)
        self.assertEqual((g["revision"], [o["exception"] for o in g["occurrences"]]), (rev, [False, True, False]))
        self.assertEqual(len(self.api.call("GET", "/reservations", token=self.bob).json["reservations"]), 3)
        self.err(self.adopt(a["reference"], 4, 1, self.bob, key="sr-1"), 409, "idempotency_key_reuse")
        self.err(self.api.call("POST", "/series", {}, token=self.bob, key="sr-1"), 409, "idempotency_key_reuse")
        # keys are scoped to the user
        other = self.anchor(local=f"{THU}T21:00", table_id="t_3", token=self.ada)
        self.assertEqual(self.adopt(other["reference"], 2, 1, self.ada, key="sr-1").status, 201)

    def test_L270_concurrent_identical_adoption_is_one_operation(self):
        a = self.anchor()
        outs = self.burst([lambda: self.adopt(a["reference"], 4, 1, self.bob, key="cs-1")] * 12)
        self.assertEqual(sorted(o.status for o in outs), [200] * 11 + [201])
        self.assertEqual(len({json.dumps(o.json, sort_keys=True) for o in outs}), 1)
        self.assertEqual(len(self.api.call("GET", "/reservations", token=self.bob).json["reservations"]), 4)

    def test_L270_L290_racing_adoptions_of_one_anchor_have_one_winner(self):
        a = self.anchor()
        outs = self.burst([lambda i=i: self.adopt(a["reference"], 3, 1, self.bob, key=f"race-{i}") for i in range(10)])
        self.assertEqual(sorted(o.status for o in outs), [201] + [409] * 9)
        for o in outs:
            if o.status == 409:
                self.err(o, 409, "already_in_series")
        self.assertEqual(len(self.api.call("GET", "/reservations", token=self.bob).json["reservations"]), 3)

    def test_L250_a_second_series_conflicting_at_one_occurrence_is_atomic(self):
        a, s = self.series(4, local=T, table_id="t_2")
        c = self.ok_book(self.bob, f"{add_days(THU, 14)}T20:30", table="t_2", party=2)        # adjacent to occurrence 2, blocks 21:00
        d = self.ok_book(self.bob, f"{THU}T21:00", table="t_2", party=2)
        n = len(self.api.call("GET", "/reservations", token=self.bob).json["reservations"])
        self.err(self.adopt(d["reference"], 4, 1, self.bob), 409, "table_unavailable")           # index 2 collides with c
        self.assertEqual(len(self.api.call("GET", "/reservations", token=self.bob).json["reservations"]), n)
        self.assertEqual(self.sget(s)["revision"], 1)
        again = self.adopt(d["reference"], 2, 1, self.bob)                                          # d was left adoptable
        self.assertEqual(again.status, 201, again)

    def test_L285_series_reads_stay_consistent_under_concurrent_writes(self):
        a, s = self.series(4)
        refs = [o["reference"] for o in s["occurrences"]]
        calls = [lambda i=i: self.patch(refs[i % 4], {"party_size": 1 + i % 2}, self.bob) for i in range(24)]
        reads = []

        def read():
            r = self.api.call("GET", f"/series/{s['series_id']}", token=self.bob)
            reads.append(r)
            return r
        calls += [read] * 16
        outs = self.burst(calls)
        self.assertTrue(all(o.status < 500 for o in outs))
        for r in reads:
            g = r.json
            self.assertEqual([o["index"] for o in g["occurrences"]], [0, 1, 2, 3])
            self.assertEqual([o["reference"] for o in g["occurrences"]], refs)
            # an exception flag and the revision only ever move together
            self.assertGreaterEqual(g["revision"], 1)
            self.assertGreaterEqual(g["revision"] - 1, sum(o["exception"] for o in g["occurrences"]))
        final = self.sget(s)
        total = sum(self.get_res(r, self.bob)["revision"] - 1 for r in refs)
        self.assertEqual(final["revision"] - 1, total, "series revision counts every real change exactly once")


class Moves(SeriesBase):
    def test_L105_L265_changed_items_adopt_the_resulting_date_policy_and_count_once(self):
        d1 = add_days(THU, 7)
        self.ok_publish(policy(d1, duration=60, cutoff=20, capacities={"t_1": 2, "t_2": 4, "t_3": 8}))
        a = self.ok_book(self.bob, T, table="t_2", party=3)
        b = self.ok_book(self.bob, T, table="t_3", party=3)
        r = self.moves([{"reference": a["reference"], "starts_at_local": f"{d1}T19:00", "junk": 1},
                        {"reference": b["reference"]}], self.bob)
        self.assertEqual(r.status, 201, r)
        x, y = r.json["reservations"]
        self.assertEqual((x["revision"], x["accepted_terms"]["policy_version"], x["ends_at"][11:16]), (2, 1, "20:00"))
        self.assertEqual(y, b, "the unchanged item keeps every value")
        self.assertEqual([e["event"] for e in self.history(a["reference"], self.bob)["entries"]], ["created", "changed"])
        self.assertEqual(len(self.history(b["reference"], self.bob)["entries"]), 1)
        self.assertEqual(self.history(a["reference"], self.bob)["entries"][1]["accepted_terms"], x["accepted_terms"])

    def test_L110_input_order_swaps_and_no_ops(self):
        a = self.ok_book(self.bob, T, table="t_2", party=2)
        b = self.ok_book(self.bob, T, table="t_3", party=2)
        r = self.moves([{"reference": a["reference"], "table_id": "t_3"}, {"reference": b["reference"], "table_id": "t_2"}], self.bob)
        self.assertEqual(r.status, 201, r)
        got = r.json["reservations"]
        self.assertEqual([x["reference"] for x in got], [a["reference"], b["reference"]])
        self.assertEqual([(x["table_id"], x["revision"]) for x in got], [("t_3", 2), ("t_2", 2)])
        n = self.moves([{"reference": a["reference"], "table_id": "t_3", "party_size": 2},
                        {"reference": b["reference"], "table_ids": ["t_2"]}], self.bob)
        self.assertEqual(n.json["reservations"], got, "no-op items retain every value, revision and history")
        self.assertEqual(len(self.history(a["reference"], self.bob)["entries"]), 2)

    def test_L265_expected_revision_per_move_types_and_stale_first(self):
        f = fixture3(reservations=[seed_res(1, "u_bob", "r_clock", "t_1", clock_minute(100), 2, "INCUTOFF")])
        self.reset(f)
        a = self.ok_book(self.bob, T, table="t_2", party=2)
        before = self.api.call("GET", "/reservations", token=self.bob).json
        for v in (True, 1.5, "1", 0, -2):
            self.err(self.moves([{"reference": a["reference"], "party_size": 3, "expected_revision": v}], self.bob), 422, "validation_failed")
        self.err(self.moves([{"reference": "INCUTOFF", "party_size": 3, "expected_revision": 4}], self.bob), 409, "stale_revision")
        self.err(self.moves([{"reference": "INCUTOFF", "party_size": 3, "expected_revision": 1}], self.bob), 409, "cutoff_passed")
        self.err(self.moves([{"reference": a["reference"], "party_size": 0, "expected_revision": 5}], self.bob), 409, "stale_revision")
        self.assertEqual(self.api.call("GET", "/reservations", token=self.bob).json, before)
        # errors are reported in input order: an earlier validation error outranks a later stale revision, and vice versa
        a2 = self.ok_book(self.bob, f"{THU}T21:00", table="t_3", party=2)
        self.patch(a2["reference"], {"party_size": 3}, self.bob)
        self.err(self.moves([{"reference": a["reference"], "party_size": 99}, {"reference": a2["reference"], "expected_revision": 1,
                                                                                "party_size": 2}], self.bob), 422, "party_exceeds_capacity")
        self.err(self.moves([{"reference": a2["reference"], "expected_revision": 1, "party_size": 2}, {"reference": a["reference"],
                                                                                                        "party_size": 99}], self.bob),
                 409, "stale_revision")
        before = self.api.call("GET", "/reservations", token=self.bob).json
        ok = self.moves([{"reference": a["reference"], "party_size": 3, "expected_revision": 1}], self.bob)
        self.assertEqual((ok.status, ok.json["reservations"][0]["revision"]), (201, 2))

    def test_L266_failure_leaves_everything_unchanged(self):
        a, s = self.series(3)
        b = self.ok_book(self.bob, f"{THU}T21:00", table="t_3", party=2)
        o1, o2 = s["occurrences"][1]["reference"], s["occurrences"][2]["reference"]
        snap = lambda: (self.api.call("GET", "/reservations", token=self.bob).json, self.sget(s),
                        [self.history(r, self.bob) for r in (o1, o2, b["reference"])], self.options("r_anker", add_days(THU, 7), 1))
        before = snap()
        key = "mf-1"
        self.err(self.moves([{"reference": o1, "party_size": 3}, {"reference": o2, "starts_at_local": f"{add_days(THU, 14)}T19:15"}],
                            self.bob, key=key), 422, "not_on_slot_grid")
        self.err(self.moves([{"reference": o1, "party_size": 3}, {"reference": b["reference"], "starts_at_local": f"{add_days(THU, 7)}T19:00",
                                                                      "table_id": "t_2"}], self.bob, key=key), 409, "table_unavailable")
        self.err(self.moves([{"reference": o1, "party_size": 3, "expected_revision": 1}, {"reference": o2, "expected_revision": 7}],
                            self.bob, key=key), 409, "stale_revision")
        self.assertEqual(snap(), before)
        ok = self.moves([{"reference": o1, "party_size": 3}], self.bob, key=key)                  # the key was never consumed
        self.assertEqual(ok.status, 201, ok)

    def test_L268_one_batch_bumps_each_affected_series_once_and_flags_each_changed_occurrence(self):
        a, s = self.series(4)
        o = [x["reference"] for x in s["occurrences"]]
        r = self.moves([{"reference": o[1], "party_size": 3}, {"reference": o[2], "party_size": 3}, {"reference": o[3]},
                        {"reference": o[0], "party_size": 2}], self.bob)
        self.assertEqual(r.status, 201, r)
        g = self.sget(s)
        self.assertEqual(g["revision"], 2, "two changed occurrences, one batch: +1")
        self.assertEqual([x["exception"] for x in g["occurrences"]], [False, True, True, False])
        self.assertEqual([x["reservation"]["revision"] for x in g["occurrences"]], [1, 2, 2, 1])

    def test_L268_two_series_in_one_batch_each_get_one_increment(self):
        a, s = self.series(3, local=T, table_id="t_2")
        b, t = self.series(3, local=f"{THU}T21:00", table_id="t_3")
        c, u = self.series(2, local=f"{THU}T18:00", table_id="t_1", party=1)
        r = self.moves([{"reference": s["occurrences"][1]["reference"], "party_size": 3}, {"reference": t["occurrences"][1]["reference"], "party_size": 3},
                        {"reference": t["occurrences"][2]["reference"], "party_size": 3}, {"reference": u["occurrences"][1]["reference"]}],
                       self.bob)
        self.assertEqual(r.status, 201, r)
        self.assertEqual((self.sget(s)["revision"], self.sget(t)["revision"], self.sget(u)["revision"]), (2, 2, 1))
        self.assertEqual([x["exception"] for x in self.sget(u)["occurrences"]], [False, False])

    def test_L269_replay_and_failed_batch_change_no_counters(self):
        a, s = self.series(3)
        o = [x["reference"] for x in s["occurrences"]]
        moves = [{"reference": o[1], "party_size": 3}, {"reference": o[2], "starts_at_local": f"{add_days(THU, 14)}T20:00"}]
        r1 = self.moves(moves, self.bob, key="mr-1")
        self.assertEqual(r1.status, 201)
        state = (self.sget(s), [self.history(x, self.bob) for x in o])
        self.patch(o[1], {"party_size": 2}, self.bob)
        self.api.call("POST", f"/reservations/{o[2]}/cancel", token=self.bob)
        later = (self.sget(s), [self.history(x, self.bob) for x in o])
        for _ in range(2):
            r = self.moves(moves, self.bob, key="mr-1")
            self.assertEqual((r.status, r.json), (200, r1.json), "original batch response, whatever happened since")
        self.assertEqual((self.sget(s), [self.history(x, self.bob) for x in o]), later)
        self.err(self.moves([{"reference": o[1], "party_size": 1}], self.bob, key="mr-1"), 409, "idempotency_key_reuse")
        self.assertEqual(state[0]["revision"], 3)

    def test_L267_each_changed_booking_gets_one_revision_and_one_entry(self):
        refs = [self.ok_book(self.bob, f"{THU}T{h}:00", table=t, party=1)["reference"] for h, t in (("18", "t_1"), ("19", "t_2"), ("20", "t_3"))]
        r = self.moves([{"reference": refs[0], "party_size": 2, "table_id": "t_1"}, {"reference": refs[1], "party_size": 2},
                        {"reference": refs[2], "party_size": 1}], self.bob)
        self.assertEqual(r.status, 201, r)
        self.assertEqual([x["revision"] for x in r.json["reservations"]], [2, 2, 1])
        self.assertEqual([len(self.history(x, self.bob)["entries"]) for x in refs], [2, 2, 1])

    def test_L277_new_paths_record_receipts_for_the_calling_user_only(self):
        a = self.anchor()
        self.ok_adopt(a["reference"], 2, 1, self.bob)
        r = self.api.call("POST", "/series", BODY(a["reference"], 2), token=self.bob, key="x-1")
        self.assertEqual(r.status, 409)                                                       # already in a series, key unused
        self.assertEqual(self.adopt(self.anchor(local=f"{THU}T21:00", table_id="t_3")["reference"], 2, 1, self.bob, key="x-1").status, 201)


class Deferred(SeriesBase):
    def test_L259_series_adoption_works_without_depending_on_a_restaurant_revision(self):
        """The restaurant revision of an adoption is stage-4 scope: here only the observable stage-3 behaviour is checked."""
        before = self.api.call("GET", "/restaurants/r_anker").json
        a, s = self.series(3)
        self.assertEqual(self.api.call("GET", "/restaurants/r_anker").json, before, "adoption does not alter the restaurant configuration")
        self.assertEqual(len(self.api.call("GET", "/restaurants/r_anker/policies").json["policies"]), 0)
        self.assertEqual(self.sget(s)["revision"], 1)
