"""Stage 3: accepted terms, revisions, amendments, cancel, decision and history (ledger 62, 75-81, 206-214, 230-242, 264, 272, 288-289)."""
import json
import re

from s3common import (Base3, THU, FRI, T, TERMS_KEYS, add_days, fixture3, policy, hours, seed_res, table, clock_minute)

RFC = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?(Z|[+-]\d\d:\d\d)$")
BOOKING_KEYS = {"reservation_id", "reference", "restaurant_id", "table_ids", "party_size", "status", "starts_at_local", "starts_at",
                "ends_at", "created_at", "revision", "accepted_terms"}
OPEN_ALL = hours("00:00", "23:59")


def clock_policy(cutoff=0, duration=10, effective="2000-01-01"):
    return policy(effective, duration=duration, slot=1, cutoff=cutoff, rest="r_clock", opening=OPEN_ALL)


class Terms(Base3):
    def test_L062_L230_create_shape_has_revision_and_terms(self):
        r = self.ok_book(self.bob, T, table="t_2", party=3)
        self.assertEqual(set(r) - {"table_id"}, BOOKING_KEYS)
        self.assertEqual((r["revision"], r["table_id"], r["table_ids"]), (1, "t_2", ["t_2"]))
        self.assertIs(type(r["revision"]), int)
        self.assert_terms(r["accepted_terms"], 0)
        p = self.ok_pair(self.bob, f"{THU}T21:00", ["t_1", "t_2"], 6)
        self.assertEqual(set(p), BOOKING_KEYS)
        self.assertEqual(self.get_res(p["reference"], self.bob), p)
        self.assertEqual(self.api.call("GET", "/reservations", token=self.bob).json["reservations"], [p, r])

    def test_L233_old_idempotent_responses_stay_exactly_original(self):
        body = {"restaurant_id": "r_anker", "table_id": "t_2", "starts_at_local": T, "party_size": 2}
        first = self.api.call("POST", "/reservations", body, token=self.bob, key="orig-1")
        ref = first.json["reference"]
        self.ok_publish(policy("2020-01-01", duration=30, cutoff=5))
        self.assertEqual(self.patch(ref, {"party_size": 3}, self.bob).json["revision"], 2)
        self.api.call("POST", f"/reservations/{ref}/cancel", token=self.bob)
        again = self.api.call("POST", "/reservations", body, token=self.bob, key="orig-1")
        self.assertEqual((again.status, again.json), (200, first.json))
        self.assertEqual((again.json["revision"], again.json["status"], again.json["accepted_terms"]["policy_version"]),
                         (1, "confirmed", 0))
        self.assertEqual(len(self.history(ref, self.bob)["entries"]), 3)

    def test_L232_seeded_bookings_start_at_revision_one_under_policy_zero(self):
        f = fixture3(reservations=[seed_res(1, "u_bob", "r_anker", "t_2", T, 2, "SEEDAAAA"),
                                   dict(seed_res(2, "u_bob", "r_anker", "t_3", T, 2, "SEEDBBBB"), status="cancelled")])
        self.reset(f)
        for ref, st in (("SEEDAAAA", "confirmed"), ("SEEDBBBB", "cancelled")):
            r = self.get_res(ref, self.bob)
            self.assertEqual((r["revision"], r["status"]), (1, st))
            self.assert_terms(r["accepted_terms"], 0)
            h = self.history(ref, self.bob)
            self.assertIn(len(h["entries"]), (0, 1))
            for e in h["entries"]:
                self.assertEqual((e["seq"], e["event"], e["revision"]), (1, "created", 1))
            d = self.decision(ref, self.bob)
            self.assertEqual((d["revision"], d["reference"]), (1, ref))

    def test_L241_L242_decision_shape_and_privacy(self):
        r = self.ok_book(self.bob, T, table="t_2", party=2)
        d = self.decision(r["reference"], self.bob)
        self.assertEqual(set(d), {"reference", "revision", "accepted_terms"})
        self.assertEqual((d["reference"], d["revision"], d["accepted_terms"]), (r["reference"], 1, r["accepted_terms"]))
        self.patch(r["reference"], {"party_size": 3}, self.bob)
        self.assertEqual(self.decision(r["reference"], self.bob)["revision"], 2)
        self.api.call("POST", f"/reservations/{r['reference']}/cancel", token=self.bob)
        d = self.decision(r["reference"], self.bob)
        self.assertEqual(d["revision"], 3)
        for path in (f"/reservations/{r['reference']}/decision", f"/reservations/{r['reference']}/history"):
            self.err(self.api.call("GET", path, token=self.ada), 404, "not_found")          # another guest (and a manager)
            self.err(self.api.call("GET", path), 404, "not_found")                           # anonymous: 404, not 401
            self.err(self.api.call("GET", path.replace(r["reference"], "NOSUCH99"), token=self.bob), 404, "not_found")
            self.err(self.api.call("GET", path.replace(r["reference"], "NOSUCH99")), 404, "not_found")
            bogus = self.api.call("GET", path, headers={"Authorization": "Bearer nonsense"})
            self.assertIn(bogus.status, (401, 404))
        a = self.api.call("GET", f"/reservations/{r['reference']}/history", token=self.ada)
        b = self.api.call("GET", "/reservations/NOSUCH99/history", token=self.ada)
        self.assertEqual((a.status, a.json), (b.status, b.json), "existence must not leak")


class Amend(Base3):
    def test_L235_L236_real_amendment_adopts_resulting_date_policy(self):
        d1 = add_days(THU, 7)
        p1 = self.ok_publish(policy(d1, duration=60, slot=30, cutoff=45))
        a = self.ok_book(self.bob, T, table="t_2", party=3)
        r = self.patch(a["reference"], {"starts_at_local": f"{d1}T19:00"}, self.bob)
        self.assertEqual(r.status, 200, r)
        j = r.json
        self.assertEqual((j["revision"], j["reference"], j["reservation_id"], j["created_at"]),
                         (2, a["reference"], a["reservation_id"], a["created_at"]))
        self.assert_terms(j["accepted_terms"], 1, reservation_duration_minutes=60, cancellation_cutoff_minutes=45)
        self.assertEqual((j["starts_at"], j["ends_at"]), (f"{d1}T19:00:00+01:00", f"{d1}T20:00:00+01:00"))
        self.assertEqual(self.get_res(a["reference"], self.bob), j)
        h = self.history(a["reference"], self.bob)["entries"]
        self.assertEqual([(e["seq"], e["event"], e["revision"]) for e in h], [(1, "created", 1), (2, "changed", 2)])
        self.assertEqual(h[0]["accepted_terms"], a["accepted_terms"])             # old entries never acquire newer terms
        self.assertEqual(h[1]["accepted_terms"], j["accepted_terms"])
        self.assertIn("t_2", self.options("r_anker", T[:10], 1)[T]["available_table_ids"])      # old slot released
        self.assertNotIn("t_2", self.options("r_anker", d1, 1)[f"{d1}T19:30"]["available_table_ids"])    # [19:00, 20:00)
        self.assertIn("t_2", self.options("r_anker", d1, 1)[f"{d1}T20:00"]["available_table_ids"])

    def test_L235_all_resulting_fields_are_validated_under_the_resulting_policy(self):
        d1 = add_days(THU, 7)
        self.ok_publish(policy(d1, duration=60, slot=60, cutoff=45, capacities={"t_1": 2, "t_2": 3, "t_3": 6},
                               opening=hours("19:00", "22:00", ["thu"])))
        a = self.ok_book(self.bob, T, table="t_2", party=4)
        before = (self.get_res(a["reference"], self.bob), self.history(a["reference"], self.bob))
        P = lambda b: self.patch(a["reference"], b, self.bob)
        self.err(P({"starts_at_local": f"{d1}T19:00"}), 422, "party_exceeds_capacity")      # unchanged party 4 > new cap 3
        self.err(P({"starts_at_local": f"{d1}T19:30", "party_size": 2}), 422, "not_on_slot_grid")
        self.err(P({"starts_at_local": f"{d1}T18:00", "party_size": 2}), 422, "outside_opening_hours")
        self.err(P({"starts_at_local": f"{d1}T22:00", "party_size": 2}), 422, "outside_opening_hours")
        self.err(P({"starts_at_local": f"{d1}T19:00", "table_id": "t_1", "party_size": 3}), 422, "party_exceeds_capacity")
        self.assertEqual((self.get_res(a["reference"], self.bob), self.history(a["reference"], self.bob)), before)
        ok = P({"starts_at_local": f"{d1}T20:00", "party_size": 3})
        self.assertEqual((ok.status, ok.json["revision"]), (200, 2))
        self.assertEqual(ok.json["ends_at"], f"{d1}T21:00:00+01:00")

    def test_L236_failed_amendment_changes_nothing(self):
        a = self.ok_book(self.bob, T, table="t_2", party=2)
        other = self.ok_book(self.ada, f"{THU}T21:00", table="t_3", party=2)
        snap = lambda: (self.get_res(a["reference"], self.bob), self.history(a["reference"], self.bob),
                        self.options("r_anker", THU, 1))
        before = snap()
        for body, code in (({"table_id": "t_3", "starts_at_local": f"{THU}T21:00"}, 409), ({"party_size": 9}, 422),
                           ({"starts_at_local": f"{THU}T19:15"}, 422), ({"table_ids": ["t_1", "t_3"]}, 422)):
            r = self.patch(a["reference"], body, self.bob)
            self.assertEqual(r.status, code, (body, r))
        self.assertEqual(snap(), before)

    def test_L079_L234_old_accepted_cutoff_is_checked_first(self):
        f = fixture3(reservations=[seed_res(1, "u_bob", "r_clock", "t_1", clock_minute(100), 2, "INCUTOFF")])
        self.reset(f)
        self.ok_publish(clock_policy(cutoff=0), rest="r_clock")                     # newer, laxer policy applies to the date
        P = lambda b: self.patch("INCUTOFF", b, self.bob)
        self.err(P({"party_size": 3}), 409, "cutoff_passed")                          # old accepted cutoff (120) governs
        self.err(P({"starts_at_local": clock_minute(60 * 72)}), 409, "cutoff_passed")
        self.err(self.api.call("POST", "/reservations/INCUTOFF/cancel", token=self.bob), 409, "cutoff_passed")
        r = self.get_res("INCUTOFF", self.bob)
        self.assertEqual((r["revision"], r["status"], r["accepted_terms"]["policy_version"]), (1, "confirmed", 0))

    def test_L234_cancel_uses_the_accepted_cutoff_not_the_current_policy(self):
        self.ok_publish(clock_policy(cutoff=0), rest="r_clock")
        near = self.ok_book(self.bob, clock_minute(30), rest="r_clock", table="t_1", party=2)      # accepted cutoff 0
        self.assertEqual(near["accepted_terms"]["cancellation_cutoff_minutes"], 0)
        c = self.api.call("POST", f"/reservations/{near['reference']}/cancel", token=self.bob)
        self.assertEqual((c.status, c.json["status"], c.json["revision"]), (200, "cancelled", 2))
        # a booking accepted under cutoff 120 may be cancelled 3 days ahead although a later policy says 7 days
        self.reset()
        far = self.ok_book(self.bob, clock_minute(60 * 72), rest="r_clock", table="t_1", party=2)
        self.ok_publish(clock_policy(cutoff=10080), rest="r_clock")
        c = self.api.call("POST", f"/reservations/{far['reference']}/cancel", token=self.bob)
        self.assertEqual((c.status, c.json["revision"]), (200, 2))

    def test_L236_amendments_far_from_start_succeed_under_a_long_cutoff(self):
        self.ok_publish(clock_policy(cutoff=10080), rest="r_clock")
        a = self.ok_book(self.bob, clock_minute(60 * 24 * 30), rest="r_clock", table="t_1", party=2)      # accepts 7 days
        r = self.patch(a["reference"], {"starts_at_local": clock_minute(60 * 24 * 20)}, self.bob)
        self.assertEqual(r.status, 200, r)                                        # 20 days ahead: old cutoff satisfied
        near = self.patch(a["reference"], {"starts_at_local": clock_minute(60 * 24 * 40)}, self.bob)
        self.assertEqual(near.status, 200)

    def test_L081_L237_no_op_keeps_terms_end_revision_and_history(self):
        a = self.ok_book(self.bob, T, table="t_2", party=2)
        p = self.ok_publish(policy("2020-01-01", duration=30, slot=15, cutoff=1, capacities={"t_1": 9, "t_2": 9, "t_3": 9}))
        before = self.history(a["reference"], self.bob)
        for body in ({}, {"party_size": 2}, {"table_id": "t_2", "starts_at_local": T, "party_size": 2}, {"table_ids": ["t_2"]},
                     {"junk": 1, "expected_revision": 1}):
            r = self.patch(a["reference"], body, self.bob)
            self.assertEqual((r.status, r.json), (200, a), body)
        self.assertEqual(self.history(a["reference"], self.bob), before)
        self.assertEqual(self.decision(a["reference"], self.bob)["revision"], 1)
        pair = self.ok_pair(self.bob, f"{THU}T21:00", ["t_1", "t_2"], 6)
        hp = self.history(pair["reference"], self.bob)
        for ids in (["t_2", "t_1"], ["t_1", "t_2"]):
            r = self.patch(pair["reference"], {"table_ids": ids}, self.bob)
            self.assertEqual((r.status, r.json), (200, pair))
        self.assertEqual(self.history(pair["reference"], self.bob), hp)

    def test_L081_no_op_still_requires_a_confirmed_editable_booking(self):
        f = fixture3(reservations=[seed_res(1, "u_bob", "r_clock", "t_1", clock_minute(100), 2, "INCUTOFF")])
        self.reset(f)
        self.err(self.patch("INCUTOFF", {}, self.bob), 409, "cutoff_passed")
        self.err(self.patch("INCUTOFF", {"party_size": 2}, self.bob), 409, "cutoff_passed")
        a = self.ok_book(self.bob, T, table="t_2", party=2)
        self.api.call("POST", f"/reservations/{a['reference']}/cancel", token=self.bob)
        self.err(self.patch(a["reference"], {}, self.bob), 409, "reservation_cancelled")
        self.err(self.patch(a["reference"], {"party_size": 2}, self.bob), 409, "reservation_cancelled")

    def test_L075_L076_L234_cancel_increments_once_and_repeat_changes_nothing(self):
        a = self.ok_book(self.bob, T, table="t_2", party=2)
        c1 = self.api.call("POST", f"/reservations/{a['reference']}/cancel", token=self.bob)
        self.assertEqual((c1.status, c1.json["status"], c1.json["revision"]), (200, "cancelled", 2))
        self.assertEqual(c1.json["accepted_terms"], a["accepted_terms"])
        h = self.history(a["reference"], self.bob)["entries"]
        self.assertEqual([(e["seq"], e["event"], e["changes"], e["revision"]) for e in h],
                         [(1, "created", h[0]["changes"], 1), (2, "cancelled", [], 2)])
        for _ in range(3):
            c = self.api.call("POST", f"/reservations/{a['reference']}/cancel", token=self.bob)
            self.assertEqual((c.status, c.json), (200, c1.json))
        self.assertEqual(len(self.history(a["reference"], self.bob)["entries"]), 2)
        self.assertEqual(self.decision(a["reference"], self.bob)["revision"], 2)
        self.err(self.patch(a["reference"], {"party_size": 3}, self.bob), 409, "reservation_cancelled")
        self.assertEqual(len(self.history(a["reference"], self.bob)["entries"]), 2, "nothing follows a cancellation")
        self.assertIn("t_2", self.options("r_anker", THU, 1)[T]["available_table_ids"])

    def test_L076_repeat_cancel_after_the_cutoff_still_200_and_changes_nothing(self):
        f = fixture3(reservations=[dict(seed_res(1, "u_bob", "r_anker", "t_2", "2020-01-02T19:00", 2, "OLDCNCL1"), status="cancelled")])
        self.reset(f)
        c = self.api.call("POST", "/reservations/OLDCNCL1/cancel", token=self.bob)
        self.assertEqual((c.status, c.json["status"], c.json["revision"]), (200, "cancelled", 1))
        self.assertEqual(self.decision("OLDCNCL1", self.bob)["revision"], 1)

    def test_L077_cancel_at_or_after_start_is_cutoff_passed_with_accepted_cutoff(self):
        f = fixture3(reservations=[seed_res(1, "u_bob", "r_anker", "t_2", "2020-01-02T19:00", 2, "PASTBOOK")])
        self.reset(f)
        self.err(self.api.call("POST", "/reservations/PASTBOOK/cancel", token=self.bob), 409, "cutoff_passed")
        self.assertEqual(self.get_res("PASTBOOK", self.bob)["revision"], 1)

    def test_L080_each_real_change_is_one_revision_and_one_history_entry(self):
        a = self.ok_book(self.bob, T, table="t_2", party=2)
        steps = [({"party_size": 3}, 2), ({"starts_at_local": f"{THU}T20:00"}, 3), ({"table_id": "t_3"}, 4),
                 ({"table_id": "t_1", "party_size": 2, "starts_at_local": f"{THU}T21:00"}, 5)]
        for body, rev in steps:
            r = self.patch(a["reference"], body, self.bob)
            self.assertEqual((r.status, r.json["revision"]), (200, rev), body)
        h = self.history(a["reference"], self.bob)["entries"]
        self.assertEqual([e["seq"] for e in h], [1, 2, 3, 4, 5])
        self.assertEqual([e["revision"] for e in h], [1, 2, 3, 4, 5])
        self.assertEqual(self.get_res(a["reference"], self.bob)["revision"], 5)


class Revisions(Base3):
    def test_L238_L240_expected_revision_types_and_ranges(self):
        a = self.ok_book(self.bob, T, table="t_2", party=2)
        for v in (True, False, 1.5, "1", 0, -1, [1], {"a": 1}, 2.0, "", 1e3):
            r = self.patch(a["reference"], {"expected_revision": v, "party_size": 3}, self.bob)
            self.assertIn(r.status, (422,), (v, r))
            if r.status == 422:
                self.err(r, 422, "validation_failed")
        self.assertEqual(self.get_res(a["reference"], self.bob)["revision"], 1)
        ok = self.patch(a["reference"], {"expected_revision": 1, "party_size": 3, "unrelated": "x"}, self.bob)
        self.assertEqual((ok.status, ok.json["revision"]), (200, 2))
        self.assertEqual(self.patch(a["reference"], {"party_size": 4}, self.bob).json["revision"], 3)     # omission: stage 1 semantics

    def test_L238_stale_revision_before_cutoff_and_validation(self):
        f = fixture3(reservations=[seed_res(1, "u_bob", "r_clock", "t_1", clock_minute(100), 2, "INCUTOFF")])
        self.reset(f)
        for body in ({"expected_revision": 5, "party_size": 3}, {"expected_revision": 2}, {"expected_revision": 9, "party_size": 0},
                     {"expected_revision": 3, "starts_at_local": "garbage"}, {"expected_revision": 7}):
            self.err(self.patch("INCUTOFF", body, self.bob), 409, "stale_revision")
        self.err(self.patch("INCUTOFF", {"expected_revision": 1, "party_size": 3}, self.bob), 409, "cutoff_passed")   # match -> cutoff
        a = self.ok_book(self.bob, T, table="t_2", party=2)
        self.err(self.patch(a["reference"], {"expected_revision": 3, "party_size": 99}, self.bob), 409, "stale_revision")
        self.err(self.patch(a["reference"], {"expected_revision": 3, "starts_at_local": f"{THU}T19:15"}, self.bob), 409, "stale_revision")
        self.err(self.patch(a["reference"], {"expected_revision": 1, "party_size": 99}, self.bob), 422, "party_exceeds_capacity")
        self.err(self.patch(a["reference"], {"expected_revision": 3}, self.bob), 409, "stale_revision")       # even for a no-op body
        self.assertEqual(self.patch(a["reference"], {"expected_revision": 1}, self.bob).status, 200)           # matching no-op
        self.assertEqual(self.get_res(a["reference"], self.bob)["revision"], 1)

    def test_L238_stale_revision_after_cancel_and_after_each_change(self):
        a = self.ok_book(self.bob, T, table="t_2", party=2)
        self.assertEqual(self.patch(a["reference"], {"party_size": 3, "expected_revision": 1}, self.bob).json["revision"], 2)
        self.err(self.patch(a["reference"], {"party_size": 4, "expected_revision": 1}, self.bob), 409, "stale_revision")
        self.assertEqual(self.patch(a["reference"], {"party_size": 4, "expected_revision": 2}, self.bob).json["revision"], 3)
        c = self.api.call("POST", f"/reservations/{a['reference']}/cancel", token=self.bob)
        self.assertEqual(c.json["revision"], 4)
        self.assertEqual(self.patch(a["reference"], {"party_size": 2, "expected_revision": 4}, self.bob).status, 409)

    def test_L239_concurrent_changes_with_one_revision_have_one_winner(self):
        a = self.ok_book(self.bob, T, table="t_2", party=2)
        outs = self.burst([lambda i=i: self.patch(a["reference"], {"expected_revision": 1,
                                                                    "starts_at_local": f"{THU}T{18 + i % 4}:{'00' if i % 2 else '30'}",
                                                                    "table_id": ("t_1", "t_3")[i % 2]}, self.bob)
                           for i in range(12)])
        codes = sorted(o.status for o in outs)
        self.assertEqual(codes.count(200), 1, codes)
        for o in outs:
            if o.status != 200:
                self.err(o, 409, "stale_revision")
        self.assertEqual(self.get_res(a["reference"], self.bob)["revision"], 2)
        self.assertEqual(len(self.history(a["reference"], self.bob)["entries"]), 2)

    def test_L239_concurrent_no_ops_preserve_the_counter(self):
        a = self.ok_book(self.bob, T, table="t_2", party=2)
        outs = self.burst([lambda: self.patch(a["reference"], {"expected_revision": 1, "party_size": 2}, self.bob)] * 10)
        self.assertTrue(all(o.status == 200 for o in outs))
        self.assertEqual(self.get_res(a["reference"], self.bob)["revision"], 1)
        self.assertEqual(len(self.history(a["reference"], self.bob)["entries"]), 1)

    def test_L272_revision_and_history_stay_in_lockstep_under_concurrent_writers(self):
        refs = [self.ok_book(self.bob, f"{THU}T{h}:00", table=t, party=2)["reference"] for h, t in (("18", "t_1"), ("19", "t_2"), ("20", "t_3"))]
        calls = []
        for i in range(30):
            ref = refs[i % 3]
            calls.append(lambda ref=ref, i=i: self.patch(ref, {"party_size": 1 + i % 2}, self.bob))
        reads = []

        def read(ref):
            h = self.api.call("GET", f"/reservations/{ref}/history", token=self.bob)
            d = self.api.call("GET", f"/reservations/{ref}/decision", token=self.bob)
            reads.append((h, d))
            return h
        calls += [lambda ref=ref: read(ref) for ref in refs * 5]
        outs = self.burst(calls)
        self.assertTrue(all(o.status < 500 for o in outs))
        for h, d in reads:
            ents = h.json["entries"]
            self.assertEqual([e["seq"] for e in ents], list(range(1, len(ents) + 1)))
            self.assertEqual([e["revision"] for e in ents], list(range(1, len(ents) + 1)))
            self.assertTrue(all(set(e["accepted_terms"]) == TERMS_KEYS for e in ents))
        for ref in refs:
            ents = self.history(ref, self.bob)["entries"]
            self.assertEqual(self.decision(ref, self.bob)["revision"], len(ents))
            self.assertEqual(self.get_res(ref, self.bob)["revision"], len(ents))


class History(Base3):
    def test_L206_L207_L208_history_shape_created_entry(self):
        a = self.ok_book(self.bob, T, table="t_2", party=4)
        h = self.history(a["reference"], self.bob)
        self.assertEqual(set(h), {"reference", "entries"})
        self.assertEqual(h["reference"], a["reference"])
        e = h["entries"][0]
        self.assertEqual(set(e), {"seq", "at", "event", "changes", "revision", "accepted_terms"})
        self.assertEqual((e["seq"], e["event"], e["revision"]), (1, "created", 1))
        self.assertRegex(e["at"], RFC)
        self.assertEqual(e["changes"], [{"field": "table_id", "from": None, "to": "t_2"},
                                         {"field": "starts_at_local", "from": None, "to": T},
                                         {"field": "party_size", "from": None, "to": 4}])
        self.assertEqual(e["accepted_terms"], a["accepted_terms"])
        self.assertTrue(self.api.call("GET", f"/reservations/{a['reference']}/history", token=self.bob).ctype.startswith("application/json"))

    def test_L211_changed_entries_name_only_changed_fields_in_fixed_order(self):
        a = self.ok_book(self.bob, T, table="t_2", party=2)
        ref = a["reference"]
        self.patch(ref, {"party_size": 3}, self.bob)
        self.patch(ref, {"party_size": 3, "table_id": "t_2", "starts_at_local": f"{THU}T20:00"}, self.bob)       # only the time changes
        self.patch(ref, {"party_size": 2, "starts_at_local": f"{THU}T21:00", "table_id": "t_3"}, self.bob)       # all three, fixed order
        self.patch(ref, {"table_id": "t_3", "party_size": 2, "starts_at_local": f"{THU}T21:00"}, self.bob)       # no-op
        e = self.history(ref, self.bob)["entries"]
        self.assertEqual([x["event"] for x in e], ["created", "changed", "changed", "changed"])
        self.assertEqual(e[1]["changes"], [{"field": "party_size", "from": 2, "to": 3}])
        self.assertEqual(e[2]["changes"], [{"field": "starts_at_local", "from": T, "to": f"{THU}T20:00"}])
        self.assertEqual(e[3]["changes"], [{"field": "table_id", "from": "t_2", "to": "t_3"},
                                           {"field": "starts_at_local", "from": f"{THU}T20:00", "to": f"{THU}T21:00"},
                                           {"field": "party_size", "from": 3, "to": 2}])
        self.assertEqual([x["revision"] for x in e], [1, 2, 3, 4])

    def test_L207_sequence_is_total_even_for_writes_in_the_same_second(self):
        a = self.ok_book(self.bob, T, table="t_3", party=1)
        for i in range(8):
            self.assertEqual(self.patch(a["reference"], {"party_size": 2 + i % 2}, self.bob).status, 200)
        e = self.history(a["reference"], self.bob)["entries"]
        self.assertEqual([x["seq"] for x in e], list(range(1, 10)))
        ats = [x["at"] for x in e]
        for x in ats:
            self.assertRegex(x, RFC)
        import datetime as dt
        parsed = [dt.datetime.fromisoformat(x.replace("Z", "+00:00")) for x in ats]
        self.assertEqual(parsed, sorted(parsed), "entries are in at order too")

    def test_L212_cancelled_entry_has_empty_changes_and_ends_the_history(self):
        a = self.ok_book(self.bob, T, table="t_2", party=2)
        self.patch(a["reference"], {"party_size": 3}, self.bob)
        self.api.call("POST", f"/reservations/{a['reference']}/cancel", token=self.bob)
        e = self.history(a["reference"], self.bob)["entries"]
        self.assertEqual((e[-1]["event"], e[-1]["changes"], e[-1]["seq"]), ("cancelled", [], 3))
        self.api.call("POST", f"/reservations/{a['reference']}/cancel", token=self.bob)
        self.patch(a["reference"], {"party_size": 1}, self.bob)
        self.assertEqual(len(self.history(a["reference"], self.bob)["entries"]), 3)
        h = self.api.call("GET", f"/reservations/{a['reference']}/history", token=self.bob)
        self.assertEqual(h.status, 200)

    def test_L209_L210_pair_creation_uses_table_ids(self):
        p = self.ok_pair(self.bob, T, ["t_2", "t_1"], 6)                     # reversed input names the declared pair
        self.assertEqual(p["table_ids"], ["t_1", "t_2"], "table sets are normalised to the declared combination order")
        e = self.history(p["reference"], self.bob)["entries"][0]
        self.assertEqual(e["changes"], [{"field": "table_ids", "from": None, "to": ["t_1", "t_2"]},
                                        {"field": "starts_at_local", "from": None, "to": T},
                                        {"field": "party_size", "from": None, "to": 6}])
        s = self.ok_pair(self.bob, f"{THU}T21:00", ["t_3"], 2)               # singleton via table_ids is a single table
        self.assertEqual(self.history(s["reference"], self.bob)["entries"][0]["changes"][0],
                         {"field": "table_id", "from": None, "to": "t_3"})

    def test_L210_changes_involving_a_pair_use_complete_table_id_lists(self):
        a = self.ok_book(self.bob, T, table="t_3", party=2)
        ref = a["reference"]
        self.patch(ref, {"table_ids": ["t_2", "t_1"], "party_size": 5, "starts_at_local": f"{THU}T20:00"}, self.bob)
        self.patch(ref, {"table_ids": ["t_3"]}, self.bob)
        self.patch(ref, {"table_ids": ["t_2", "t_3"]}, self.bob)
        self.patch(ref, {"table_ids": ["t_1", "t_2"]}, self.bob)
        self.patch(ref, {"table_id": "t_1", "party_size": 2}, self.bob)
        e = self.history(ref, self.bob)["entries"]
        self.assertEqual(e[1]["changes"], [{"field": "table_ids", "from": ["t_3"], "to": ["t_1", "t_2"]},
                                           {"field": "starts_at_local", "from": T, "to": f"{THU}T20:00"},
                                           {"field": "party_size", "from": 2, "to": 5}])
        self.assertEqual(e[2]["changes"], [{"field": "table_ids", "from": ["t_1", "t_2"], "to": ["t_3"]}])
        self.assertEqual(e[3]["changes"], [{"field": "table_ids", "from": ["t_3"], "to": ["t_2", "t_3"]}])
        self.assertEqual(e[4]["changes"], [{"field": "table_ids", "from": ["t_2", "t_3"], "to": ["t_1", "t_2"]}])
        self.assertEqual(e[5]["changes"], [{"field": "table_ids", "from": ["t_1", "t_2"], "to": ["t_1"]},
                                           {"field": "party_size", "from": 5, "to": 2}], "pair to single still lists sets")
        self.assertEqual([x["revision"] for x in e], [1, 2, 3, 4, 5, 6])

    def test_L264_reversed_input_pair_is_no_amendment_and_responses_are_normalised(self):
        p = self.ok_pair(self.bob, T, ["t_1", "t_2"], 6)
        r = self.patch(p["reference"], {"table_ids": ["t_2", "t_1"]}, self.bob)
        self.assertEqual((r.status, r.json["revision"], r.json["table_ids"]), (200, 1, ["t_1", "t_2"]))
        self.assertEqual(len(self.history(p["reference"], self.bob)["entries"]), 1)
        self.err(self.pair_book(self.bob, T, ["t_2", "t_1"], 6), 409, "table_unavailable")
        q = self.pair_book(self.bob, f"{THU}T21:00", ["t_3", "t_2"], 6)                    # declared as [t_2, t_3]
        self.assertEqual(q.json["table_ids"], ["t_2", "t_3"])

    def test_L213_replays_record_nothing(self):
        body = {"restaurant_id": "r_anker", "table_id": "t_2", "starts_at_local": T, "party_size": 2}
        first = self.api.call("POST", "/reservations", body, token=self.bob, key="h-1")
        for _ in range(3):
            self.assertEqual(self.api.call("POST", "/reservations", body, token=self.bob, key="h-1").status, 200)
        e = self.history(first.json["reference"], self.bob)["entries"]
        self.assertEqual((len(e), e[0]["revision"]), (1, 1))
        self.assertEqual(len(self.api.call("GET", "/reservations", token=self.bob).json["reservations"]), 1)
        m = self.moves([{"reference": first.json["reference"], "party_size": 3}], self.bob, key="h-2")
        self.assertEqual(m.status, 201)
        for _ in range(2):
            self.moves([{"reference": first.json["reference"], "party_size": 3}], self.bob, key="h-2")
        self.assertEqual(len(self.history(first.json["reference"], self.bob)["entries"]), 2)
        self.assertEqual(self.decision(first.json["reference"], self.bob)["revision"], 2)

    def test_L214_every_entry_carries_its_own_complete_terms(self):
        d1 = add_days(THU, 7)
        a = self.ok_book(self.bob, T, table="t_2", party=2)
        self.ok_publish(policy(d1, duration=60, cutoff=15, capacities={"t_1": 2, "t_2": 4, "t_3": 7}))
        self.patch(a["reference"], {"starts_at_local": f"{d1}T19:00"}, self.bob)
        self.ok_publish(policy(d1, duration=75, cutoff=5, capacities={"t_1": 2, "t_2": 4, "t_3": 8}))           # same date supersedes
        self.patch(a["reference"], {"party_size": 3}, self.bob)
        e = self.history(a["reference"], self.bob)["entries"]
        self.assertEqual([x["accepted_terms"]["policy_version"] for x in e], [0, 1, 2])
        self.assertEqual([x["accepted_terms"]["reservation_duration_minutes"] for x in e], [90, 60, 75])
        self.assertEqual(e[2]["accepted_terms"]["capacities"]["t_3"], 8)
        self.assertEqual(e[0]["accepted_terms"], a["accepted_terms"])
        self.assertEqual(self.get_res(a["reference"], self.bob)["accepted_terms"], e[2]["accepted_terms"])

    def test_L206_history_survives_cancellation_and_is_private(self):
        a = self.ok_book(self.bob, T, table="t_2", party=2)
        self.api.call("POST", f"/reservations/{a['reference']}/cancel", token=self.bob)
        self.assertEqual(len(self.history(a["reference"], self.bob)["entries"]), 2)
        self.err(self.api.call("GET", f"/reservations/{a['reference']}/history", token=self.ada), 404, "not_found")

    def test_L206_other_users_writes_do_not_enter_my_history(self):
        a = self.ok_book(self.bob, T, table="t_2", party=2)
        b = self.ok_book(self.ada, f"{THU}T21:00", table="t_2", party=2)
        self.patch(b["reference"], {"party_size": 3}, self.ada)
        self.assertEqual(len(self.history(a["reference"], self.bob)["entries"]), 1)
        self.assertEqual(len(self.history(b["reference"], self.ada)["entries"]), 2)
