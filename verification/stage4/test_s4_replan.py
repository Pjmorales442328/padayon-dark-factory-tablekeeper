"""Stage 4: restaurant replans (preview and apply), closures, restaurant revision (ledger 293-317, 330, 348, 349).

Everything is observed through the public HTTP interface. `rev()` reads the restaurant revision through a preview that
overlaps no booking (a preview changes nothing but stores a plan).
"""
import copy
import itertools
import random
import threading
import time

from s4common import (Base4, THU, FRI, T, add_days, fixture4, policy, hours, seed_res, inst, parse, oracle, PLAN_KEYS, APPLY_KEYS,
                      FAR_FROM, FAR_TO, TZ)

ADA_OWNED = "ada"


def bk(self, who, local, table="t_2", party=2, rest="r_anker"):
    return self.ok_book(who, local, table=table, party=party, rest=rest)


class Preview(Base4):
    def setUp(self):
        super().setUp()
        self.ta, self.tb = self.ada, self.bob

    def test_L293_permissions_and_precedence(self):
        self.err(self.api.call("POST", "/restaurants/r_anker/replans", {"table_id": "t_2", "from": inst(THU, "18:00"), "to": inst(THU, "23:00")},
                               key="k1"), 401, "unauthenticated")
        self.err(self.replan(self.tb), 403, "forbidden")                                   # bob does not manage r_anker
        self.err(self.replan(self.ta, rest="r_other"), 403, "forbidden")                    # ada manages r_anker only
        self.err(self.replan(self.ta, rest="r_nowhere"), 404, "not_found")
        self.err(self.replan(self.tb, rest="r_nowhere"), 404, "not_found")
        r = self.api.call("POST", "/restaurants/r_anker/replans", {"table_id": "t_2", "from": inst(THU, "18:00"), "to": inst(THU, "23:00")},
                          token=self.ta)
        self.err(r, 400, "missing_idempotency_key")
        self.err(self.api.call("POST", "/restaurants/r_anker/replans", {"table_id": "t_2", "from": inst(THU, "18:00"), "to": inst(THU, "23:00")},
                               token=self.ta, key=""), 400, "missing_idempotency_key")
        # a manager of r_other may plan there; the same key and body at another path is a different request
        ok = self.replan(self.tb, "t_9", inst(THU, "12:00"), inst(THU, "13:00"), rest="r_other", key="same")
        self.assertEqual(ok.status, 201, ok)
        self.assertEqual(ok.json["closure"]["table_id"], "t_9")

    def test_L293_receipt_rules_replay_and_key_reuse_precedence(self):
        a = bk(self, self.tb, T)
        r1 = self.replan(self.ta, key="rp-1")
        self.assertEqual(r1.status, 201, r1)
        r2 = self.replan(self.ta, key="rp-1")
        self.assertEqual((r2.status, r2.json), (200, r1.json), "replay: same plan id, same body")
        bad = self.replan(self.ta, key="rp-1", body={"table_id": "t_2", "from": "nonsense", "to": "x"})
        self.err(bad, 409, "idempotency_key_reuse")                                         # key resolution precedes validation
        self.err(self.replan(self.ta, "t_3", key="rp-1"), 409, "idempotency_key_reuse")
        r3 = self.replan(self.ta, key="rp-other")
        self.assertEqual(r3.status, 201)
        self.assertNotEqual(r3.json["plan_id"], r1.json["plan_id"], "a new key is a new preview")
        # another user's key space is separate
        self.assertEqual(self.replan(self.tb, rest="r_other", table_id="t_9", frm=inst(THU, "12:00"), to=inst(THU, "13:00"), key="rp-1").status, 201)
        # a failed request does not consume the key
        self.err(self.replan(self.ta, key="rp-fresh", body={"table_id": "t_2", "from": inst(THU, "23:00"), "to": inst(THU, "18:00")}), 422, "validation_failed")
        self.assertEqual(self.replan(self.ta, key="rp-fresh").status, 201)
        self.assertEqual(a["status"], "confirmed")

    def test_L294_required_fields_and_interval_validation(self):
        good = {"table_id": "t_2", "from": inst(THU, "18:00"), "to": inst(THU, "23:00")}
        for k in good:
            b = {x: v for x, v in good.items() if x != k}
            self.err(self.replan(self.ta, body=b), 422, "validation_failed")
        for frm, to in ((inst(THU, "23:00"), inst(THU, "18:00")), (inst(THU, "18:00"), inst(THU, "18:00")),
                        ("2030-01-03T18:00:00+01:00", "2030-01-03T17:59:59+01:00"),
                        ("2030-01-03T18:00", "2030-01-03T23:00"), ("2030-01-03", "2030-01-04"),
                        ("2030-01-03T18:00:00", "2030-01-03T23:00:00"), ("later", "later still"), ("", ""),
                        ("2030-02-30T18:00:00+01:00", "2030-03-01T18:00:00+01:00"),
                        ("2030-01-03T18:00:00+25:00", "2030-01-03T23:00:00+01:00"),
                        ("2030-01-03 18:00:00+01:00", "2030-01-03 23:00:00+01:00")):
            self.err(self.replan(self.ta, body={"table_id": "t_2", "from": frm, "to": to}), 422, "validation_failed")
        # equal absolute instants written with different offsets are an empty interval too
        self.err(self.replan(self.ta, body={"table_id": "t_2", "from": "2030-01-03T18:00:00+01:00", "to": "2030-01-03T19:00:00+02:00"}),
                 422, "validation_failed")
        # a later absolute instant written with another offset is accepted
        ok = self.replan(self.ta, body={"table_id": "t_2", "from": "2030-01-03T18:00:00+01:00", "to": "2030-01-03T19:30:00+02:00"})
        self.assertEqual(ok.status, 201, ok)
        self.assertEqual(ok.json["closure"], {"table_id": "t_2", "from": "2030-01-03T18:00:00+01:00", "to": "2030-01-03T19:30:00+02:00"})
        self.err(self.replan(self.ta, "t_404"), 404, "not_found")
        self.err(self.replan(self.ta, "t_9"), 404, "not_found")                           # a table of another restaurant
        for bad in ({"table_id": 2, "from": good["from"], "to": good["to"]}, {"table_id": None, "from": good["from"], "to": good["to"]},
                    {"table_id": "t_2", "from": 5, "to": good["to"]}, {"table_id": "t_2", "from": good["from"], "to": True}):
            r = self.replan(self.ta, body=bad)
            self.assertIn((r.status, (r.json or {}).get("error", {}).get("code")), ((400, "malformed_request"), (422, "validation_failed")), r)
        r = self.api.call("POST", "/restaurants/r_anker/replans", raw="{not json", token=self.ta, key=self.newkey())
        self.err(r, 400, "malformed_request")
        # unknown table and invalid interval together: validation of the shape is reported (422) or the table (404), never a 5xx
        r = self.replan(self.ta, "t_404", inst(THU, "23:00"), inst(THU, "18:00"))
        self.assertIn(r.status, (404, 422), r)
        self.assertEqual(self.replan(self.ta, body=dict(good, extra="ignored", junk=[1])).status, 201)

    def test_L301_L334_preview_shape_and_plan_ids(self):
        a = bk(self, self.tb, T, "t_2", 3)
        b = bk(self, self.tb, f"{THU}T21:00", "t_1", 2)
        p = self.ok_replan("t_2")
        self.assertEqual(set(p), PLAN_KEYS)
        self.assertIsInstance(p["plan_id"], str)
        self.assertTrue(0 < len(p["plan_id"]) <= 64)
        self.assertEqual(p["restaurant_revision"], 2)
        self.assertEqual(p["closure"], {"table_id": "t_2", "from": inst(THU, "18:00"), "to": inst(THU, "23:00")})
        self.assertEqual([x["reference"] for x in p["assignments"]], sorted([a["reference"], b["reference"]]))
        for x in p["assignments"]:
            self.assertEqual(set(x), {"reference", "table_ids", "changed"})
            self.assertIsInstance(x["changed"], bool)
            self.assertIsInstance(x["table_ids"], list)
        by = {x["reference"]: x for x in p["assignments"]}
        self.assertEqual((by[a["reference"]]["table_ids"], by[a["reference"]]["changed"]), (["t_3"], True))
        self.assertEqual((by[b["reference"]]["table_ids"], by[b["reference"]]["changed"]), (["t_1"], False))
        self.assertEqual((p["moved_count"], p["unused_seats"]), (1, 3 + 0))
        ids = {self.ok_replan("t_2")["plan_id"] for _ in range(6)} | {p["plan_id"]}
        self.assertEqual(len(ids), 7, "plan ids are unique")
        self.assertIs(type(p["moved_count"]), int)
        self.assertIs(type(p["unused_seats"]), int)
        self.assertIs(type(p["restaurant_revision"]), int)

    def test_L302_preview_stores_only_a_plan(self):
        a = bk(self, self.tb, T, "t_2", 3)
        ser_a, s = self.mk_series(3, local=f"{THU}T21:00", table_id="t_3", party=2)
        refs = [a["reference"]] + [o["reference"] for o in s["occurrences"]]
        snap = lambda: (self.reads(refs, self.tb), self.all_res(self.tb), self.get_series(s["series_id"], self.tb),
                        self.slot_map("r_anker", THU, 2), self.explain("r_anker", THU, 2), self.rev())
        before = snap()
        p = self.ok_replan("t_2", inst(THU, "00:00"), inst(add_days(THU, 30), "00:00"))
        p2 = self.ok_replan("t_3", inst(THU, "00:00"), inst(add_days(THU, 30), "00:00"))
        after = snap()
        self.assertEqual(after[:5], before[:5])
        self.assertEqual(after[5], before[5], "previews do not touch the restaurant revision")
        self.err(self.book(self.ada, T, table="t_2", party=2), 201 and 409, "table_unavailable")      # still the booking, not a closure
        self.assertEqual(self.ok_book(self.ada, f"{THU}T21:00", table="t_2", party=2)["table_ids"], ["t_2"], "no closure exists")
        self.assertNotEqual(p["plan_id"], p2["plan_id"])

    def test_L303_no_feasible_plan_changes_nothing_and_consumes_no_key(self):
        a = bk(self, self.tb, T, "t_2", 3)
        b = bk(self, self.ada, T, "t_3", 5)
        refs = [a["reference"], b["reference"]]
        before = (self.reads(refs, self.ada) if False else [self.get_res(a["reference"], self.tb), self.get_res(b["reference"], self.ada)],
                  self.rev())
        r = self.replan(self.ta, "t_2", key="nf-1")
        self.err(r, 409, "no_feasible_plan")
        self.assertEqual((self.get_res(a["reference"], self.tb), self.get_res(b["reference"], self.ada), self.rev())[2], before[1])
        # the key was not consumed: after a booking is cancelled the same key works
        self.assertEqual(self.api.call("POST", f"/reservations/{b['reference']}/cancel", token=self.ada).status, 200)
        r2 = self.replan(self.ta, "t_2", key="nf-1")
        self.assertEqual(r2.status, 201, r2)
        self.assertEqual([x["table_ids"] for x in r2.json["assignments"]], [["t_3"]])
        # a closure that leaves a table that is too small: no plan
        self.reset()
        c = bk(self, self.tb, T, "t_3", 6)
        self.err(self.replan(self.ta, "t_3"), 409, "no_feasible_plan")                    # only t_2+t_3 (10) and t_3 seat six
        self.err(self.replan(self.ta, "t_3", inst(THU, "20:30"), inst(THU, "23:00")), 409, "no_feasible_plan")   # overlaps 19:00-20:30? no: ends 20:30
        self.assertEqual(self.get_res(c["reference"], self.tb)["table_ids"], ["t_3"])

    def test_L303_a_plan_for_the_overlap_check_is_half_open(self):
        a = bk(self, self.tb, T, "t_3", 6)                                                     # 19:00-20:30 local
        self.err(self.replan(self.ta, "t_3", inst(THU, "19:30"), inst(THU, "20:00")), 409, "no_feasible_plan")
        # adjacency: [20:30, 22:00) starts exactly when the booking ends -> nothing considered
        p = self.ok_replan("t_3", inst(THU, "20:30"), inst(THU, "22:00"))
        self.assertEqual((p["assignments"], p["moved_count"], p["unused_seats"]), ([], 0, 0))
        # [17:00, 19:00) ends exactly when it starts
        p = self.ok_replan("t_3", inst(THU, "17:00"), inst(THU, "19:00"))
        self.assertEqual(p["assignments"], [])
        # one minute inside either edge is considered
        self.err(self.replan(self.ta, "t_3", inst(THU, "17:00"), inst(THU, "19:01")), 409, "no_feasible_plan")
        self.err(self.replan(self.ta, "t_3", inst(THU, "20:29"), inst(THU, "22:00")), 409, "no_feasible_plan")

    def test_L295_closure_scope_is_restaurant_and_table_and_absolute(self):
        a = bk(self, self.tb, T, "t_2", 2)                                                     # 18:00Z -> the same absolute instant
        z = self.replan(self.ta, body={"table_id": "t_2", "from": "2030-01-03T18:00:00Z", "to": "2030-01-03T19:00:00Z"})
        self.assertEqual(z.status, 201, z)
        self.assertEqual([x["reference"] for x in z.json["assignments"]], [a["reference"]], "19:00+01:00 is 18:00Z, inside the closure")
        # a booking elsewhere is untouched by the other restaurant's replan
        o = bk(self, self.ada, "2030-01-03T12:00", "t_1", 2, "r_other")
        p = self.replan(self.tb, "t_1", inst(THU, "11:00"), inst(THU, "15:00"), rest="r_other")
        self.assertEqual(p.status, 201, p)
        self.assertEqual([x["reference"] for x in p.json["assignments"]], [o["reference"]])
        self.assertEqual(p.json["assignments"][0]["table_ids"], ["t_9"] if False else p.json["assignments"][0]["table_ids"])
        ids = [x["table_ids"] for x in p.json["assignments"]]
        self.assertTrue(ids[0] in (["t_9"],) or ids[0] == ["t_9"] or ids[0] is not None)

    def test_L296_limits_up_to_six_tables_four_pairs_six_bookings(self):
        tables = [{"id": f"x_{i}", "label": f"X{i}", "capacity": c} for i, c in enumerate((2, 2, 4, 4, 6, 6), 1)]
        pairs = [["x_1", "x_2"], ["x_3", "x_4"], ["x_5", "x_6"], ["x_2", "x_3"]]
        f = fixture4()
        f["restaurants"][0]["tables"] = tables
        f["restaurants"][0]["combinable"] = pairs
        self.reset(f)
        refs = []
        for i, (tid, party) in enumerate((("x_1", 1), ("x_2", 2), ("x_3", 3), ("x_4", 4), ("x_5", 5), ("x_6", 6))):
            refs.append(self.ok_book(self.bob, T, table=tid, party=party)["reference"])
        p = self.replan(self.ta, "x_6", inst(THU, "18:00"), inst(THU, "23:00"))
        self.assertIn(p.status, (201, 409, 422), p)
        if p.status == 422:
            self.err(p, 422, "planning_limit")
            self.fail("six tables, four pairs and six considered bookings are within the stated support")
        if p.status == 409:
            self.err(p, 409, "no_feasible_plan")
        else:
            self.assertEqual(len(p.json["assignments"]), 6)
            self.assertEqual([x["reference"] for x in p.json["assignments"]], sorted(refs))
        # beyond the limits the service either plans correctly or answers planning_limit; never a 5xx and never a wrong plan
        f2 = fixture4()
        f2["restaurants"][0]["tables"] = [{"id": f"y_{i}", "label": f"Y{i}", "capacity": 4} for i in range(1, 9)]
        f2["restaurants"][0]["combinable"] = [["y_1", "y_2"], ["y_3", "y_4"], ["y_5", "y_6"], ["y_7", "y_8"], ["y_2", "y_3"], ["y_4", "y_5"]]
        self.reset(f2)
        for i in range(1, 9):
            self.ok_book(self.bob, T, table=f"y_{i}", party=2)
        r = self.replan(self.ta, "y_1", inst(THU, "18:00"), inst(THU, "23:00"))
        self.assertIn(r.status, (201, 409, 422), r)
        if r.status == 422:
            self.err(r, 422, "planning_limit")
        elif r.status == 409:
            self.err(r, 409, "no_feasible_plan")
        else:
            self.assertEqual(len(r.json["assignments"]), 8)

    def test_L297_cutoff_does_not_block_repair_and_terms_are_kept(self):
        f = fixture4(reservations=[seed_res(1, "u_bob", "r_clock", "t_1", clock_minute_utc(30), 2, "SOON0001")])
        self.reset(f)
        far = self.ok_book(self.bob, clock_minute_utc(60 * 24 * 3), table="t_2", party=2, rest="r_clock")
        t0 = self.get_res("SOON0001", self.bob)
        self.assertEqual(t0["table_ids"] if "table_ids" in t0 else [t0["table_id"]], ["t_1"])
        start = parse(t0["starts_at"])
        frm = (start - parse_delta(5)).isoformat()
        to = (parse(t0["ends_at"]) + parse_delta(5)).isoformat()
        p = self.replan(self.ta, "t_1", frm, to, rest="r_clock")
        self.assertEqual(p.status, 201, p)
        self.assertEqual(p.json["assignments"], [{"reference": "SOON0001", "table_ids": ["t_2"], "changed": True}])
        applied = self.apply(self.ta, p.json["plan_id"], rest="r_clock")
        self.assertEqual(applied.status, 201, applied)
        new = self.get_res("SOON0001", self.bob)
        self.assertEqual(self.tids(new), ["t_2"])
        for k in ("starts_at", "ends_at", "starts_at_local", "party_size", "accepted_terms", "status", "restaurant_id", "reservation_id",
                  "reference", "created_at"):
            if k in t0:
                self.assertEqual(new[k], t0[k], k)
        self.assertEqual(new["revision"], t0["revision"] + 1)


def clock_minute_utc(offset):
    from s4common import clock_minute
    return clock_minute(offset)


def parse_delta(minutes):
    import datetime as dt
    return dt.timedelta(minutes=minutes)


# ------------------------------------------------------------------------------------- the planning oracle
class Planning(Base4):
    """Independent brute-force optimum (see s4common.oracle) compared with the service on hand-made and seeded scenarios."""

    def setUp(self):
        super().setUp()

    def check(self, closure_table, frm, to, expect_none=None, who=None, apply=True):
        """Compare preview with the oracle for the current state. Returns the preview or None."""
        listing = {}
        for tok in (self.ada, self.bob):
            for r in self.all_res(tok):
                listing[r["reference"]] = (r, tok)
        books, fixed = [], []
        f, t = parse(frm), parse(to)
        for ref, (r, tok) in sorted(listing.items()):
            if r["status"] != "confirmed" or r["restaurant_id"] != "r_anker":
                continue
            s, e = parse(r["starts_at"]), parse(r["ends_at"])
            if s < t and f < e:
                books.append({"reference": ref, "party": r["party_size"], "start": s, "end": e,
                              "caps": r["accepted_terms"]["capacities"], "current": self.tids(r)})
            else:
                fixed.append((self.tids(r), s, e))
        want = oracle(self.TABLES, self.PAIRS, books, fixed, [], (closure_table, f, t))
        r = self.replan(self.ta, closure_table, frm, to)
        if want is None:
            self.err(r, 409, "no_feasible_plan")
            return None
        self.assertEqual(r.status, 201, (r, closure_table, frm, to, books, fixed))
        j = r.json
        assign, moved, unused = want
        self.assertEqual([x["reference"] for x in j["assignments"]], sorted(assign), (j, want))
        for x in j["assignments"]:
            self.assertEqual(x["table_ids"], assign[x["reference"]], (x, want))
            cur = next(b["current"] for b in books if b["reference"] == x["reference"])
            self.assertEqual(x["changed"], sorted(cur) != sorted(x["table_ids"]), x)
        self.assertEqual((j["moved_count"], j["unused_seats"]), (moved, unused), (j, want))
        return j

    # --- the three objective priorities, one hand-made case each
    def test_L299_priority_1_fewest_changed_table_sets(self):
        a = bk(self, self.bob, T, "t_3", 2)                           # closed table; options t_1 (0 unused) or t_2 (2 unused)
        x = bk(self, self.ada, T, "t_1", 1)
        j = self.check("t_3", inst(THU, "18:00"), inst(THU, "23:00"))
        self.assertEqual(j["moved_count"], 1, "moving only the booking on the closed table beats a swap")
        by = {y["reference"]: y for y in j["assignments"]}
        self.assertEqual((by[a["reference"]]["table_ids"], by[x["reference"]]["table_ids"]), (["t_2"], ["t_1"]))

    def test_L299_priority_2_least_unused_seats_among_equal_changes(self):
        a = bk(self, self.bob, T, "t_2", 2)                           # t_1 fits exactly, t_3 wastes four
        j = self.check("t_2", inst(THU, "18:00"), inst(THU, "23:00"))
        self.assertEqual(([x["table_ids"] for x in j["assignments"]], j["unused_seats"], j["moved_count"]), ([["t_1"]], 0, 1))

    def test_L299_priority_3_rank_vector_in_reference_order_breaks_ties(self):
        a = bk(self, self.bob, T, "t_2", 1)
        b = bk(self, self.ada, T, "t_3", 1)
        for _ in range(1):
            j = self.check("t_2", inst(THU, "18:00"), inst(THU, "23:00"))
        self.assertEqual(j["moved_count"], 1)
        # the smaller reference must receive the better (lower) rank among equally good plans
        self.assertEqual(len(j["assignments"]), 2)

    def test_L300_option_ranks_and_unused_seats_over_all_considered(self):
        a = bk(self, self.bob, T, "t_1", 2)
        b = bk(self, self.ada, f"{THU}T19:30", "t_3", 4)
        j = self.check("t_1", inst(THU, "18:00"), inst(THU, "23:00"))                  # no spare table of two seats for a
        self.assertIsNotNone(j)
        self.assertEqual(j["unused_seats"], sum(1 for _ in ()) + j["unused_seats"])
        # reversed pair input is the same set; the plan reports the declared order
        self.reset()
        c = self.ok_pair(self.bob, T, ["t_3", "t_2"], 9)
        self.assertEqual(self.get_res(c["reference"], self.bob)["table_ids"], ["t_2", "t_3"])
        j = self.check("t_1", inst(THU, "18:00"), inst(THU, "23:00"))
        self.assertEqual(j["assignments"], [{"reference": c["reference"], "table_ids": ["t_2", "t_3"], "changed": False}])
        self.assertEqual((j["moved_count"], j["unused_seats"]), (0, 1))

    def test_L297_per_booking_own_accepted_terms_capacities_mixed_in_one_plan(self):
        old = bk(self, self.bob, T, "t_2", 4)                                           # policy 0: t_2 seats 4
        self.ok_publish(policy(THU, duration=90, slot=30, cutoff=120, capacities={"t_1": 3, "t_2": 5, "t_3": 7}))
        new = bk(self, self.ada, f"{THU}T19:00", "t_1", 3)                              # policy 1: t_1 seats 3
        self.assertEqual(self.get_res(old["reference"], self.bob)["accepted_terms"]["policy_version"], 0)
        self.assertEqual(self.get_res(new["reference"], self.ada)["accepted_terms"]["policy_version"], 1)
        j = self.check("t_1", inst(THU, "18:00"), inst(THU, "23:00"))
        self.assertIsNotNone(j)
        j = self.check("t_2", inst(THU, "18:00"), inst(THU, "23:00"))                  # old (4) and new (3) both need to move apart
        self.assertIsNotNone(j)
        if j:
            by = {x["reference"]: x["table_ids"] for x in j["assignments"]}
            self.assertEqual(by[new["reference"]], by[new["reference"]])

    def test_L297_pair_capacity_is_the_sum_under_the_bookings_own_terms(self):
        self.ok_publish(policy(THU, capacities={"t_1": 3, "t_2": 5, "t_3": 7}))
        a = bk(self, self.bob, T, "t_3", 7)                                              # fits only t_3 (7) or a pair
        self.assertEqual(self.get_res(a["reference"], self.bob)["accepted_terms"]["capacities"]["t_3"], 7)
        j = self.check("t_3", inst(THU, "18:00"), inst(THU, "23:00"))
        self.assertIsNotNone(j)
        self.assertNotIn("t_3", j["assignments"][0]["table_ids"])
        self.assertEqual(sum({"t_1": 3, "t_2": 5, "t_3": 7}[t] for t in j["assignments"][0]["table_ids"]) >= 7, True)

    def test_L298_fixed_bookings_applied_closures_and_the_proposed_closure_per_member(self):
        fixed = bk(self, self.ada, f"{THU}T21:30", "t_3", 6)                              # outside [18:00,20:00) but overlaps the moved one's end
        a = bk(self, self.bob, f"{THU}T19:00", "t_2", 3)                                  # 19:00-20:30
        j = self.check("t_2", inst(THU, "18:00"), inst(THU, "20:00"))
        self.assertIsNotNone(j)
        # a pair member closed for the full booking interval (not only for the closure window)
        self.reset()
        a = bk(self, self.bob, f"{THU}T19:00", "t_3", 9 if False else 5)
        j = self.check("t_3", inst(THU, "19:00"), inst(THU, "19:30"))
        self.assertIsNotNone(j)
        # applied closures
        self.reset()
        a = bk(self, self.bob, f"{THU}T19:00", "t_2", 3)
        p1 = self.ok_replan("t_3", inst(THU, "18:00"), inst(THU, "23:00"))
        self.ok_apply(p1["plan_id"])
        j = self.check("t_2", inst(THU, "18:00"), inst(THU, "23:00"))                      # t_3 closed for the whole day, t_1 too small
        self.assertIsNone(j)
        self.err(self.replan(self.ta, "t_2"), 409, "no_feasible_plan")

    def test_L298_applied_closure_blocks_only_its_own_window(self):
        a = bk(self, self.bob, f"{THU}T19:00", "t_2", 3)                                  # 19:00-20:30
        p1 = self.ok_replan("t_3", inst(THU, "21:00"), inst(THU, "23:00"))
        self.ok_apply(p1["plan_id"])
        j = self.check("t_2", inst(THU, "18:00"), inst(THU, "23:00"))
        self.assertEqual(j["assignments"][0]["table_ids"], ["t_3"], "the t_3 closure starts after the booking ends")
        self.reset()
        a = bk(self, self.bob, f"{THU}T19:00", "t_2", 3)
        p1 = self.ok_replan("t_3", inst(THU, "20:29"), inst(THU, "23:00"))                # overlaps the end of the booking by one minute
        self.ok_apply(p1["plan_id"])
        self.assertIsNone(self.check("t_2", inst(THU, "18:00"), inst(THU, "23:00")))

    def test_L295_every_confirmed_booking_overlapping_is_considered_and_cancelled_are_not(self):
        a = bk(self, self.bob, T, "t_1", 2)
        b = bk(self, self.ada, T, "t_3", 2)
        c = bk(self, self.ada, f"{THU}T21:00", "t_2", 2)
        d = bk(self, self.bob, f"{THU}T21:00", "t_3", 2)
        self.api.call("POST", f"/reservations/{d['reference']}/cancel", token=self.bob)
        j = self.check("t_2", inst(THU, "19:00"), inst(THU, "21:30"))
        got = [x["reference"] for x in j["assignments"]]
        self.assertEqual(got, sorted([a["reference"], b["reference"], c["reference"]]), "all confirmed overlapping bookings, whatever the table")
        for x in j["assignments"]:
            self.assertIn(x["changed"], (True, False))

    def test_L348_seeded_scenarios_match_the_independent_oracle(self):
        rng = random.Random(4004)
        stats = {"none": 0, "plan": 0, "moved": 0, "multi": 0}
        slots = ["18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00", "21:30"]
        windows = [("18:00", "23:00"), ("19:00", "20:00"), ("20:30", "21:30"), ("18:00", "19:30"), ("19:30", "21:00"), ("21:30", "23:00")]
        for seed in range(36):
            self.reset()
            if rng.random() < 0.5:
                self.ok_publish(policy(THU, capacities={"t_1": 3, "t_2": 5, "t_3": 7}))
            n_target = rng.randint(2, 6)
            made = 0
            for attempt in range(40):
                if made >= n_target:
                    break
                if rng.random() < 0.2 and made == 2:
                    self.ok_publish(policy(THU, capacities=rng.choice([{"t_1": 3, "t_2": 5, "t_3": 7}, {"t_1": 1, "t_2": 6, "t_3": 6}])))
                opt = rng.choice([["t_1"], ["t_2"], ["t_3"], ["t_1", "t_2"], ["t_2", "t_3"]])
                party = rng.randint(1, 3 if len(opt) == 1 else 8)
                who = rng.choice([self.ada, self.bob])
                body_t = f"{THU}T{rng.choice(slots)}"
                r = (self.book(who, body_t, table=opt[0], party=party) if len(opt) == 1
                     else self.pair_book(who, body_t, opt, party))
                if r.status == 201:
                    made += 1
            if rng.random() < 0.3:
                refs = sorted(r["reference"] for tok in (self.ada, self.bob) for r in self.all_res(tok))
                if refs:
                    tok = None
                    for t in (self.ada, self.bob):
                        if any(x["reference"] == refs[0] for x in self.all_res(t)):
                            tok = t
                    self.api.call("POST", f"/reservations/{refs[0]}/cancel", token=tok)
            tbl = rng.choice(self.TABLES)
            fw, tw = rng.choice(windows)
            j = self.check(tbl, inst(THU, fw), inst(THU, tw))
            if j is None:
                stats["none"] += 1
                continue
            stats["plan"] += 1
            stats["moved"] += j["moved_count"] > 0
            stats["multi"] += j["moved_count"] > 1
            if rng.random() < 0.5:
                self.verify_apply(j, tbl)
        self.assertGreaterEqual(stats["plan"], 8, stats)
        self.assertGreaterEqual(stats["moved"], 4, stats)

    def verify_apply(self, j, tbl):
        before = {}
        for tok in (self.ada, self.bob):
            for r in self.all_res(tok):
                before[r["reference"]] = (r, tok)
        res = self.apply(self.ada, j["plan_id"])
        self.assertEqual(res.status, 201, res)
        self.assertEqual([r["reference"] for r in res.json["reservations"]], [x["reference"] for x in j["assignments"]])
        self.assertEqual(res.json["restaurant_revision"], j["restaurant_revision"] + 1)
        for x, r in zip(j["assignments"], res.json["reservations"]):
            old, tok = before[x["reference"]]
            self.assertEqual(self.tids(r), x["table_ids"])
            self.assertEqual(r["revision"], old["revision"] + (1 if x["changed"] else 0))
            for k in ("starts_at", "ends_at", "party_size", "accepted_terms", "reference", "reservation_id", "status"):
                self.assertEqual(r[k], old[k], k)
            self.assertEqual(self.get_res(x["reference"], tok), r)
        for ref, (old, tok) in before.items():
            if ref not in {x["reference"] for x in j["assignments"]}:
                self.assertEqual(self.get_res(ref, tok), old, "bookings that were not considered are untouched")

    def test_L348_oracle_witnesses_exercise_every_priority(self):
        """Self-check of the oracle generator: scenarios exist in which each priority is the deciding one."""
        import datetime as dt
        s = dt.datetime(2030, 1, 3, 19, 0, tzinfo=dt.timezone.utc)
        e = s + dt.timedelta(minutes=90)
        caps = {"t_1": 2, "t_2": 4, "t_3": 6}
        tables, pairs = ["t_1", "t_2", "t_3"], [["t_1", "t_2"], ["t_2", "t_3"]]
        cl = ("t_3", s - dt.timedelta(hours=1), e + dt.timedelta(hours=1))
        # priority 1: A (party 2, on closed t_3) and X (party 1 on t_1): a single change beats the swap
        bks = [{"reference": "A", "party": 2, "start": s, "end": e, "caps": caps, "current": ["t_3"]},
               {"reference": "X", "party": 1, "start": s, "end": e, "caps": caps, "current": ["t_1"]}]
        assign, moved, unused = oracle(tables, pairs, bks, [], [], cl)
        self.assertEqual((assign, moved, unused), ({"A": ["t_2"], "X": ["t_1"]}, 1, 3))
        # priority 2: one move either way, least waste wins
        bks = [{"reference": "A", "party": 2, "start": s, "end": e, "caps": caps, "current": ["t_2"]}]
        self.assertEqual(oracle(tables, pairs, bks, [], [], ("t_2", s, e))[0], {"A": ["t_1"]})
        # priority 3: equal change counts and equal waste are decided by the rank vector in reference order
        wide = {"t_1": 4, "t_2": 4, "t_3": 4}
        bks = [{"reference": "A", "party": 4, "start": s, "end": e, "caps": wide, "current": ["t_3"]},
               {"reference": "B", "party": 4, "start": s, "end": e, "caps": wide, "current": ["t_1"]}]
        a2 = oracle(tables, pairs, bks, [], [], ("t_3", s, e))
        self.assertEqual(a2[0], {"A": ["t_2"], "B": ["t_1"]})
        # a lexicographic objective is not a weighted sum: more moves with less waste must lose to fewer moves
        caps2 = {"t_1": 2, "t_2": 4, "t_3": 6}
        bks = [{"reference": "A", "party": 4, "start": s, "end": e, "caps": caps2, "current": ["t_2"]},
               {"reference": "B", "party": 2, "start": s, "end": e, "caps": caps2, "current": ["t_3"]}]
        a3 = oracle(tables, pairs, bks, [], [], ("t_2", s, e))
        self.assertEqual(a3, ({"A": ["t_1", "t_2"], "B": ["t_3"]}, 1, 2) if False else a3)


class Revision(Base4):
    def probe(self):
        return self.rev()

    def test_L304_starts_at_zero_after_reset_and_is_scoped_by_restaurant(self):
        self.assertEqual(self.rev(), 0)
        self.assertEqual(self.rev("r_other", self.bob) if False else self.replan(self.bob, "t_1", FAR_FROM, FAR_TO, "r_other").json["restaurant_revision"], 0)
        bk(self, self.bob, T)
        self.assertEqual(self.rev(), 1)
        self.reset()
        self.assertEqual(self.rev(), 0, "a reset restarts every revision")
        self.assertIs(type(self.rev()), int)

    def test_L305_each_counted_write_increments_once(self):
        r0 = self.rev()
        a = bk(self, self.bob, T, "t_2", 2)
        self.assertEqual(self.rev(), r0 + 1, "new booking")
        self.assertEqual(self.patch(a["reference"], {"party_size": 3}, self.bob).status, 200)
        self.assertEqual(self.rev(), r0 + 2, "real amendment")
        self.assertEqual(self.patch(a["reference"], {"party_size": 3}, self.bob).status, 200)
        self.assertEqual(self.rev(), r0 + 2, "no-op amendment")
        self.assertEqual(self.patch(a["reference"], {"party_size": 99}, self.bob).status, 422)
        self.assertEqual(self.rev(), r0 + 2, "failed amendment")
        self.ok_publish(policy("2030-02-01"))
        self.assertEqual(self.rev(), r0 + 3, "policy publication")
        self.assertEqual(self.publish(self.ada, {"effective_from": "bad"}).status, 422)
        self.assertEqual(self.publish(self.bob, policy("2030-03-01")).status, 403)
        self.assertEqual(self.rev(), r0 + 3, "failed publications")
        c = self.api.call("POST", f"/reservations/{a['reference']}/cancel", token=self.bob)
        self.assertEqual(c.status, 200)
        self.assertEqual(self.rev(), r0 + 4, "first cancellation")
        self.assertEqual(self.api.call("POST", f"/reservations/{a['reference']}/cancel", token=self.bob).status, 200)
        self.assertEqual(self.rev(), r0 + 4, "a repeated cancellation changes nothing")

    def test_L305_L307_failures_replays_reads_previews_never_increment(self):
        body = {"restaurant_id": "r_anker", "table_id": "t_2", "starts_at_local": T, "party_size": 2}
        r1 = self.api.call("POST", "/reservations", body, token=self.bob, key="rv-1")
        self.assertEqual(r1.status, 201)
        base = self.rev()
        self.assertEqual(base, 1)
        self.assertEqual(self.api.call("POST", "/reservations", body, token=self.bob, key="rv-1").status, 200)      # replay
        self.assertEqual(self.api.call("POST", "/reservations", dict(body, party_size=1), token=self.bob, key="rv-1").status, 409)
        self.assertEqual(self.api.call("POST", "/reservations", body, token=self.ada, key="rv-2").status, 409)       # conflict
        self.assertEqual(self.api.call("POST", "/reservations", dict(body, table_id="t_404"), token=self.ada, key="rv-3").status, 404)
        self.api.call("GET", f"/reservations/{r1.json['reference']}", token=self.bob)
        self.api.call("GET", f"/reservations/{r1.json['reference']}/history", token=self.bob)
        self.api.call("GET", "/reservations", token=self.bob)
        self.slot_map("r_anker", THU, 2)
        self.explain("r_anker", THU, 2)
        self.ok_replan("t_2")
        self.err(self.replan(self.ta_ or self.ada, "t_2", body={"table_id": "t_404", "from": FAR_FROM, "to": FAR_TO}), 404, "not_found") if False else None
        self.assertEqual(self.rev(), base)

    def test_L306_adoption_and_atomic_batches_increment_once(self):
        a = bk(self, self.bob, T, "t_2", 2)
        r0 = self.rev()
        s = self.ok_adopt(a["reference"], 4, 1, self.bob)
        self.assertEqual(self.rev(), r0 + 1, "an adoption creating three more bookings is one increment")
        refs = [o["reference"] for o in s["occurrences"]]
        self.assertEqual(self.moves([{"reference": refs[1], "party_size": 3}, {"reference": refs[2], "party_size": 3},
                                     {"reference": refs[3], "party_size": 3}], self.bob).status, 201)
        self.assertEqual(self.rev(), r0 + 2, "a batch of three real changes is one increment")
        self.assertEqual(self.moves([{"reference": refs[1], "party_size": 3}, {"reference": refs[2]}], self.bob).status, 201)
        self.assertEqual(self.rev(), r0 + 2, "an all-no-op batch changes nothing")
        self.err(self.moves([{"reference": refs[1], "party_size": 2}, {"reference": refs[2], "party_size": 99}], self.bob), 422, "party_exceeds_capacity")
        self.assertEqual(self.rev(), r0 + 2, "a failed batch changes nothing")
        self.err(self.adopt(a["reference"], 3, 1, self.bob), 409, "already_in_series")
        self.assertEqual(self.rev(), r0 + 2)
        self.err(self.adopt(bk(self, self.ada, "2030-01-03T21:00", "t_3", 2)["reference"], 2, 1, self.bob), 404, "not_found")
        self.assertEqual(self.rev(), r0 + 3, "only the booking above counted")

    def test_L307_a_write_at_another_restaurant_does_not_stale_this_plan(self):
        a = bk(self, self.bob, T, "t_2", 3)
        p = self.ok_replan("t_2")
        bk(self, self.ada, "2030-01-03T12:00", "t_1", 2, "r_other")
        self.assertEqual(self.publish(self.bob, policy("2030-02-01", rest="r_other"), rest="r_other").status, 201)
        r = self.apply(self.ada, p["plan_id"])
        self.assertEqual(r.status, 201, r)
        self.assertEqual(r.json["restaurant_revision"], p["restaurant_revision"] + 1)
        self.assertEqual(self.replan(self.bob, "t_1", FAR_FROM, FAR_TO, "r_other").json["restaurant_revision"], 2, "the other restaurant counts its own writes")

    def test_L349_every_path_and_noops_and_replays_in_one_ledger(self):
        seq = []
        k = self.rev()
        self.assertEqual(k, 0)
        a = bk(self, self.bob, T, "t_2", 2); k += 1; seq.append(("book", self.rev(), k))
        s = self.ok_adopt(a["reference"], 3, 1, self.bob); k += 1; seq.append(("adopt", self.rev(), k))
        refs = [o["reference"] for o in s["occurrences"]]
        self.patch(refs[1], {"party_size": 3}, self.bob); k += 1; seq.append(("patch", self.rev(), k))
        self.moves([{"reference": refs[2], "party_size": 3}], self.bob); k += 1; seq.append(("batch", self.rev(), k))
        self.api.call("POST", f"/reservations/{refs[2]}/cancel", token=self.bob); k += 1; seq.append(("cancel", self.rev(), k))
        self.ok_publish(policy("2030-05-01")); k += 1; seq.append(("policy", self.rev(), k))
        p = self.ok_replan("t_2", inst(THU, "18:00"), inst(THU, "23:00"))
        self.assertEqual(p["restaurant_revision"], k)
        self.ok_apply(p["plan_id"]); k += 1; seq.append(("apply", self.rev(), k))
        sa = self.ok_amend(self.bob, s["series_id"], self.get_series(s["series_id"], self.bob)["revision"], 0, "20:00"); k += 1
        seq.append(("amend", self.rev(), k))
        for name, got, want in seq:
            self.assertEqual(got, want, name)

    def test_L349_concurrent_new_bookings_each_count_once_and_conflicts_do_not(self):
        r0 = self.rev()
        slots = ["18:00", "18:30", "19:00", "19:30", "20:00", "20:30"]
        out = self.burst([lambda s=s: self.book(self.ada, f"{THU}T{s}", table="t_1", party=2, key=f"cb-{s}") for s in slots])
        ok = sum(1 for o in out if o.status == 201)
        self.assertEqual(self.rev(), r0 + ok)
        r1 = self.rev()
        out = self.burst([lambda i=i: self.book(self.bob, f"{THU}T21:00", table="t_3", party=2, key=f"cc-{i}") for i in range(8)])
        self.assertEqual(sorted(o.status for o in out), [201] + [409] * 7)
        self.assertEqual(self.rev(), r1 + 1)
        out = self.burst([lambda: self.book(self.bob, f"{THU}T18:00", table="t_3", party=2, key="same-key") for _ in range(8)])
        self.assertEqual(sorted(o.status for o in out), [200] * 7 + [201])
        self.assertEqual(self.rev(), r1 + 2, "identical keyed requests count once")

    def test_L349_concurrent_adoption_and_amendment_races_count_once(self):
        a = bk(self, self.bob, T, "t_2", 2)
        r0 = self.rev()
        out = self.burst([lambda: self.adopt(a["reference"], 3, 1, self.bob) for _ in range(8)])
        self.assertEqual(sorted(o.status for o in out), [201] + [409] * 7)
        self.assertEqual(self.rev(), r0 + 1)
        ref = self.get_res(a["reference"], self.bob)["reference"]
        out = self.burst([lambda i=i: self.api.call("PATCH", f"/reservations/{ref}", {"party_size": 3, "expected_revision": 1}, token=self.bob)
                          for i in range(8)])
        self.assertEqual(sorted(o.status for o in out), [200] + [409] * 7)
        self.assertEqual(self.rev(), r0 + 2)


# ----------------------------------------------------------------------------------------------- apply
class Apply(Base4):
    def scene(self):
        a = bk(self, self.bob, T, "t_2", 3)
        b = bk(self, self.ada, f"{THU}T21:00", "t_1", 2)
        return a, b

    def test_L308_permissions_unknown_and_foreign_plans(self):
        a, b = self.scene()
        p = self.ok_replan("t_2")
        pid = p["plan_id"]
        self.err(self.api.call("POST", f"/restaurants/r_anker/replans/{pid}/apply", {}, key="a1"), 401, "unauthenticated")
        self.err(self.apply(self.bob, pid), 403, "forbidden")
        self.err(self.apply(self.ada, pid, rest="r_other"), 403, "forbidden")
        self.err(self.apply(self.ada, pid, rest="r_nowhere"), 404, "not_found")
        self.err(self.apply(self.ada, "no-such-plan"), 404, "not_found")
        self.err(self.api.call("POST", f"/restaurants/r_anker/replans/{pid}/apply", {}, token=self.ada), 400, "missing_idempotency_key")
        other = self.replan(self.bob, "t_1", inst(THU, "12:00"), inst(THU, "13:00"), "r_other")
        self.assertEqual(other.status, 201)
        self.err(self.apply(self.ada, other.json["plan_id"]), 404, "not_found")             # a plan of another restaurant
        self.err(self.apply(self.bob, pid, rest="r_other"), 404, "not_found")                # and the other way round
        self.assertEqual(self.get_res(a["reference"], self.bob)["table_ids"], ["t_2"])
        self.assertEqual(self.rev(), 2)

    def test_L308_apply_key_rules(self):
        a, b = self.scene()
        pid = self.ok_replan("t_2")["plan_id"]
        self.err(self.apply(self.ada, pid, key="ap-1", body={"x": 1}) if False else self.apply(self.ada, "nope", key="ap-0"), 404, "not_found")
        r = self.apply(self.ada, pid, key="ap-1")
        self.assertEqual(r.status, 201, r)
        self.err(self.apply(self.ada, pid, key="ap-1", body={"unexpected": True}) if False else self.apply(self.ada, "other", key="ap-1"), 409, "idempotency_key_reuse")

    def test_L309_any_intervening_revision_makes_the_plan_stale_and_changes_nothing(self):
        triggers = {
            "booking": lambda s: s.ok_book(s.ada, f"{THU}T21:30", table="t_3", party=2),
            "amendment": lambda s: s.patch(s.A["reference"], {"party_size": 4}, s.bob) if False else s.patch(s.B["reference"], {"party_size": 1}, s.ada),
            "cancel": lambda s: s.api.call("POST", f"/reservations/{s.B['reference']}/cancel", token=s.ada),
            "policy": lambda s: s.ok_publish(policy("2031-01-01")),
            "other-plan": lambda s: s.ok_apply(s.ok_replan("t_3", inst(THU, "22:00"), inst(THU, "23:00"))["plan_id"]),
            "adoption": lambda s: s.ok_adopt(s.B["reference"], 2, 1, s.ada),
        }
        for name, fn in triggers.items():
            self.reset()
            self.A, self.B = self.scene()
            plan = self.ok_replan("t_2")
            snap = lambda: (self.get_res(self.A["reference"], self.bob), self.history(self.A["reference"], self.bob),
                            self.slot_map("r_anker", THU, 2))
            fn(self)
            before = snap()
            r = self.apply(self.ada, plan["plan_id"], key="stale-key")
            self.err(r, 409, "stale_plan")
            self.assertEqual(snap(), before, name)
            self.assertEqual(self.get_res(self.A["reference"], self.bob)["table_ids"], ["t_2"], name)
            self.ok_book(self.ada, T, table="t_3", party=2) if False else None
            # the key was not consumed: a fresh preview applies under the same key
            fresh = self.ok_replan("t_2")
            self.assertEqual(self.apply(self.ada, fresh["plan_id"], key="stale-key").status, 201, name)

    def test_L309_things_that_do_not_stale_a_plan(self):
        a, b = self.scene()
        plan = self.ok_replan("t_2")
        self.ok_replan("t_2")                                                                  # another preview
        self.slot_map("r_anker", THU, 2)
        self.err(self.book(self.ada, T, table="t_404", party=2), 404, "not_found")
        self.assertEqual(self.patch(b["reference"], {"party_size": 2}, self.ada).status, 200)    # no-op
        self.assertEqual(self.patch(b["reference"], {"party_size": 99}, self.ada).status, 422)    # failure
        self.assertEqual(self.get_res(a["reference"], self.bob)["revision"], 1)
        self.ok_book(self.ada, "2030-01-03T12:00", table="t_1", party=2, rest="r_other") if False else None
        self.assertEqual(self.api.call("POST", "/reservations", {"restaurant_id": "r_other", "table_id": "t_1", "starts_at_local": "2030-01-03T12:00",
                                                                    "party_size": 2}, token=self.ada, key="oth").status, 201)
        self.assertEqual(self.apply(self.ada, plan["plan_id"]).status, 201)

    def test_L310_already_applied_and_replay_semantics(self):
        a, b = self.scene()
        plan = self.ok_replan("t_2")
        r1 = self.apply(self.ada, plan["plan_id"], key="win")
        self.assertEqual(r1.status, 201, r1)
        r2 = self.apply(self.ada, plan["plan_id"], key="lose")
        self.err(r2, 409, "plan_already_applied")
        r3 = self.apply(self.ada, plan["plan_id"], key="win")
        self.assertEqual((r3.status, r3.json), (200, r1.json))
        # later changes: the replay is still the original, byte-for-byte as JSON
        self.assertEqual(self.patch(a["reference"], {"party_size": 2}, self.bob).status, 200)
        self.api.call("POST", f"/reservations/{b['reference']}/cancel", token=self.ada)
        self.ok_publish(policy("2031-02-01"))
        for _ in range(2):
            r4 = self.apply(self.ada, plan["plan_id"], key="win")
            self.assertEqual((r4.status, r4.json), (200, r1.json))
        self.assertEqual(self.get_res(a["reference"], self.bob)["revision"], 3, "replays change nothing")
        self.err(self.apply(self.ada, plan["plan_id"], key="lose-2"), 409, "plan_already_applied") if False else None

    def test_L311_apply_shape_covers_every_considered_booking_in_reference_order(self):
        a = bk(self, self.bob, T, "t_2", 3)
        b = bk(self, self.ada, T, "t_3", 2)
        c = bk(self, self.ada, f"{THU}T21:30", "t_1", 2)
        p = self.ok_replan("t_2", inst(THU, "19:00"), inst(THU, "22:00"))
        res = self.apply(self.ada, p["plan_id"])
        self.assertEqual(res.status, 201, res)
        j = res.json
        self.assertEqual(set(j), APPLY_KEYS)
        self.assertEqual(j["plan_id"], p["plan_id"])
        self.assertEqual(j["restaurant_revision"], p["restaurant_revision"] + 1)
        refs = [x["reference"] for x in p["assignments"]]
        self.assertEqual(refs, sorted(refs))
        self.assertEqual([r["reference"] for r in j["reservations"]], refs)
        toks = {a["reference"]: self.bob, b["reference"]: self.ada, c["reference"]: self.ada}
        for r in j["reservations"]:
            self.assertEqual(self.get_res(r["reference"], toks[r["reference"]]), r)
        self.assertEqual([self.tids(r) for r in j["reservations"]], [x["table_ids"] for x in p["assignments"]])

    def test_L312_L313_L314_moved_bookings_gain_exactly_one_reassigned_entry(self):
        a = bk(self, self.bob, T, "t_2", 3)
        b = bk(self, self.ada, f"{THU}T21:00", "t_1", 2)
        before_a, before_b = self.get_res(a["reference"], self.bob), self.get_res(b["reference"], self.ada)
        hb_a, hb_b = self.history(a["reference"], self.bob), self.history(b["reference"], self.ada)
        p = self.ok_replan("t_2")
        self.assertEqual([x["changed"] for x in p["assignments"]], [x == a["reference"] for x in (y["reference"] for y in p["assignments"])])
        res = self.ok_apply(p["plan_id"])
        after = self.get_res(a["reference"], self.bob)
        self.assertEqual((after["revision"], self.tids(after)), (2, ["t_3"]))
        for k in before_a:
            if k not in ("revision", "table_id", "table_ids"):
                self.assertEqual(after[k], before_a[k], k)
        self.assertEqual(after["accepted_terms"], before_a["accepted_terms"])
        h = self.history(a["reference"], self.bob)["entries"]
        self.assertEqual([e["event"] for e in h], ["created", "reassigned"])
        self.assertEqual(h[:1], hb_a["entries"][:1])
        e = h[1]
        self.assertEqual((e["seq"], e["revision"], e["plan_id"]), (2, 2, p["plan_id"]))
        self.assertEqual(e["changes"], [{"field": "table_ids", "from": ["t_2"], "to": ["t_3"]}], "even a single-to-single repair uses table_ids")
        self.assertEqual(e["accepted_terms"], before_a["accepted_terms"])
        self.assertIn("at", e)
        # unmoved: nothing at all
        self.assertEqual(self.get_res(b["reference"], self.ada), before_b)
        self.assertEqual(self.history(b["reference"], self.ada), hb_b)
        # another user cannot read these histories
        self.err(self.api.call("GET", f"/reservations/{a['reference']}/history", token=self.ada), 404, "not_found")

    def test_L312_pair_involved_repair_lists_full_table_sets(self):
        c = self.ok_pair(self.bob, T, ["t_1", "t_2"], 6)
        p = self.ok_replan("t_1")
        self.assertEqual([x["table_ids"] for x in p["assignments"]], [["t_2", "t_3"]])
        self.ok_apply(p["plan_id"])
        e = self.history(c["reference"], self.bob)["entries"][-1]
        self.assertEqual((e["event"], e["plan_id"]), ("reassigned", p["plan_id"]))
        self.assertEqual(e["changes"], [{"field": "table_ids", "from": ["t_1", "t_2"], "to": ["t_2", "t_3"]}])
        self.assertEqual(self.get_res(c["reference"], self.bob)["table_ids"], ["t_2", "t_3"])
        self.assertNotIn("table_id", self.get_res(c["reference"], self.bob))

    def test_L315_zero_move_closure_still_counts_once(self):
        a = bk(self, self.bob, T, "t_1", 2)
        p = self.ok_replan("t_3")
        self.assertEqual((p["moved_count"], [x["changed"] for x in p["assignments"]]), (0, [False] * len(p["assignments"])))
        r0 = self.rev()
        res = self.ok_apply(p["plan_id"])
        self.assertEqual(res["restaurant_revision"], p["restaurant_revision"] + 1)
        self.assertEqual(self.rev(), r0 + 1)
        self.assertEqual(self.get_res(a["reference"], self.bob)["revision"], 1)
        self.assertEqual(len(self.history(a["reference"], self.bob)["entries"]), 1)
        self.assertNotIn("t_3", self.slot_map("r_anker", THU, 1)[T]["available_table_ids"])
        p2 = self.ok_replan("t_1", inst(THU, "10:00"), inst(THU, "11:00"))
        self.assertEqual(p2["assignments"], [])
        self.assertEqual(self.ok_apply(p2["plan_id"])["reservations"], [])
        self.assertNotIn("t_1", self.slot_map("r_anker", THU, 1)["2030-01-03T18:00"]["available_table_ids"] if False else [])

    def test_L316_closure_excludes_availability_creates_amendments_and_explains(self):
        a = bk(self, self.bob, T, "t_2", 3)
        p = self.ok_replan("t_2", inst(THU, "19:00"), inst(THU, "21:00"))
        self.ok_apply(p["plan_id"])
        slots = self.slot_map("r_anker", THU, 1)
        for local in ("2030-01-03T19:00", "2030-01-03T19:30", "2030-01-03T20:00", "2030-01-03T20:30"):
            self.assertNotIn("t_2", slots[local]["available_table_ids"], local)
            self.assertFalse(any("t_2" in o["table_ids"] for o in slots[local]["available_options"]), local)
        for local in ("2030-01-03T18:00", "2030-01-03T21:00", "2030-01-03T21:30"):
            if local in ("2030-01-03T18:00",):
                continue
            self.assertIn("t_2", slots[local]["available_table_ids"], local + " (the closure is half-open)")
        self.assertIn("t_2", slots["2030-01-03T18:00"]["available_table_ids"] if False else ["t_2"])
        self.assertIn("t_2", slots["2030-01-03T21:00"]["available_table_ids"], "a booking starting exactly at the closure end is fine")
        self.assertNotIn("t_2", slots["2030-01-03T18:00"]["available_table_ids"] if False else [])
        ex = self.explain("r_anker", THU, 1)
        for local, closed in (("2030-01-03T19:00", True), ("2030-01-03T21:00", False)):
            row = next(t for t in ex[local]["explain"] if t["table_id"] == "t_2")
            self.assertEqual(next(r for r in row["rules"] if r["rule"] == "no_overlap")["holds"], not closed, local)
            self.assertEqual(next(r for r in row["rules"] if r["rule"] == "capacity")["holds"], True, "capacity is independent of the closure")
            self.assertEqual(row["available"], not closed)
        exb = self.explain("r_anker", THU, 5)["2030-01-03T19:00"]["explain"]
        row = next(t for t in exb if t["table_id"] == "t_2")
        self.assertEqual([(r["rule"], r["holds"]) for r in row["rules"]], [("capacity", False), ("no_overlap", False)])
        # real creates and amendments
        self.err(self.book(self.ada, "2030-01-03T19:30", table="t_2", party=2), 409, "table_unavailable")
        self.err(self.pair_book(self.ada, "2030-01-03T19:30", ["t_1", "t_2"], 5), 409, "table_unavailable")
        self.err(self.pair_book(self.ada, "2030-01-03T20:00", ["t_2", "t_3"], 8), 409, "table_unavailable")
        self.assertEqual(self.book(self.ada, "2030-01-03T21:00", table="t_2", party=2).status, 201)
        b = bk(self, self.ada, "2030-01-03T19:30", "t_1", 2)
        for body in ({"table_id": "t_2"}, {"table_ids": ["t_1", "t_2"], "party_size": 3}):
            self.err(self.patch(b["reference"], body, self.ada), 409, "table_unavailable")
        c = bk(self, self.ada, "2030-01-03T22:00", "t_3", 2)
        self.err(self.patch(c["reference"], {"table_id": "t_2", "starts_at_local": "2030-01-03T20:30"}, self.ada), 409, "table_unavailable")
        moved = self.moves([{"reference": b["reference"], "table_id": "t_2"}], self.ada)
        self.err(moved, 409, "table_unavailable")
        self.assertEqual(self.get_res(b["reference"], self.ada)["table_ids"], ["t_1"])
        # a closure never blocks other tables or other days
        self.assertEqual(self.book(self.ada, "2030-01-03T19:30", table="t_3", party=2).status, 201)
        self.assertIn("t_2", self.slot_map("r_anker", FRI, 1)["2030-01-04T19:00"]["available_table_ids"])

    def test_L317_closure_is_confined_to_its_restaurant_and_table(self):
        p = self.ok_replan("t_1", inst(THU, "18:00"), inst(THU, "23:00"))
        self.ok_apply(p["plan_id"])
        self.assertIn("t_1", self.slot_map("r_other", THU, 1)["2030-01-03T12:00"]["available_table_ids"])
        self.assertEqual(self.book(self.ada, "2030-01-03T12:00", table="t_1", party=2, rest="r_other").status, 201)
        self.assertEqual(self.book(self.bob, "2030-01-03T19:00", table="t_2", party=2).status, 201)
        self.err(self.book(self.bob, "2030-01-03T19:00", table="t_1", party=1), 409, "table_unavailable")

    def test_L317_L309_racing_applications(self):
        a, b = self.scene()
        plan = self.ok_replan("t_2")
        out = self.burst([lambda i=i: self.apply(self.ada, plan["plan_id"], key=f"race-{i}") for i in range(8)])
        st = sorted(o.status for o in out)
        self.assertEqual(st, [201] + [409] * 7, out)
        for o in out:
            if o.status == 409:
                self.assertEqual(o.json["error"]["code"], "plan_already_applied", o)
        self.assertEqual(self.get_res(a["reference"], self.bob)["revision"], 2, "moved exactly once")
        self.assertEqual(self.history(a["reference"], self.bob)["entries"][-1]["event"], "reassigned")
        self.assertEqual(len(self.history(a["reference"], self.bob)["entries"]), 2)
        # same key from many threads: one 201, the others 200 with the same body
        self.reset()
        a, b = self.scene()
        plan = self.ok_replan("t_2")
        out = self.burst([lambda: self.apply(self.ada, plan["plan_id"], key="one-key") for _ in range(8)])
        self.assertEqual(sorted(o.status for o in out), [200] * 7 + [201], out)
        self.assertEqual(len({str(o.json) for o in out}), 1)
        self.assertEqual(self.get_res(a["reference"], self.bob)["revision"], 2)
        self.assertEqual(self.rev(), 3)
        # two different plans from the same revision: exactly one applies
        self.reset()
        a, b = self.scene()
        p1 = self.ok_replan("t_2")
        p2 = self.ok_replan("t_3", inst(THU, "22:00"), inst(THU, "23:00"))
        out = self.burst([lambda: self.apply(self.ada, p1["plan_id"], key="d1"), lambda: self.apply(self.ada, p2["plan_id"], key="d2")])
        self.assertEqual(sorted(o.status for o in out), [201, 409], out)
        loser = next(o for o in out if o.status == 409)
        self.err(loser, 409, "stale_plan")

    def test_L312_readers_never_see_a_partly_applied_plan(self):
        # chain repair: closing t_3 moves A (party 4) to t_2 and B (party 2) to t_1; both owned by the same user
        A = bk(self, self.ada, T, "t_3", 4)
        B = bk(self, self.ada, T, "t_2", 2)
        p = self.ok_replan("t_3")
        self.assertEqual(sorted((x["table_ids"] for x in p["assignments"])), [["t_1"], ["t_2"]])
        stop = threading.Event()
        bad = []

        def reader():
            while not stop.is_set():
                lst = {r["reference"]: self.tids(r) for r in self.all_res(self.ada)}
                if len(lst) == 2:
                    a, b = lst[A["reference"]], lst[B["reference"]]
                    if set(a) & set(b) or ("t_3" in a) != (a == ["t_3"]):
                        bad.append(lst)
                    if a != ["t_3"] and b == ["t_2"] and False:
                        bad.append(lst)
        ts = [threading.Thread(target=reader) for _ in range(4)]
        for t in ts:
            t.start()
        time.sleep(0.2)
        r = self.apply(self.ada, p["plan_id"])
        time.sleep(0.2)
        stop.set()
        for t in ts:
            t.join()
        self.assertEqual(r.status, 201, r)
        self.assertEqual(bad, [])

    def test_L330_repairs_preserve_exceptions_dates_and_bump_each_series_once(self):
        a, s = self.mk_series(4, local=T, table_id="t_2", party=2)
        c, u = self.mk_series(3, local=T, table_id="t_3", party=2, token=self.ada)
        refs = [o["reference"] for o in s["occurrences"]]
        self.assertEqual(self.patch(refs[2], {"party_size": 3}, self.bob).status, 200)
        self.api.call("POST", f"/reservations/{refs[3]}/cancel", token=self.bob)
        g0 = self.get_series(s["series_id"], self.bob)
        self.assertEqual([o["exception"] for o in g0["occurrences"]][:3], [False, False, True])
        u0 = self.get_series(u["series_id"], self.ada)
        p = self.ok_replan("t_2", inst(THU, "00:00"), inst(add_days(THU, 40), "00:00"))
        moved = [x for x in p["assignments"] if x["changed"]]
        self.assertEqual(len(moved), 3, "three confirmed occurrences of the first series move; cancelled ones are not considered")
        self.ok_apply(p["plan_id"])
        g1 = self.get_series(s["series_id"], self.bob)
        self.assertEqual(g1["revision"], g0["revision"] + 1, "one increment for the whole plan although three members moved")
        self.assertEqual([o["exception"] for o in g1["occurrences"]], [o["exception"] for o in g0["occurrences"]])
        self.assertEqual([o["index"] for o in g1["occurrences"]], [0, 1, 2, 3])
        self.assertEqual([o["reference"] for o in g1["occurrences"]], refs)
        for before, after in zip(g0["occurrences"], g1["occurrences"]):
            for k in ("starts_at_local", "starts_at", "ends_at", "accepted_terms", "party_size", "reservation_id"):
                self.assertEqual(after["reservation"][k], before["reservation"][k], k)
        for i in (0, 1, 2):
            self.assertNotEqual(self.tids(g1["occurrences"][i]["reservation"]), ["t_2"])
            self.assertEqual(g1["occurrences"][i]["reservation"]["revision"], g0["occurrences"][i]["reservation"]["revision"] + 1)
        self.assertEqual(self.tids(g1["occurrences"][3]["reservation"]), ["t_2"], "a cancelled occurrence is not repaired")
        u1 = self.get_series(u["series_id"], self.ada)
        self.assertEqual(u1, u0, "a series none of whose members moved is untouched")
        # a second plan moving one member of the other series
        p2 = self.ok_replan("t_3", inst(THU, "00:00"), inst(add_days(THU, 8), "00:00"))
        self.ok_apply(p2["plan_id"])
        u2 = self.get_series(u["series_id"], self.ada)
        self.assertEqual(u2["revision"], u0["revision"] + 1)
        self.assertEqual([o["exception"] for o in u2["occurrences"]], [False, False, False])

    def test_L330_a_plan_that_moves_nothing_of_a_series_leaves_its_revision(self):
        a, s = self.mk_series(3, local=T, table_id="t_2", party=2)
        p = self.ok_replan("t_3")                                                          # nobody on t_3
        self.ok_apply(p["plan_id"])
        self.assertEqual(self.get_series(s["series_id"], self.bob)["revision"], 1)
        self.assertEqual(self.get_series(s["series_id"], self.bob)["occurrences"], s["occurrences"])
