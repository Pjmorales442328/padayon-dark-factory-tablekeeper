"""Stage 3: availability explanations and published policies (ledger 198-205, 216-231, 271, 278, 288-289)."""
import json
import re

from s3common import (Base3, THU, FRI, SUN, T, TERMS_KEYS, add_days, fixture3, policy, hours, seed_res, table, clock_minute)

TABLES = ["t_1", "t_2", "t_3"]
CAPS = {"t_1": 2, "t_2": 4, "t_3": 6}


class Explain(Base3):
    def test_L198_L201_L202_explain_shape_every_table_once_in_fixture_order(self):
        s = self.explain("r_anker", THU, 4)
        self.assertEqual(len(s), 8)
        for local, slot in s.items():
            self.assertEqual(set(slot), {"starts_at_local", "starts_at", "available_table_ids", "available_options", "explain"})
            ex = slot["explain"]
            self.assertEqual([e["table_id"] for e in ex], TABLES)
            for e in ex:
                self.assertEqual(set(e), {"table_id", "policy_version", "available", "rules"})
                self.assertEqual(e["policy_version"], 0)
                self.assertEqual([(r["rule"], set(r)) for r in e["rules"]], [("capacity", {"rule", "holds"}), ("no_overlap", {"rule", "holds"})])
                self.assertTrue(all(isinstance(r["holds"], bool) for r in e["rules"]))
                self.assertIsInstance(e["available"], bool)
        e = s[T]["explain"]
        self.assertEqual([x["rules"][0]["holds"] for x in e], [False, True, True])         # capacity for a party of 4
        self.assertEqual([x["available"] for x in e], [False, True, True])
        self.assertEqual(s[T]["available_table_ids"], ["t_2", "t_3"])

    def test_L203_available_iff_both_rules_hold_and_matches_ids(self):
        self.ok_book(self.bob, T, table="t_3", party=2)                      # t_3 busy at 19:00
        self.ok_book(self.bob, f"{THU}T20:30", table="t_2", party=2)
        for party in (1, 2, 4, 5, 7):
            for slot in self.explain("r_anker", THU, party).values():
                ex = slot["explain"]
                for e in ex:
                    both = all(r["holds"] for r in e["rules"])
                    self.assertEqual(e["available"], both, (party, slot["starts_at_local"], e))
                self.assertEqual([e["table_id"] for e in ex if e["available"]], slot["available_table_ids"])

    def test_L203_both_false_is_reported_as_both_false(self):
        self.ok_book(self.bob, T, table="t_2", party=2)
        e = {x["table_id"]: x for x in self.explain("r_anker", THU, 5)[T]["explain"]}
        self.assertEqual([(r["rule"], r["holds"]) for r in e["t_2"]["rules"]], [("capacity", False), ("no_overlap", False)])
        self.assertFalse(e["t_2"]["available"])
        self.assertEqual([(r["rule"], r["holds"]) for r in e["t_1"]["rules"]], [("capacity", False), ("no_overlap", True)])
        self.assertEqual([(r["rule"], r["holds"]) for r in e["t_3"]["rules"]], [("capacity", True), ("no_overlap", True)])
        self.ok_book(self.bob, T, table="t_1", party=1, key="b2")
        e = {x["table_id"]: x for x in self.explain("r_anker", THU, 1)[T]["explain"]}
        self.assertEqual([(r["rule"], r["holds"]) for r in e["t_1"]["rules"]], [("capacity", True), ("no_overlap", False)])

    def test_L198_rules_independent_cancelled_and_adjacent_bookings(self):
        b = self.ok_book(self.bob, T, table="t_3", party=2)
        self.api.call("POST", f"/reservations/{b['reference']}/cancel", token=self.bob)
        e = {x["table_id"]: x for x in self.explain("r_anker", THU, 2)[T]["explain"]}
        self.assertTrue(e["t_3"]["rules"][1]["holds"], "cancelled bookings do not overlap")
        self.ok_book(self.bob, f"{THU}T20:30", table="t_3", party=2)
        e = {x["table_id"]: x for x in self.explain("r_anker", THU, 2)[T]["explain"]}
        self.assertTrue(e["t_3"]["rules"][1]["holds"], "adjacent bookings do not overlap")
        e = {x["table_id"]: x for x in self.explain("r_anker", THU, 2)[f"{THU}T19:30"]["explain"]}
        self.assertFalse(e["t_3"]["rules"][1]["holds"])

    def test_L203_pair_bookings_overlap_every_member(self):
        self.ok_pair(self.bob, T, ["t_1", "t_2"], 6)
        e = {x["table_id"]: x for x in self.explain("r_anker", THU, 1)[T]["explain"]}
        self.assertEqual([e[t]["rules"][1]["holds"] for t in TABLES], [False, False, True])

    def test_L199_explain_accepts_only_literal_true(self):
        base = f"/availability?restaurant_id=r_anker&date={THU}&party_size=2"
        for v in ("false", "1", "", "True", "TRUE", "0", "yes", "tru", "true%20", "%20true", "null"):
            self.err(self.api.call("GET", f"{base}&explain={v}"), 422, "validation_failed")
        self.err(self.api.call("GET", f"{base}&explain"), 422, "validation_failed")
        self.assertEqual(self.api.call("GET", f"{base}&explain=true").status, 200)
        self.assertEqual(self.api.call("GET", f"{base}&explain=true&explain=false").status, 200)       # first value is used
        self.err(self.api.call("GET", f"{base}&explain=false&explain=true"), 422, "validation_failed")

    def test_L200_without_explain_no_explanation_fields(self):
        r = self.api.call("GET", f"/availability?restaurant_id=r_anker&date={THU}&party_size=2")
        self.assertEqual(set(r.json), {"restaurant_id", "date", "timezone", "slots"})
        for s in r.json["slots"]:
            self.assertEqual(set(s), {"starts_at_local", "starts_at", "available_table_ids", "available_options"})
            self.assertNotIn("explain", json.dumps(s))

    def test_L204_closed_day_and_full_slots(self):
        r = self.api.call("GET", f"/availability?restaurant_id=r_anker&date={SUN}&party_size=2&explain=true")
        self.assertEqual((r.status, r.json["slots"]), (200, []))
        for tid in TABLES:
            self.ok_book(self.bob, T, table=tid, party=1, key=f"f-{tid}")
        s = self.explain("r_anker", THU, 1)[T]
        self.assertEqual(s["available_table_ids"], [])
        self.assertEqual([e["table_id"] for e in s["explain"]], TABLES)
        self.assertTrue(all(e["available"] is False and e["rules"][1]["holds"] is False for e in s["explain"]))
        s = self.explain("r_anker", THU, 99)[T]                               # nothing fits at all
        self.assertEqual(len(s["explain"]), 3)
        self.assertTrue(all(e["rules"][0]["holds"] is False for e in s["explain"]))

    def test_L204_tables_of_other_restaurant_and_order(self):
        f = fixture3()
        f["restaurants"][0]["tables"] = [table("t_z", 4, "Z"), table("t_a", 2, "A"), table("t_m", 6, "M")]
        f["restaurants"][0]["combinable"] = []
        self.reset(f)
        s = self.explain("r_anker", THU, 3)[T]
        self.assertEqual([e["table_id"] for e in s["explain"]], ["t_z", "t_a", "t_m"])
        self.assertEqual(s["available_table_ids"], ["t_z", "t_m"])
        s = self.explain("r_other", THU, 3)[f"{THU}T12:00"]
        self.assertEqual([e["table_id"] for e in s["explain"]], ["t_1", "t_9"])

    def test_L289_explain_validation_before_other_data_and_unknown_restaurant(self):
        self.err(self.api.call("GET", f"/availability?restaurant_id=nope&date={THU}&party_size=2&explain=true"), 404, "not_found")
        self.err(self.api.call("GET", f"/availability?restaurant_id=r_anker&date={THU}&explain=true"), 422, "validation_failed")


class Policies(Base3):
    def test_L216_L217_publication_permissions(self):
        p = policy(f"{THU}")
        self.err(self.api.call("POST", "/restaurants/r_anker/policies", p, key="k1"), 401, "unauthenticated")
        self.err(self.publish(self.bob, p), 403, "forbidden")
        self.err(self.publish(self.ada, p, rest="nope"), 404, "not_found")
        self.err(self.publish(self.bob, p, rest="nope"), 404, "not_found")
        self.err(self.publish(self.ada, p, rest="r_other"), 403, "forbidden")                    # ada manages r_anker only
        self.assertEqual(self.publish(self.bob, policy(THU, rest="r_other"), rest="r_other").status, 201)
        self.err(self.api.call("POST", "/restaurants/r_anker/policies", p, token=self.ada), 400, "missing_idempotency_key")
        self.assertEqual(self.api.call("GET", "/restaurants/r_anker/policies").json, {"policies": []})   # nothing was published

    def test_L216_manager_defaults_empty_and_role_grants_no_diner_access(self):
        f = fixture3()
        for r in f["restaurants"]:
            r.pop("manager_user_ids")
        self.reset(f)
        self.err(self.publish(self.ada, policy(THU)), 403, "forbidden")
        self.reset()
        b = self.ok_book(self.bob, T, table="t_2", party=2)
        ada = self.ada                                                         # a manager
        for path in (f"/reservations/{b['reference']}", f"/reservations/{b['reference']}/history",
                     f"/reservations/{b['reference']}/decision"):
            self.err(self.api.call("GET", path, token=ada), 404, "not_found")
        self.err(self.patch(b["reference"], {"party_size": 3}, ada), 404, "not_found")

    def test_L224_publication_returns_policy_plus_version(self):
        p = policy("2030-02-01", duration=120, slot=60, cutoff=60)
        r = self.publish(self.ada, dict(p, junk="ignored"))
        self.assertEqual(r.status, 201, r)
        for k, v in p.items():
            self.assertEqual(r.json[k], v, k)
        self.assertEqual(r.json["policy_version"], 1)
        self.assertIsInstance(r.json["policy_version"], int)
        self.assertEqual(self.ok_publish(policy("2030-02-02"))["policy_version"], 2)
        self.assertEqual(self.ok_publish(policy("2029-01-01"))["policy_version"], 3)                # past date, any order

    def test_L218_L219_L220_L221_L222_invalid_policies_422_and_allocate_nothing(self):
        good = policy("2030-02-01")
        bad = []
        for k in good:
            bad.append({x: y for x, y in good.items() if x != k})
        for v in ("2030-02-30", "20300201", "2030-2-1", "2030-02-01T00:00", 20300201, None, True, "", "yesterday", "2030-13-01"):
            bad.append(dict(good, effective_from=v))
        for f in ("slot_minutes", "reservation_duration_minutes"):
            for v in (0, -1, 1441, True, False, 1.5, "30", None, [30]):
                bad.append(dict(good, **{f: v}))
        for v in (-1, 10081, True, 1.5, "60", None):
            bad.append(dict(good, cancellation_cutoff_minutes=v))
        o = hours("18:00", "23:00", ["mon"])
        bad += [dict(good, opening_hours=v) for v in (
            "x", {}, None, [{"weekday": "mon", "opens": "18:00", "closes": "18:00"}],
            [{"weekday": "mon", "opens": "19:00", "closes": "18:00"}],
            [{"weekday": "mon", "opens": "18:00", "closes": "23:00"}, {"weekday": "mon", "opens": "10:00", "closes": "12:00"}],
            [{"weekday": "monday", "opens": "18:00", "closes": "23:00"}],
            [{"weekday": "mon", "opens": "6:00", "closes": "23:00"}],
            [{"weekday": "mon", "opens": "18:00", "closes": "24:00"}],
            [{"weekday": "mon", "opens": "22:00", "closes": "02:00"}],
            [{"weekday": "mon", "opens": 1800, "closes": 2300}], [5])]
        caps = {"t_1": 2, "t_2": 4, "t_3": 6}
        bad += [dict(good, capacities=v) for v in (
            {"t_1": 2, "t_2": 4}, {"t_1": 2, "t_2": 4, "t_3": 6, "t_4": 8}, {"t_1": 2, "t_2": 4, "zzz": 6},
            {"t_1": 0, "t_2": 4, "t_3": 6}, {"t_1": 101, "t_2": 4, "t_3": 6}, {"t_1": True, "t_2": 4, "t_3": 6},
            {"t_1": 2.5, "t_2": 4, "t_3": 6}, {"t_1": "2", "t_2": 4, "t_3": 6}, {"t_1": None, "t_2": 4, "t_3": 6},
            {"t_1": -2, "t_2": 4, "t_3": 6}, {}, [], "x", None, {"t_9": 2, "t_1": 1, "t_2": 1})]
        for b in bad:
            r = self.publish(self.ada, b)
            self.assertEqual(r.status, 422, (b, r))
            self.err(r, 422, "validation_failed")
        self.assertEqual(self.api.call("GET", "/restaurants/r_anker/policies").json, {"policies": []})
        r = self.publish(self.ada, dict(good, capacities={"t_1": 100, "t_2": 1, "t_3": 50}))      # boundaries are valid
        self.assertEqual((r.status, r.json["policy_version"]), (201, 1), "invalid writes must not consume a version")
        for f, v in (("slot_minutes", 1440), ("reservation_duration_minutes", 1), ("cancellation_cutoff_minutes", 0)):
            self.assertEqual(self.publish(self.ada, dict(good, **{f: v})).status, 201)
        self.assertEqual(self.publish(self.ada, dict(good, cancellation_cutoff_minutes=10080)).json["policy_version"], 5)

    def test_L222_malformed_bodies_and_state_untouched(self):
        for raw in ("{x", "", "[]", "7", "null"):
            r = self.api.call("POST", "/restaurants/r_anker/policies", raw=raw, token=self.ada, key=self.newkey())
            self.err(r, 400, "malformed_request")
        self.assertEqual(self.ok_publish(policy(THU))["policy_version"], 1)

    def test_L223_policy_cannot_change_tables_timezone_or_combinations(self):
        before = self.api.call("GET", "/restaurants/r_anker").json
        p = dict(policy(THU), timezone="Asia/Tokyo", tables=[{"id": "t_9", "label": "X", "capacity": 3}], combinable=[["t_1", "t_3"]],
                 name="Hijack", id="other")
        self.assertEqual(self.publish(self.ada, p).status, 201)
        self.assertEqual(self.api.call("GET", "/restaurants/r_anker").json, before)
        self.assertEqual(self.api.call("GET", "/availability?restaurant_id=r_anker&date=%s&party_size=2" % THU).json["timezone"],
                         "Europe/Berlin")
        self.err(self.pair_book(self.ada, T, ["t_1", "t_3"], 3), 422, "combination_not_allowed")

    def test_L228_listing_is_public_ordered_and_omits_policy_zero(self):
        a = self.ok_publish(policy("2030-03-01"))
        b = self.ok_publish(policy("2030-01-01", duration=60))
        r = self.api.call("GET", "/restaurants/r_anker/policies")
        self.assertEqual((r.status, r.json), (200, {"policies": [a, b]}))
        self.assertEqual([p["policy_version"] for p in r.json["policies"]], [1, 2])
        self.assertTrue(r.ctype.startswith("application/json"))
        self.err(self.api.call("GET", "/restaurants/nope/policies"), 404, "not_found")
        self.assertEqual(self.api.call("GET", "/restaurants/r_other/policies").json, {"policies": []})

    def test_L271_versions_are_scoped_per_restaurant(self):
        self.assertEqual(self.ok_publish(policy(THU))["policy_version"], 1)
        self.assertEqual(self.ok_publish(policy(THU, rest="r_other"), "r_other", self.bob)["policy_version"], 1)
        self.assertEqual(self.ok_publish(policy(THU))["policy_version"], 2)
        self.assertEqual(self.ok_publish(policy(THU, rest="r_other"), "r_other", self.bob)["policy_version"], 2)

    def test_L225_L229_restaurant_detail_stays_the_original_fixture(self):
        before = self.api.call("GET", "/restaurants/r_anker").json
        self.ok_publish(policy("2020-01-01", duration=30, slot=15, cutoff=0, capacities={"t_1": 9, "t_2": 9, "t_3": 9}))
        after = self.api.call("GET", "/restaurants/r_anker").json
        self.assertEqual(after, before)
        self.assertEqual({t["id"]: t["capacity"] for t in after["tables"]}, CAPS)
        self.assertEqual(after["slot_minutes"], 30)
        self.assertEqual(self.api.call("GET", "/restaurants").json["restaurants"][0],
                         {"id": "r_anker", "name": "Zum Anker", "timezone": "Europe/Berlin"})

    def test_L226_L205_L288_selection_by_local_start_date_not_publication_order(self):
        p1 = self.ok_publish(policy("2030-02-01", duration=120, slot=60, cutoff=30))
        p2 = self.ok_publish(policy("2030-01-15", duration=60, slot=30, cutoff=90))     # published later, effective earlier
        d0, d2, d1 = "2030-01-10", "2030-01-17", "2030-02-05"                           # Thursdays
        for d, ver in ((d0, 0), (d2, 2), (add_days(d2, 7), 2), (d1, 1), ("2030-02-01", 1), ("2030-01-15", 2), ("2030-01-14", 0)):
            ex = self.api.call("GET", f"/availability?restaurant_id=r_anker&date={d}&party_size=1&explain=true")
            self.assertEqual(ex.status, 200)
            vers = {e["policy_version"] for s in ex.json["slots"] for e in s["explain"]}
            if ex.json["slots"]:
                self.assertEqual(vers, {ver}, d)
        # the policy changes slot values: P1 grid 60 min, duration 120 -> 18,19,20,21 ; P2 grid 30, duration 60 -> 18:00..22:00
        t = lambda d: [s["starts_at_local"][11:] for s in self.avail("r_anker", d, 1)["slots"]]
        self.assertEqual(t(d1), ["18:00", "19:00", "20:00", "21:00"])
        self.assertEqual(t(d2), ["18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00", "21:30", "22:00"])
        self.assertEqual(t(d0), ["18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00", "21:30"])

    def test_L226_L288_same_date_ties_choose_greatest_version(self):
        self.ok_publish(policy("2030-02-07", duration=120, slot=60))
        self.ok_publish(policy("2030-02-07", duration=60, slot=30))
        self.ok_publish(policy("2030-02-07", duration=45, slot=15))            # greatest version wins
        s = self.explain("r_anker", "2030-02-07", 1)
        self.assertEqual({e["policy_version"] for x in s.values() for e in x["explain"]}, {3})
        self.assertEqual(list(s)[1][11:], "18:15")

    def test_L227_L228_past_effective_dates_and_new_policy_supersedes_for_future_only(self):
        a = self.ok_book(self.bob, T, table="t_2", party=2)                    # accepted under policy 0
        self.ok_publish(policy("2020-01-01", duration=30, slot=30, cutoff=10))
        again = self.get_res(a["reference"], self.bob)
        self.assertEqual(again, a, "publication must not edit an accepted booking")
        self.assertEqual(self.history(a["reference"], self.bob)["entries"][0]["accepted_terms"]["policy_version"], 0)
        # the booking keeps its accepted end time, so it still occupies [19:00, 20:30)
        s = self.options("r_anker", THU, 1)
        self.assertNotIn("t_2", s[f"{THU}T20:00"]["available_table_ids"])
        self.assertIn("t_2", s[f"{THU}T20:30"]["available_table_ids"])
        self.assertEqual([x["starts_at_local"][11:] for x in s.values()][-1], "22:30")                   # 30 minute duration
        c = self.ok_book(self.bob, f"{THU}T21:00", table="t_2", party=2)
        self.assertEqual((c["accepted_terms"]["policy_version"], c["ends_at"]), (1, f"{THU}T21:30:00+01:00"))

    def test_L205_L230_L231_new_booking_snapshots_the_selected_policy(self):
        caps = {"t_1": 3, "t_2": 5, "t_3": 7}
        op = hours("17:00", "23:00", ["thu"])
        p = self.ok_publish(policy("2030-01-01", duration=60, slot=60, cutoff=45, opening=op, capacities=caps))
        r = self.ok_book(self.bob, f"{THU}T17:00", table="t_1", party=3)                # P1 grid, hours, capacity
        self.assertEqual(r["revision"], 1)
        self.assert_terms(r["accepted_terms"], 1, slot_minutes=60, reservation_duration_minutes=60, cancellation_cutoff_minutes=45,
                          opening_hours=op, capacities=caps)
        self.assertNotIn("effective_from", r["accepted_terms"])
        self.assertEqual((r["starts_at"], r["ends_at"]), (f"{THU}T17:00:00+01:00", f"{THU}T18:00:00+01:00"))
        self.err(self.book(self.bob, f"{THU}T17:30", table="t_2", party=2), 422, "not_on_slot_grid")
        self.err(self.book(self.bob, f"{THU}T16:00", table="t_2", party=2), 422, "outside_opening_hours")
        self.err(self.book(self.bob, f"{THU}T23:00", table="t_2", party=2), 422, "outside_opening_hours")
        self.err(self.book(self.bob, f"{THU}T18:00", table="t_1", party=4), 422, "party_exceeds_capacity")
        self.assertEqual(self.book(self.bob, f"{THU}T18:00", table="t_3", party=7).status, 201)
        # a different date still follows policy 0
        r0 = self.ok_book(self.bob, "2029-01-04T19:00", table="t_2", party=4)
        self.assert_terms(r0["accepted_terms"], 0, slot_minutes=30, reservation_duration_minutes=90, cancellation_cutoff_minutes=120,
                          capacities=CAPS)
        self.err(self.book(self.bob, "2029-01-04T19:00", table="t_1", party=3, key="x"), 422, "party_exceeds_capacity")

    def test_L230_policy_zero_snapshot_matches_fixture(self):
        f = fixture3(reservations=[seed_res(1, "u_bob", "r_anker", "t_2", T, 3, "SEEDAAAA")])
        self.reset(f)
        fx = f["restaurants"][0]
        r = self.ok_book(self.bob, f"{THU}T21:00", table="t_3", party=2)
        self.assertEqual(r["accepted_terms"], {"policy_version": 0, "slot_minutes": 30, "reservation_duration_minutes": 90,
                                               "cancellation_cutoff_minutes": 120, "opening_hours": fx["opening_hours"],
                                               "capacities": CAPS})
        s = self.get_res("SEEDAAAA", self.bob)
        self.assertEqual((s["revision"], s["accepted_terms"]["policy_version"]), (1, 0))

    def test_L231_snapshots_are_copies_not_shared_with_later_publications(self):
        r = self.ok_book(self.bob, T, table="t_2", party=2)
        self.ok_publish(policy("2020-01-01", duration=30, capacities={"t_1": 9, "t_2": 9, "t_3": 9}))
        self.assertEqual(self.get_res(r["reference"], self.bob)["accepted_terms"], r["accepted_terms"])
        self.assertEqual(self.decision(r["reference"], self.bob)["accepted_terms"], r["accepted_terms"])
        a = self.api.call("GET", f"/reservations/{r['reference']}", token=self.bob).json
        b = self.api.call("GET", "/reservations", token=self.bob).json["reservations"][0]
        self.assertEqual(a, b)

    def test_L263_pair_capacity_is_summed_from_the_selected_policy(self):
        self.ok_publish(policy("2030-01-01", capacities={"t_1": 1, "t_2": 1, "t_3": 20}))
        self.err(self.pair_book(self.bob, T, ["t_1", "t_2"], 3), 422, "party_exceeds_capacity")
        self.assertEqual(self.pair_book(self.bob, T, ["t_1", "t_2"], 2).status, 201)
        self.assertEqual(self.pair_book(self.bob, f"{THU}T21:00", ["t_2", "t_3"], 21).status, 201)
        later = add_days(THU, 7)                                              # a free Thursday under the same policy
        o = self.options("r_anker", later, 21)[f"{later}T19:00"]["available_options"]
        self.assertEqual([x["table_ids"] for x in o], [["t_2", "t_3"]])
        self.assertEqual(o[0]["capacity"], 21)
        o = self.options("r_anker", "2029-01-04", 5)["2029-01-04T19:00"]["available_options"]    # policy 0 date
        self.assertEqual([x["capacity"] for x in o], [6, 6, 10])

    def test_L224_L277_policy_idempotency(self):
        p = policy(THU)
        a = self.publish(self.ada, p, key="pk-1")
        b = self.publish(self.ada, p, key="pk-1")
        self.assertEqual((a.status, b.status, a.json), (201, 200, b.json))
        self.assertEqual(self.api.call("GET", "/restaurants/r_anker/policies").json["policies"], [a.json])
        self.err(self.publish(self.ada, dict(p, slot_minutes=15), key="pk-1"), 409, "idempotency_key_reuse")
        self.err(self.publish(self.ada, {}, key="pk-1"), 409, "idempotency_key_reuse")            # even if the new body is invalid
        self.assertEqual(self.publish(self.ada, dict(p, effective_from="2030-05-01"), key="pk-2").json["policy_version"], 2)
        # replay allocates nothing
        self.assertEqual(self.publish(self.ada, p, key="pk-1").json["policy_version"], 1)
        self.assertEqual(self.publish(self.ada, dict(p, effective_from="2030-06-01"), key="pk-3").json["policy_version"], 3)
        # failed keys are reusable; same key in another path or user is independent
        self.err(self.publish(self.ada, dict(p, slot_minutes=0), key="pk-4"), 422, "validation_failed")
        self.assertEqual(self.publish(self.ada, p, key="pk-4").status, 201)
        self.assertEqual(self.api.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_id": "t_2", "starts_at_local": T,
                                                                  "party_size": 2}, token=self.ada, key="pk-1").status, 201)
        self.err(self.publish(self.bob, p, key="pk-1"), 403, "forbidden")

    def test_L224_concurrent_identical_publication_is_one_operation(self):
        p = policy(THU)
        outs = self.burst([lambda: self.publish(self.ada, p, key="cp-1")] * 15)
        self.assertEqual(sorted(o.status for o in outs), [200] * 14 + [201])
        self.assertEqual(len({json.dumps(o.json, sort_keys=True) for o in outs}), 1)
        self.assertEqual(len(self.api.call("GET", "/restaurants/r_anker/policies").json["policies"]), 1)

    def test_L271_L285_concurrent_distinct_publications_get_unique_consecutive_versions(self):
        outs = self.burst([lambda i=i: self.publish(self.ada, policy(add_days("2030-01-01", i)), key=f"cd-{i}") for i in range(20)])
        self.assertTrue(all(o.status == 201 for o in outs))
        self.assertEqual(sorted(o.json["policy_version"] for o in outs), list(range(1, 21)))
        listed = self.api.call("GET", "/restaurants/r_anker/policies").json["policies"]
        self.assertEqual(sorted(p["policy_version"] for p in listed), list(range(1, 21)))
        for o in outs:
            self.assertIn(o.json, listed)

    def test_L278_reset_validates_manager_user_ids(self):
        def rej(v):
            f = fixture3()
            f["restaurants"][0]["manager_user_ids"] = v
            self.err(self.api.call("POST", "/_test/reset", f), 422, "validation_failed")
            self.assertEqual(self.api.call("GET", "/restaurants/r_anker").status, 200)
        for v in ("u_ada", {"a": 1}, [1], [True], [None], ["u_ada", "u_ada"], ["u_nobody"], ["u_ada", "nobody"], None, [["u_ada"]]):
            rej(v)
        f = fixture3()
        f["restaurants"][0]["manager_user_ids"] = ["u_ada", "u_bob"]
        self.assertEqual(self.api.call("POST", "/_test/reset", f).status, 204)
        self.assertEqual(self.publish(self.bob, policy(THU)).status, 201)
        f["restaurants"][0]["manager_user_ids"] = []
        self.assertEqual(self.api.call("POST", "/_test/reset", f).status, 204)

    def test_L279_reset_clears_policies_and_versions(self):
        self.ok_publish(policy(THU))
        self.ok_publish(policy(THU))
        self.reset()
        self.assertEqual(self.api.call("GET", "/restaurants/r_anker/policies").json, {"policies": []})
        self.assertEqual(self.ok_publish(policy(THU))["policy_version"], 1)

    def test_L205_policy_changes_what_is_bookable_on_the_clock_restaurant(self):
        self.ok_publish(policy("2000-01-01", duration=20, slot=5, cutoff=0, rest="r_clock"), rest="r_clock")
        local = clock_minute(60 * 24 * 3)
        local = local[:-2] + "%02d" % (int(local[-2:]) // 5 * 5)                 # the policy grid is 5 minutes
        r = self.ok_book(self.bob, local, rest="r_clock", table="t_1", party=2)
        self.assertEqual((r["accepted_terms"]["policy_version"], r["accepted_terms"]["cancellation_cutoff_minutes"]), (1, 0))
        self.assertEqual(self.api.call("POST", f"/reservations/{r['reference']}/cancel", token=self.bob).status, 200)
