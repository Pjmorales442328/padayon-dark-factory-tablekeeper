"""Stage 2 API checks: combined tables, options, amendments, moves, seeds, validation, races (ledger 22,58,62,69,78,81,
105,156-188). Written from requirements-stage-2.md only."""
import copy
import json
import unittest

from s2common import (Base2, THU, FRI, SUN, fixture2, seed_res, hours, table, LABELS)

T = f"{THU}T19:00"


def pair_ids(opts):
    return [o["table_ids"] for o in opts]


class Options(Base2):
    def test_L058_L161_L162_options_shape_order_and_single_ids_unchanged(self):
        s = self.options("r_anker", THU, 5)[T]
        self.assertEqual(s["available_table_ids"], ["t_3"])                 # singles only, as in stage 1
        self.assertEqual(s["available_options"], [
            {"table_ids": ["t_3"], "capacity": 6},
            {"table_ids": ["t_1", "t_2"], "capacity": 6},
            {"table_ids": ["t_2", "t_3"], "capacity": 10}])
        self.assertEqual(set(s), {"starts_at_local", "starts_at", "available_table_ids", "available_options"})
        s = self.options("r_anker", THU, 1)[T]
        self.assertEqual(s["available_table_ids"], ["t_1", "t_2", "t_3"])
        self.assertEqual(pair_ids(s["available_options"]), [["t_1"], ["t_2"], ["t_3"], ["t_1", "t_2"], ["t_2", "t_3"]])
        self.assertEqual([o["capacity"] for o in s["available_options"]], [2, 4, 6, 6, 10])

    def test_L158_L163_capacity_filter_on_pairs(self):
        self.assertEqual(pair_ids(self.options("r_anker", THU, 7)[T]["available_options"]), [["t_2", "t_3"]])
        self.assertEqual(self.options("r_anker", THU, 7)[T]["available_table_ids"], [])
        self.assertEqual(pair_ids(self.options("r_anker", THU, 10)[T]["available_options"]), [["t_2", "t_3"]])
        self.assertEqual(self.options("r_anker", THU, 11)[T]["available_options"], [])
        self.assertEqual(pair_ids(self.options("r_anker", THU, 6)[T]["available_options"]),
                         [["t_3"], ["t_1", "t_2"], ["t_2", "t_3"]])      # capacity >= party (6 == 6 qualifies)

    def test_L163_pair_listed_in_reverse_keeps_combinable_order(self):
        self.reset(fixture2(combinable=[["t_3", "t_2"], ["t_1", "t_2"]]))
        ids = pair_ids(self.options("r_anker", THU, 5)[T]["available_options"])
        self.assertEqual(ids, [["t_3"], ["t_3", "t_2"], ["t_1", "t_2"]])

    def test_L164_pair_omitted_when_any_member_occupied(self):
        self.ok_book(self.ada, T, table="t_2", party=2)
        ids = pair_ids(self.options("r_anker", THU, 1)[T]["available_options"])
        self.assertEqual(ids, [["t_1"], ["t_3"]])
        self.reset()
        self.ok_book(self.ada, T, table="t_1", party=2)
        ids = pair_ids(self.options("r_anker", THU, 1)[T]["available_options"])
        self.assertEqual(ids, [["t_2"], ["t_3"], ["t_2", "t_3"]])
        self.assertEqual(self.options("r_anker", THU, 1)[T]["available_table_ids"], ["t_2", "t_3"])

    def test_L159_L164_pair_booking_blocks_overlapping_slots_only(self):
        self.ok_pair(self.ada, T, ["t_1", "t_2"], 6)
        m = self.options("r_anker", THU, 1)
        for h, busy in (("18:00", True), ("18:30", True), ("19:00", True), ("19:30", True), ("20:00", True),
                        ("20:30", False), ("21:00", False)):
            s = m[f"{THU}T{h}"]
            self.assertEqual("t_1" not in s["available_table_ids"], busy, h)
            self.assertEqual("t_2" not in s["available_table_ids"], busy, h)
            self.assertIn("t_3", s["available_table_ids"], h)
        self.assertNotIn(["t_2", "t_3"], pair_ids(m[T]["available_options"]))
        self.assertIn(["t_2", "t_3"], pair_ids(m[f"{THU}T20:30"]["available_options"]))

    def test_L164_L156_cross_restaurant_pairs_independent(self):
        self.ok_pair(self.ada, T, ["t_1", "t_2"], 6)
        self.assertEqual(pair_ids(self.options("r_other", THU, 1)[f"{THU}T12:00"]["available_options"]),
                         [["t_1"], ["t_9"], ["t_1", "t_9"]])
        self.assertEqual(self.book(self.ada, f"{THU}T19:00", table="t_1", rest="r_other", party=8).status, 201)

    def test_L156_L157_no_pairs_when_absent_or_empty(self):
        for comb in ([], None):
            f = fixture2()
            if comb is None:
                for r in f["restaurants"]:
                    r.pop("combinable", None)
            else:
                f["restaurants"][0]["combinable"] = comb
            self.reset(f)
            s = self.options("r_anker", THU, 1)[T]
            self.assertEqual(pair_ids(s["available_options"]), [["t_1"], ["t_2"], ["t_3"]])
            self.err(self.pair_book(self.ada, T, ["t_1", "t_2"], 3), 422, "combination_not_allowed")

    def test_L054_L156_restaurant_detail_has_combinable(self):
        r = self.api.call("GET", "/restaurants/r_anker").json
        self.assertEqual(r.get("combinable"), [["t_1", "t_2"], ["t_2", "t_3"]])
        self.assertEqual(r["tables"], fixture2()["restaurants"][0]["tables"])

    def test_L061_closed_day_has_no_options(self):
        j = self.avail("r_anker", SUN, 1)
        self.assertEqual(j["slots"], [])

    def test_L058_options_present_on_full_slots(self):
        for tid in ("t_1", "t_2", "t_3"):
            self.ok_book(self.ada, T, table=tid, party=1)
        s = self.options("r_anker", THU, 1)[T]
        self.assertEqual((s["available_table_ids"], s["available_options"]), ([], []))


class Create(Base2):
    def test_L062_L166_shapes(self):
        pair = self.ok_pair(self.ada, T, ["t_1", "t_2"], 6)
        self.assertEqual(sorted(pair["table_ids"]), ["t_1", "t_2"])
        self.assertNotIn("table_id", pair)
        self.assertEqual(set(pair), {"reservation_id", "reference", "restaurant_id", "table_ids", "party_size", "status",
                                    "starts_at_local", "starts_at", "ends_at", "created_at"})
        self.assertEqual((pair["starts_at"], pair["ends_at"]), (f"{THU}T19:00:00+01:00", f"{THU}T20:30:00+01:00"))
        single = self.ok_pair(self.ada, T, ["t_3"], 2)
        self.assertEqual((single["table_id"], single["table_ids"]), ("t_3", ["t_3"]))
        legacy = self.ok_book(self.ada, f"{THU}T21:00", table="t_3", party=2)
        self.assertEqual((legacy["table_id"], legacy["table_ids"]), ("t_3", ["t_3"]))
        for r in (pair, single, legacy):
            got = self.api.call("GET", f"/reservations/{r['reference']}", token=self.ada).json
            self.assertEqual(got, r)

    def test_L165_both_selectors_rejected(self):
        self.err(self.api.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_id": "t_1", "table_ids": ["t_1"],
                                                          "starts_at_local": T, "party_size": 1},
                               token=self.ada, key="k1"), 422, "validation_failed")
        self.err(self.api.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_id": "t_1", "table_ids": [],
                                                          "starts_at_local": T, "party_size": 1},
                               token=self.ada, key="k2"), 422, "validation_failed")
        self.assertEqual(self.api.call("GET", "/reservations", token=self.ada).json, {"reservations": []})

    def test_L165_neither_selector_rejected(self):
        self.err(self.api.call("POST", "/reservations", {"restaurant_id": "r_anker", "starts_at_local": T,
                                                          "party_size": 1}, token=self.ada, key="k3"),
                 422, "validation_failed")

    def test_L167_not_combinable_and_more_than_two(self):
        for ids in (["t_1", "t_3"], ["t_3", "t_1"]):                  # not transitive: t1-t2 and t2-t3 only
            self.err(self.pair_book(self.ada, T, ids, 3), 422, "combination_not_allowed")
        self.err(self.pair_book(self.ada, T, ["t_1", "t_2", "t_3"], 3), 422, "combination_not_allowed")
        self.err(self.pair_book(self.ada, T, ["t_1", "t_2", "t_3", "t_1"], 3), 422, "combination_not_allowed")
        self.assertEqual(self.api.call("GET", "/reservations", token=self.ada).json, {"reservations": []})

    def test_L167_not_combinable_regardless_of_capacity(self):
        self.err(self.pair_book(self.ada, T, ["t_1", "t_3"], 8), 422, "combination_not_allowed")

    def test_L157_L158_any_declared_order_works(self):
        for ids, start in ((["t_2", "t_1"], T), (["t_3", "t_2"], f"{THU}T21:00")):
            r = self.pair_book(self.ada, start, ids, 5)
            self.assertEqual(r.status, 201, r)
            self.assertEqual(sorted(r.json["table_ids"]), sorted(ids))
            self.assertNotIn("table_id", r.json)

    def test_L168_duplicates_and_empty(self):
        for ids in (["t_1", "t_1"], ["t_2", "t_2"], []):
            self.err(self.pair_book(self.ada, T, ids, 1), 422, "validation_failed")

    def test_L168_wrong_types_are_400(self):
        for ids in ("t_1", 5, {"a": 1}, [1, 2], [["t_1"]], [None], True):
            r = self.pair_book(self.ada, T, ids, 1)
            self.assertEqual(r.status, 400, (ids, r))
            self.err(r, 400, "malformed_request")

    def test_L169_unknown_and_foreign_members_404(self):
        self.err(self.pair_book(self.ada, T, ["t_1", "zzz"], 2), 404, "not_found")
        self.err(self.pair_book(self.ada, T, ["zzz"], 2), 404, "not_found")
        self.err(self.pair_book(self.ada, T, ["t_9"], 2), 404, "not_found")          # belongs to r_other
        self.err(self.pair_book(self.ada, T, ["t_1", "t_9"], 2), 404, "not_found")
        self.err(self.pair_book(self.ada, T, ["t_1", "t_2"], 2, rest="nope"), 404, "not_found")
        self.err(self.pair_book(self.ada, T, ["t_2", "t_9"], 2, rest="r_other"), 404, "not_found")
        self.assertEqual(self.pair_book(self.ada, T, ["t_1", "t_9"], 9, rest="r_other").status, 201)   # r_other pair

    def test_L069_L170_summed_capacity(self):
        self.err(self.pair_book(self.ada, T, ["t_1", "t_2"], 7), 422, "party_exceeds_capacity")
        self.err(self.pair_book(self.ada, T, ["t_1", "t_2"], 100), 422, "party_exceeds_capacity")
        self.err(self.pair_book(self.ada, T, ["t_3"], 7), 422, "party_exceeds_capacity")
        self.assertEqual(self.pair_book(self.ada, T, ["t_1", "t_2"], 6).status, 201)
        self.err(self.pair_book(self.ada, f"{THU}T21:00", ["t_2", "t_3"], 11), 422, "party_exceeds_capacity")
        self.assertEqual(self.pair_book(self.ada, f"{THU}T21:00", ["t_2", "t_3"], 10).status, 201)
        # a pair may be booked for a party that fits a single table
        self.assertEqual(self.pair_book(self.ada, f"{THU}T18:00", ["t_2", "t_3"], 1).status, 201)

    def test_L170_any_member_overlap_is_409(self):
        self.ok_pair(self.ada, T, ["t_1", "t_2"], 6)
        for ids, start in ((["t_2"], T), (["t_1"], f"{THU}T19:30"), (["t_2", "t_3"], f"{THU}T20:00"),
                           (["t_1", "t_2"], f"{THU}T18:00")):
            self.err(self.pair_book(self.bob, start, ids, 1), 409, "table_unavailable")
        self.assertEqual(self.pair_book(self.bob, T, ["t_3"], 1).status, 201)        # disjoint member set
        self.assertEqual(self.pair_book(self.bob, f"{THU}T20:30", ["t_2", "t_3"], 5).status, 201)   # adjacent

    def test_L159_L188_both_members_occupied_for_full_duration_each(self):
        j = self.ok_pair(self.ada, T, ["t_2", "t_3"], 8)
        self.err(self.book(self.bob, f"{THU}T19:30", table="t_3", party=1), 409, "table_unavailable")
        self.err(self.book(self.bob, f"{THU}T20:00", table="t_2", party=1), 409, "table_unavailable")
        self.assertEqual(self.book(self.bob, f"{THU}T20:30", table="t_2", party=1).status, 201)
        self.assertEqual(self.book(self.bob, T, table="t_1", party=1).status, 201)

    def test_L164_pair_of_other_restaurant_same_ids(self):
        self.ok_pair(self.ada, T, ["t_1", "t_9"], 9, rest="r_other")
        self.assertEqual(self.pair_book(self.bob, T, ["t_1", "t_2"], 6).status, 201)         # r_anker t_1 unaffected

    def test_L170_validation_order_inherited(self):
        self.err(self.pair_book(self.ada, f"{THU}T19:15", ["t_1", "t_2"], 6), 422, "not_on_slot_grid")
        self.err(self.pair_book(self.ada, f"{THU}T22:00", ["t_1", "t_2"], 6), 422, "outside_opening_hours")
        self.err(self.pair_book(self.ada, T, ["t_1", "t_2"], 0), 422, "validation_failed")
        self.err(self.pair_book(self.ada, T, ["t_1", "t_2"], "6"), 422, "validation_failed")
        self.err(self.api.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_ids": ["t_1", "t_2"],
                                                          "starts_at_local": 5, "party_size": 3}, token=self.ada,
                               key="kk"), 400, "malformed_request")

    def test_L179_pair_receipts_replay_and_body_comparison(self):
        t = self.ada
        body = {"restaurant_id": "r_anker", "table_ids": ["t_1", "t_2"], "starts_at_local": T, "party_size": 6}
        a = self.api.call("POST", "/reservations", body, token=t, key="pk-1")
        b = self.api.call("POST", "/reservations", body, token=t, key="pk-1")
        self.assertEqual((a.status, b.status, a.json), (201, 200, b.json))
        raw = '{"party_size":6,"starts_at_local":"%s","table_ids":["t_1","t_2"],"restaurant_id":"r_anker"}' % T
        c = self.api.call("POST", "/reservations", raw=raw, token=t, key="pk-1")
        self.assertEqual((c.status, c.json), (200, a.json))
        # array order is part of the JSON value
        self.err(self.api.call("POST", "/reservations", dict(body, table_ids=["t_2", "t_1"]), token=t, key="pk-1"),
                 409, "idempotency_key_reuse")
        # table_id (legacy) vs table_ids singleton are different bodies
        s = self.api.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_id": "t_3",
                                                     "starts_at_local": T, "party_size": 2}, token=t, key="pk-2")
        self.assertEqual(s.status, 201)
        self.err(self.api.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_ids": ["t_3"],
                                                          "starts_at_local": T, "party_size": 2}, token=t, key="pk-2"),
                 409, "idempotency_key_reuse")
        # replay after amendment and cancellation
        ref = a.json["reference"]
        self.assertEqual(self.api.call("PATCH", f"/reservations/{ref}", {"starts_at_local": f"{THU}T21:00"}, token=t).status, 200)
        self.assertEqual(self.api.call("POST", f"/reservations/{ref}/cancel", token=t).status, 200)
        d = self.api.call("POST", "/reservations", body, token=t, key="pk-1")
        self.assertEqual((d.status, d.json), (200, a.json))
        self.assertEqual(d.json["status"], "confirmed")
        self.assertEqual(len(self.api.call("GET", "/reservations", token=t).json["reservations"]), 2)

    def test_L051_L179_concurrent_identical_pair_create(self):
        t = self.ada
        body = {"restaurant_id": "r_anker", "table_ids": ["t_1", "t_2"], "starts_at_local": T, "party_size": 6}
        outs = self.burst([lambda: self.api.call("POST", "/reservations", body, token=t, key="cpk")] * 20)
        self.assertEqual(sorted(o.status for o in outs), [200] * 19 + [201])
        self.assertEqual(len({json.dumps(o.json, sort_keys=True) for o in outs}), 1)

    def test_L050_failed_pair_keys_do_not_consume(self):
        t = self.ada
        body = {"restaurant_id": "r_anker", "table_ids": ["t_1", "t_3"], "starts_at_local": T, "party_size": 3}
        self.err(self.api.call("POST", "/reservations", body, token=t, key="fk"), 422, "combination_not_allowed")
        ok = self.api.call("POST", "/reservations", dict(body, table_ids=["t_1", "t_2"]), token=t, key="fk")
        self.assertEqual(ok.status, 201, ok)


class Amend(Base2):
    def test_L171_patch_between_single_and_pair(self):
        t = self.ada
        a = self.ok_book(t, T, table="t_3", party=5)
        ref = a["reference"]
        r = self.api.call("PATCH", f"/reservations/{ref}", {"table_ids": ["t_1", "t_2"]}, token=t)
        self.assertEqual(r.status, 200, r)
        self.assertEqual(sorted(r.json["table_ids"]), ["t_1", "t_2"])
        self.assertNotIn("table_id", r.json)
        for k in ("reservation_id", "reference", "created_at", "party_size", "starts_at_local"):
            self.assertEqual(r.json[k], a[k])
        s = self.options("r_anker", THU, 1)[T]
        self.assertEqual(s["available_table_ids"], ["t_3"])                 # t_3 released, t_1/t_2 taken
        r = self.api.call("PATCH", f"/reservations/{ref}", {"table_ids": ["t_3"]}, token=t)
        self.assertEqual((r.status, r.json["table_id"], r.json["table_ids"]), (200, "t_3", ["t_3"]))
        self.assertEqual(self.options("r_anker", THU, 1)[T]["available_table_ids"], ["t_1", "t_2"])
        r = self.api.call("PATCH", f"/reservations/{ref}", {"table_ids": ["t_2", "t_3"], "party_size": 9}, token=t)
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json["party_size"], 9)
        r = self.api.call("PATCH", f"/reservations/{ref}", {"table_id": "t_1", "party_size": 2}, token=t)
        self.assertEqual((r.status, r.json["table_id"]), (200, "t_1"))

    def test_L171_patch_rules_same_as_create(self):
        t = self.ada
        a = self.ok_pair(t, T, ["t_1", "t_2"], 6)
        P = lambda b: self.api.call("PATCH", f"/reservations/{a['reference']}", b, token=t)
        self.err(P({"table_ids": ["t_1", "t_3"]}), 422, "combination_not_allowed")
        self.err(P({"table_ids": ["t_1", "t_2", "t_3"]}), 422, "combination_not_allowed")
        self.err(P({"table_ids": ["t_1", "t_1"]}), 422, "validation_failed")
        self.err(P({"table_ids": []}), 422, "validation_failed")
        self.err(P({"table_ids": ["t_1", "zzz"]}), 404, "not_found")
        self.err(P({"table_ids": ["t_1", "t_9"]}), 404, "not_found")
        self.err(P({"table_ids": "t_1"}), 400, "malformed_request")
        self.err(P({"table_id": "t_1", "table_ids": ["t_1"]}), 422, "validation_failed")
        self.err(P({"party_size": 7}), 422, "party_exceeds_capacity")
        self.err(P({"table_ids": ["t_2", "t_3"], "party_size": 11}), 422, "party_exceeds_capacity")
        self.assertEqual(self.api.call("GET", f"/reservations/{a['reference']}", token=t).json, a)
        self.assertEqual(pair_ids(self.options("r_anker", THU, 1)[T]["available_options"]), [["t_3"]])

    def test_L171_failed_amendment_changes_nothing(self):
        t = self.ada
        a = self.ok_pair(t, T, ["t_1", "t_2"], 6)
        other = self.ok_book(self.bob, T, table="t_3", party=2)
        r = self.api.call("PATCH", f"/reservations/{a['reference']}", {"table_ids": ["t_2", "t_3"], "party_size": 5}, token=t)
        self.err(r, 409, "table_unavailable")
        self.assertEqual(self.api.call("GET", f"/reservations/{a['reference']}", token=t).json, a)
        self.assertEqual(self.options("r_anker", THU, 1)[T]["available_table_ids"], [])
        # moving a pair so that it overlaps only itself is fine
        r = self.api.call("PATCH", f"/reservations/{a['reference']}", {"starts_at_local": f"{THU}T19:30"}, token=t)
        self.assertEqual(r.status, 200, r)

    def test_L081_L173_noop_pair_reordering(self):
        t = self.ada
        a = self.ok_pair(t, T, ["t_1", "t_2"], 6)
        for body in ({"table_ids": ["t_2", "t_1"]}, {"table_ids": ["t_1", "t_2"]}, {},
                     {"table_ids": ["t_2", "t_1"], "party_size": 6, "starts_at_local": T}):
            r = self.api.call("PATCH", f"/reservations/{a['reference']}", body, token=t)
            self.assertEqual(r.status, 200, (body, r))
            self.assertEqual(r.json, a)
        self.err(self.book(self.bob, T, table="t_2"), 409, "table_unavailable")
        # singleton no-op: table_ids [x] equals table_id x
        s = self.ok_book(t, f"{THU}T21:00", table="t_3", party=2)
        r = self.api.call("PATCH", f"/reservations/{s['reference']}", {"table_ids": ["t_3"]}, token=t)
        self.assertEqual((r.status, r.json), (200, s))

    def test_L172_cancel_frees_every_member_and_repeats(self):
        t = self.ada
        a = self.ok_pair(t, T, ["t_2", "t_3"], 8)
        c1 = self.api.call("POST", f"/reservations/{a['reference']}/cancel", token=t)
        self.assertEqual((c1.status, c1.json["status"]), (200, "cancelled"))
        self.assertEqual(sorted(c1.json["table_ids"]), ["t_2", "t_3"])
        self.assertNotIn("table_id", c1.json)
        self.assertEqual(self.options("r_anker", THU, 1)[T]["available_table_ids"], ["t_1", "t_2", "t_3"])
        self.assertEqual(self.pair_book(self.bob, T, ["t_1", "t_2"], 6).status, 201)
        self.assertEqual(self.api.call("POST", f"/reservations/{a['reference']}/cancel", token=t).json, c1.json)

    def test_L079_patch_cancelled_pair_conflict_code(self):
        t = self.ada
        a = self.ok_pair(t, T, ["t_1", "t_2"], 6)
        self.api.call("POST", f"/reservations/{a['reference']}/cancel", token=t)
        self.err(self.api.call("PATCH", f"/reservations/{a['reference']}", {"table_ids": ["t_2", "t_3"]}, token=t),
                 409, "reservation_cancelled")

    def test_L073_list_order_and_shapes_with_pairs(self):
        t = self.ada
        a = self.ok_pair(t, T, ["t_1", "t_2"], 6)
        b = self.ok_book(t, f"{FRI}T19:00", table="t_3", party=2)
        got = self.api.call("GET", "/reservations", token=t).json["reservations"]
        self.assertEqual(got, [b, a])


class Seeds(Base2):
    def test_L022_L160_seed_table_ids_and_status(self):
        f = fixture2(reservations=[
            seed_res(1, "u_ada", "r_anker", "t_3", T, 2, "SEEDSNG1"),
            dict(seed_res(2, "u_bob", "r_anker", "t_1", T, 5, "SEEDPAIR"), table_ids=["t_1", "t_2"]),
        ])
        del f["reservations"][1]["table_id"]
        f["reservations"].append(dict(seed_res(3, "u_ada", "r_anker", "t_3", f"{THU}T21:00", 2, "SEEDCNCL"), status="cancelled"))
        f["reservations"].append(dict(seed_res(4, "u_ada", "r_anker", "t_2", f"{THU}T21:00", 2, "SEEDCONF"), status="confirmed"))
        self.reset(f)
        ada, bob = self.ada, self.bob
        s = self.api.call("GET", "/reservations/SEEDSNG1", token=ada).json
        self.assertEqual((s["status"], s["table_id"], s["table_ids"], s["reservation_id"]), ("confirmed", "t_3", ["t_3"], "res_s1"))
        p = self.api.call("GET", "/reservations/SEEDPAIR", token=bob).json
        self.assertEqual((p["status"], p["table_ids"], p["reservation_id"], p["party_size"]), ("confirmed", ["t_1", "t_2"], "res_s2", 5))
        self.assertNotIn("table_id", p)
        c = self.api.call("GET", "/reservations/SEEDCNCL", token=ada).json
        self.assertEqual((c["status"], c["table_ids"]), ("cancelled", ["t_3"]))
        # cancelled seed occupies nothing: t_3 at 21:00 is free, confirmed seed on t_2 is not
        m = self.options("r_anker", THU, 1)
        self.assertIn("t_3", m[f"{THU}T21:00"]["available_table_ids"])
        self.assertNotIn("t_2", m[f"{THU}T21:00"]["available_table_ids"])
        self.assertNotIn("t_1", m[T]["available_table_ids"])         # pair seed occupies both members
        self.assertNotIn("t_2", m[T]["available_table_ids"])
        self.assertNotIn("t_3", m[T]["available_table_ids"])
        self.assertEqual(self.book(ada, f"{THU}T21:00", table="t_3", party=2).status, 201)

    def test_L160_L188_cancelled_seed_may_overlap_confirmed(self):
        f = fixture2(reservations=[seed_res(1, "u_ada", "r_anker", "t_2", T, 2, "SEEDAAAA"),
                                   dict(seed_res(2, "u_bob", "r_anker", "t_2", T, 2, "SEEDBBBB"), status="cancelled")])
        self.assertEqual(self.api.call("POST", "/_test/reset", f).status, 204)

    def test_L182_L096_invalid_seeds_rejected(self):
        def rej(res):
            self.err(self.api.call("POST", "/_test/reset", fixture2(reservations=res)), 422, "validation_failed")
            self.assertEqual(self.api.call("GET", "/restaurants/r_anker").status, 200)   # untouched
        base = seed_res(1, "u_ada", "r_anker", "t_1", T, 2, "SEEDAAAA")
        pair = dict(seed_res(2, "u_bob", "r_anker", "t_1", T, 5, "SEEDBBBB"), table_ids=["t_1", "t_2"])
        del pair["table_id"]
        rej([base, pair])                                                       # overlap on t_1
        for bad in (["t_1", "t_3"], ["t_1", "t_1"], ["t_1", "t_2", "t_3"], [], ["t_1", "zzz"], ["t_1", "t_9"], "t_1", [1, 2]):
            p = dict(pair, table_ids=bad)
            rej([p])
        rej([dict(pair, table_id="t_1")])                                       # both selectors
        rej([dict(pair, party_size=7)])                                         # over summed capacity
        rej([dict(base, status="bogus")])
        rej([dict(base, status=5)])
        # status confirmed + cancelled both accepted
        for st in ("confirmed", "cancelled"):
            self.assertEqual(self.api.call("POST", "/_test/reset", fixture2(reservations=[dict(base, status=st)])).status, 204)
        self.reset()

    def test_L182_combinable_declarations_validated(self):
        def rej(comb, what):
            f = fixture2()
            f["restaurants"][0]["combinable"] = comb
            self.err(self.api.call("POST", "/_test/reset", f), 422, "validation_failed")
            self.assertEqual(self.api.call("GET", "/restaurants/r_anker").json["combinable"],
                             [["t_1", "t_2"], ["t_2", "t_3"]], what)
        rej("t_1", "string")
        rej({"a": 1}, "object")
        rej([["t_1"]], "singleton entry")
        rej([["t_1", "t_2", "t_3"]], "triple")
        rej([[]], "empty entry")
        rej([["t_1", "t_1"]], "same member twice")
        rej([["t_1", "zzz"]], "unknown table")
        rej([["t_1", "t_9"]], "table of other restaurant")
        rej([[1, 2]], "non string members")
        rej([["t_1", None]], "null member")
        rej([["t_1", "t_2"], ["t_2", "t_1"]], "unordered duplicate")
        rej([["t_1", "t_2"], ["t_1", "t_2"]], "exact duplicate")
        rej(["t_1t_2"], "entry not list")
        f = fixture2(combinable=[["t_1", "t_2"], ["t_2", "t_3"], ["t_1", "t_3"]])    # a triangle of pairs is fine
        self.assertEqual(self.api.call("POST", "/_test/reset", f).status, 204)
        self.assertEqual(pair_ids(self.options("r_anker", THU, 1)[T]["available_options"])[-1], ["t_1", "t_3"])
        self.reset()

    def test_L187_pair_identity_is_restaurant_local(self):
        f = fixture2()
        f["restaurants"][1]["combinable"] = [["t_1", "t_9"]]
        f["restaurants"][0]["combinable"] = [["t_1", "t_2"]]
        self.assertEqual(self.api.call("POST", "/_test/reset", f).status, 204)        # same ids elsewhere are fine
        self.reset()


class Moves(Base2):
    def mv(self, moves, key=None, token=None):
        return self.api.call("POST", "/reservation-moves", {"moves": moves}, token=token or self.ada, key=key or self.newkey())

    def test_L105_L177_moves_accept_table_ids(self):
        a = self.ok_book(self.ada, T, table="t_3", party=2)
        r = self.mv([{"reference": a["reference"], "table_ids": ["t_1", "t_2"]}])
        self.assertEqual(r.status, 201, r)
        x = r.json["reservations"][0]
        self.assertEqual(sorted(x["table_ids"]), ["t_1", "t_2"])
        self.assertNotIn("table_id", x)
        self.assertEqual(x["reference"], a["reference"])
        self.assertEqual(self.options("r_anker", THU, 1)[T]["available_table_ids"], ["t_3"])

    def test_L178_swap_single_and_pair_atomic(self):
        a = self.ok_book(self.ada, T, table="t_3", party=2)
        b = self.ok_pair(self.ada, T, ["t_1", "t_2"], 5)
        r = self.mv([{"reference": a["reference"], "table_ids": ["t_1", "t_2"], "party_size": 5},
                     {"reference": b["reference"], "table_ids": ["t_3"], "party_size": 5}])
        self.assertEqual(r.status, 201, r)
        got = r.json["reservations"]
        self.assertEqual([x["reference"] for x in got], [a["reference"], b["reference"]])
        self.assertEqual(sorted(got[0]["table_ids"]), ["t_1", "t_2"])
        self.assertEqual((got[1]["table_id"], got[1]["table_ids"]), ("t_3", ["t_3"]))

    def test_L177_overlap_among_results_or_with_unlisted(self):
        a = self.ok_book(self.ada, T, table="t_3", party=2)
        b = self.ok_book(self.ada, T, table="t_1", party=2)
        c = self.ok_book(self.bob, f"{THU}T21:00", table="t_2", party=2)
        before = self.api.call("GET", "/reservations", token=self.ada).json
        # both results contain t_2
        self.err(self.mv([{"reference": a["reference"], "table_ids": ["t_2", "t_3"], "party_size": 5},
                          {"reference": b["reference"], "table_ids": ["t_1", "t_2"], "party_size": 5}]), 409, "table_unavailable")
        # result overlaps an unlisted booking (bob holds t_2 at 21:00)
        self.err(self.mv([{"reference": a["reference"], "table_ids": ["t_2", "t_3"], "starts_at_local": f"{THU}T21:00",
                           "party_size": 5}]), 409, "table_unavailable")
        # listed but unchanged booking retains its occupancy (b stays on t_1)
        self.err(self.mv([{"reference": a["reference"], "table_ids": ["t_1", "t_2"], "party_size": 5}, {"reference": b["reference"]}]),
                 409, "table_unavailable")
        self.assertEqual(self.api.call("GET", "/reservations", token=self.ada).json, before)

    def test_L178_non_occupancy_errors_precede_occupancy_in_order(self):
        a = self.ok_book(self.ada, T, table="t_3", party=2)
        b = self.ok_book(self.ada, T, table="t_1", party=2)
        self.ok_book(self.bob, f"{THU}T21:00", table="t_2", party=1)
        conflict = {"reference": a["reference"], "table_ids": ["t_2", "t_3"], "starts_at_local": f"{THU}T21:00", "party_size": 5}
        self.err(self.mv([conflict, {"reference": b["reference"], "table_ids": ["t_1", "t_3"]}]), 422, "combination_not_allowed")
        self.err(self.mv([conflict, {"reference": b["reference"], "table_ids": ["t_1", "t_1"]}]), 422, "validation_failed")
        self.err(self.mv([conflict, {"reference": b["reference"], "table_ids": ["t_1", "t_2"], "party_size": 7}]), 422,
                 "party_exceeds_capacity")
        self.err(self.mv([conflict, {"reference": b["reference"], "table_ids": ["t_1", "zz"]}]), 404, "not_found")
        self.err(self.mv([{"reference": a["reference"], "table_ids": ["t_1", "t_3"]},
                          {"reference": b["reference"], "table_ids": ["t_1", "t_1"]}]), 422, "combination_not_allowed")
        self.err(self.mv([{"reference": a["reference"], "table_id": "t_1", "table_ids": ["t_1"]}]), 422, "validation_failed")

    def test_L178_unchanged_pair_permutation_is_noop(self):
        b = self.ok_pair(self.ada, T, ["t_1", "t_2"], 5)
        c = self.ok_book(self.ada, T, table="t_3", party=2)
        r = self.mv([{"reference": b["reference"], "table_ids": ["t_2", "t_1"]}, {"reference": c["reference"]}])
        self.assertEqual(r.status, 201, r)
        self.assertEqual(r.json["reservations"], [b, c])

    def test_L179_L111_pair_batch_receipts(self):
        a = self.ok_book(self.ada, T, table="t_3", party=2)
        moves = [{"reference": a["reference"], "table_ids": ["t_1", "t_2"], "party_size": 5}]
        r1 = self.mv(moves, key="pm-1")
        r2 = self.mv(moves, key="pm-1")
        self.assertEqual((r1.status, r2.status, r1.json), (201, 200, r2.json))
        self.api.call("POST", f"/reservations/{a['reference']}/cancel", token=self.ada)
        r3 = self.mv(moves, key="pm-1")
        self.assertEqual((r3.status, r3.json), (200, r1.json))
        self.err(self.mv([{"reference": a["reference"], "table_ids": ["t_2", "t_1"], "party_size": 5}], key="pm-1"), 409,
                 "idempotency_key_reuse")

    def test_L109_batch_failure_changes_nothing_with_pairs(self):
        a = self.ok_book(self.ada, T, table="t_3", party=2)
        b = self.ok_book(self.ada, T, table="t_1", party=2)
        before = self.api.call("GET", "/reservations", token=self.ada).json
        key = "pm-f"
        self.err(self.mv([{"reference": a["reference"], "table_ids": ["t_2", "t_3"], "party_size": 5},
                          {"reference": b["reference"], "table_ids": ["t_1", "t_2"], "party_size": 5}], key=key), 409,
                 "table_unavailable")
        self.assertEqual(self.api.call("GET", "/reservations", token=self.ada).json, before)
        ok = self.mv([{"reference": a["reference"], "table_ids": ["t_2", "t_3"], "party_size": 5}], key=key)
        self.assertEqual(ok.status, 201, ok)


class Races(Base2):
    def test_L066_L181_exactly_one_winner_among_pairwise_overlapping_sets(self):
        shapes = [["t_1", "t_2"], ["t_2"], ["t_2", "t_3"], ["t_2", "t_1"], ["t_3", "t_2"]]
        outs = self.burst([lambda i=i: self.pair_book(self.ada if i % 2 else self.bob, T, shapes[i % 5], 2, key=f"r-{i}")
                           for i in range(25)])
        self.assertEqual(sorted(o.status for o in outs), [201] + [409] * 24)
        for o in outs:
            if o.status == 409:
                self.err(o, 409, "table_unavailable")

    def test_L181_disjoint_sets_both_succeed(self):
        outs = self.burst([lambda: self.pair_book(self.ada, T, ["t_1", "t_2"], 5, key="d1"),
                           lambda: self.pair_book(self.bob, T, ["t_3"], 5, key="d2")] * 1)
        self.assertEqual([o.status for o in outs], [201, 201])

    def test_L181_races_between_create_and_patch_and_move(self):
        a = self.ok_book(self.ada, f"{THU}T21:00", table="t_3", party=2)
        outs = self.burst([
            lambda: self.pair_book(self.bob, T, ["t_2", "t_3"], 8, key="x1"),
            lambda: self.api.call("PATCH", f"/reservations/{a['reference']}", {"starts_at_local": T, "table_ids": ["t_3"]},
                                  token=self.ada),
            lambda: self.api.call("POST", "/reservation-moves", {"moves": [{"reference": a["reference"], "starts_at_local": T,
                                                                           "table_ids": ["t_2", "t_3"], "party_size": 8}]},
                                  token=self.ada, key="x3")])
        wins = [o for o in outs if o.status in (200, 201)]
        self.assertEqual(len(wins), 1, [o.status for o in outs])        # all three need t_3 at 19:00

    def test_L180_L188_invariant_holds_under_mixed_load_and_reads_stay_consistent(self):
        import random
        rnd = random.Random(7)
        users = [self.ada, self.bob]
        sets = [["t_1"], ["t_2"], ["t_3"], ["t_1", "t_2"], ["t_2", "t_3"]]
        slots = [f"{THU}T{h:02d}:{m:02d}" for h in (18, 19, 20, 21) for m in (0, 30) if (h, m) <= (21, 30)]
        calls = []
        for i in range(60):
            ids = rnd.choice(sets)
            st = rnd.choice(slots)
            calls.append(lambda i=i, ids=ids, st=st: self.pair_book(users[i % 2], st, ids, 1, key=f"m-{i}"))
        reads = []

        def read():
            r = self.api.call("GET", f"/availability?restaurant_id=r_anker&date={THU}&party_size=1")
            reads.append(r)
            return r
        calls += [read] * 30
        calls += [lambda: self.api.call("GET", "/reservations", token=self.ada)] * 10
        outs = self.burst(calls)
        self.assertTrue(all(o.status < 500 for o in outs))
        for r in reads:
            self.assertEqual(r.status, 200)
            for s in r.json["slots"]:
                free = set(s["available_table_ids"])
                self.assertEqual([o["table_ids"] for o in s["available_options"] if len(o["table_ids"]) == 1],
                                 [[x] for x in s["available_table_ids"]])
                for o in s["available_options"]:
                    self.assertTrue(set(o["table_ids"]) <= free, (s, o))     # a pair is offered only if both are free
        allr = []
        for t in users:
            allr += self.api.call("GET", "/reservations", token=t).json["reservations"]
        conf = [r for r in allr if r["status"] == "confirmed"]
        mins = lambda s: int(s[11:13]) * 60 + int(s[14:16])
        for i, a in enumerate(conf):
            for b in conf[i + 1:]:
                if set(a["table_ids"]) & set(b["table_ids"]):
                    self.assertGreaterEqual(abs(mins(a["starts_at_local"]) - mins(b["starts_at_local"])), 90, (a, b))
        self.assertEqual(len({r["reference"] for r in allr}), len(allr))

    def test_L180_export_during_writes_is_importable_and_consistent(self):
        calls = [lambda i=i: self.pair_book(self.ada, f"{THU}T{18 + i % 4}:00", [["t_1", "t_2"], ["t_3"]][i % 2], 1, key=f"e-{i}")
                 for i in range(12)]
        calls += [lambda: self.api.call("GET", "/_test/export")] * 8
        outs = self.burst(calls)
        from s2common import Api, base_url
        for o in outs[12:]:
            self.assertEqual(o.status, 200)
            self.assertEqual(Api(base_url(2)).call("POST", "/_test/import", o.json).status, 204)


class Inherited(Base2):
    def test_L105_L110_noop_item_in_batch_with_legacy_table_id(self):
        a = self.ok_book(self.ada, T, table="t_2", party=2)
        r = self.api.call("POST", "/reservation-moves", {"moves": [{"reference": a["reference"], "table_id": "t_2"}]},
                          token=self.ada, key="lg")
        self.assertEqual((r.status, r.json["reservations"]), (201, [a]))

    def test_L176_single_table_flows_unchanged(self):
        j = self.ok_book(self.ada, T, table="t_2", party=4)
        self.assertEqual((j["table_id"], j["table_ids"]), ("t_2", ["t_2"]))
        self.assertEqual(self.api.call("GET", f"/reservations/{j['reference']}", token=self.ada).json, j)
        cs = self.api.call("POST", f"/reservations/{j['reference']}/cancel", token=self.ada)
        self.assertEqual((cs.status, cs.json["table_id"]), (200, "t_2"))

    def test_L186_identity_invariants_with_pairs(self):
        refs, ids = set(), set()
        for i, st in enumerate((f"{THU}T18:00", f"{THU}T19:30", f"{THU}T21:00")):
            for tids in (["t_1", "t_2"], ["t_3"]):
                j = self.ok_pair(self.ada, st, tids, 1)
                refs.add(j["reference"])
                ids.add(j["reservation_id"])
        self.assertEqual((len(refs), len(ids)), (6, 6))
        import re
        self.assertTrue(all(re.fullmatch(r"[A-Z0-9]{6,12}", r) for r in refs))
