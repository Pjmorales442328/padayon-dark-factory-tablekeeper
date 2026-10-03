"""Idempotency (43-52) and atomic reservation moves (103-111)."""
import json
import unittest

from common import Base, THU, FRI, fixture, seed_res, clock_minute


def body(table="t_2", local=None, party=2, rest="r_anker"):
    return {"restaurant_id": rest, "table_id": table, "starts_at_local": local or f"{THU}T19:00",
            "party_size": party}


class Idempotency(Base):
    def post(self, token, b, key, path="/reservations", raw=None):
        return self.api.call("POST", path, b if raw is None else None, token=token, key=key, raw=raw)

    def test_L048_first_201_replay_200_identical(self):
        t, k = self.ada, "key-1"
        a = self.post(t, body(), k)
        b = self.post(t, body(), k)
        self.assertEqual((a.status, b.status), (201, 200), (a, b))
        self.assertEqual(a.json, b.json)
        self.assertEqual(len(self.api.call("GET", "/reservations", token=t).json["reservations"]), 1)
        for _ in range(3):
            c = self.post(t, body(), k)
            self.assertEqual((c.status, c.json), (200, a.json))

    def test_L049_body_comparison_json_value(self):
        t, k = self.ada, "key-2"
        a = self.post(t, None, k, raw='{"restaurant_id":"r_anker","table_id":"t_2",'
                                      f'"starts_at_local":"{THU}T19:00","party_size":2}}')
        self.assertEqual(a.status, 201)
        b = self.post(t, None, k, raw='\n{ "party_size" : 2 ,\n "starts_at_local":"' + f'{THU}T19:00' +
                                      '", "table_id":"t_2",   "restaurant_id":"r_anker" }\n')
        self.assertEqual((b.status, b.json), (200, a.json), b)
        # unicode escapes decode to same JSON value
        c = self.post(t, None, k, raw='{"restaurant_id":"r_\\u0061nker","table_id":"t_2",'
                                      f'"starts_at_local":"{THU}T19:00","party_size":2}}')
        self.assertEqual((c.status, c.json), (200, a.json), c)

    def test_L049_types_preserved(self):
        t = self.ada
        a = self.post(t, body(party=1, table="t_3"), "key-3")
        self.assertEqual(a.status, 201)
        for variant in (body(party=True, table="t_3"), body(party="1", table="t_3"), body(party=1.5, table="t_3")):
            r = self.post(t, variant, "key-3")
            self.err(r, 409, "idempotency_key_reuse")
        # unknown extra fields change the JSON value
        r = self.post(t, dict(body(party=1, table="t_3"), extra=1), "key-3")
        self.err(r, 409, "idempotency_key_reuse")
        self.assertEqual(self.post(t, body(party=1, table="t_3"), "key-3").status, 200)

    def test_L047_different_body_409_even_if_invalid(self):
        t, k = self.ada, "key-4"
        self.assertEqual(self.post(t, body(), k).status, 201)
        self.err(self.post(t, body(table="t_3"), k), 409, "idempotency_key_reuse")
        self.err(self.post(t, {}, k), 409, "idempotency_key_reuse")
        self.err(self.post(t, {"zzz": 1}, k), 409, "idempotency_key_reuse")
        self.err(self.post(t, body(party=0), k), 409, "idempotency_key_reuse")
        self.err(self.post(t, body(party="x", local="garbage"), k), 409, "idempotency_key_reuse")
        self.err(self.post(t, body(rest="nope"), k), 409, "idempotency_key_reuse")
        self.err(self.post(t, {"restaurant_id": 5}, k), 409, "idempotency_key_reuse")
        self.assertEqual(self.post(t, body(), k).status, 200)

    def test_L046_order_parse_auth_then_receipt_then_fields(self):
        t, k = self.ada, "key-5"
        self.assertEqual(self.post(t, body(), k).status, 201)
        # not an object -> 400 before receipt lookup
        self.err(self.post(t, None, k, raw="[1]"), 400, "malformed_request")
        self.err(self.post(t, None, k, raw="{oops"), 400, "malformed_request")
        # no auth -> 401 before receipt lookup
        self.err(self.api.call("POST", "/reservations", {}, key=k), 401, "unauthenticated")
        # another user's use of the same key is independent: invalid body -> field validation
        self.err(self.post(self.bob, {}, k), 422, "validation_failed")

    def test_L050_failed_requests_do_not_consume_keys(self):
        t = self.ada
        k = "key-6"
        self.err(self.post(t, body(party=0), k), 422, "validation_failed")
        self.err(self.post(t, body(table="nope"), k), 404, "not_found")
        self.err(self.post(t, body(local=f"{THU}T19:15"), k), 422, "not_on_slot_grid")
        # now a different valid body with the same key is first use
        r = self.post(t, body(), k)
        self.assertEqual(r.status, 201, r)
        self.assertEqual(self.post(t, body(), k).status, 200)

    def test_L050_conflict_does_not_consume_key(self):
        held = self.ok_book(self.bob, f"{THU}T19:00")
        t, k = self.ada, "key-7"
        self.err(self.post(t, body(), k), 409, "table_unavailable")
        self.err(self.post(t, body(), k), 409, "table_unavailable")      # not a replay of the failure
        self.api.call("POST", f"/reservations/{held['reference']}/cancel", token=self.bob)
        r = self.post(t, body(), k)
        self.assertEqual(r.status, 201, r)                              # first use
        self.assertEqual(self.post(t, body(), k).status, 200)

    def test_L050_missing_key_does_not_consume(self):
        self.err(self.api.call("POST", "/reservations", body(), token=self.ada), 400, "missing_idempotency_key")
        self.assertEqual(len(self.api.call("GET", "/reservations", token=self.ada).json["reservations"]), 0)

    def test_L044_scope_user(self):
        a, b = self.ada, self.bob
        r1 = self.post(a, body(table="t_1"), "same")
        # same key AND same body from another user is not a replay (table is taken)
        r3 = self.post(b, body(table="t_1"), "same")
        self.err(r3, 409, "table_unavailable")
        r2 = self.post(b, body(table="t_2"), "same")      # failed 4xx did not consume bob's key
        self.assertEqual((r1.status, r2.status), (201, 201))
        self.assertNotEqual(r1.json["reference"], r2.json["reference"])
        self.assertEqual(self.post(a, body(table="t_1"), "same").status, 200)
        self.assertEqual(self.post(b, body(table="t_2"), "same").status, 200)

    def test_L045_other_path_independent(self):
        t = self.ada
        a = self.ok_book(t, f"{THU}T19:00", table="t_2", key="shared")
        b = self.ok_book(t, f"{THU}T19:00", table="t_3", key="other")
        r = self.api.call("POST", "/reservation-moves", {"moves": [{"reference": a["reference"], "table_id": "t_1"}]},
                          token=t, key="shared")
        self.assertEqual(r.status, 201, r)
        r2 = self.api.call("POST", "/reservation-moves", {"moves": [{"reference": a["reference"], "table_id": "t_1"}]},
                           token=t, key="shared")
        self.assertEqual((r2.status, r2.json), (200, r.json))
        # and the key on /reservations still replays its own response
        again = self.post(t, body(table="t_2"), "shared")
        self.assertEqual((again.status, again.json), (200, a))

    def test_L052_replay_after_amend_and_cancel(self):
        t = self.ada
        first = self.post(t, body(), "key-8")
        ref = first.json["reference"]
        self.assertEqual(self.api.call("PATCH", f"/reservations/{ref}", {"starts_at_local": f"{THU}T21:00"},
                                       token=t).status, 200)
        r = self.post(t, body(), "key-8")
        self.assertEqual((r.status, r.json), (200, first.json))
        self.assertEqual(self.api.call("GET", f"/reservations/{ref}", token=t).json["starts_at_local"], f"{THU}T21:00")
        self.assertEqual(self.api.call("POST", f"/reservations/{ref}/cancel", token=t).status, 200)
        r = self.post(t, body(), "key-8")
        self.assertEqual((r.status, r.json), (200, first.json))
        self.assertEqual(r.json["status"], "confirmed")
        # replay must not re-book the cancelled slot
        self.assertIn("t_2", self.slot_map("r_anker", THU)[f"{THU}T21:00"]["available_table_ids"])
        self.assertIn("t_2", self.slot_map("r_anker", THU)[f"{THU}T19:00"]["available_table_ids"])
        self.assertEqual(self.api.call("GET", f"/reservations/{ref}", token=t).json["status"], "cancelled")
        self.assertEqual(len(self.api.call("GET", "/reservations", token=t).json["reservations"]), 1)

    def test_L051_concurrent_identical(self):
        t = self.ada
        outs = self.burst([lambda: self.post(t, body(), "conc-1")] * 25)
        self.assertEqual(sorted(o.status for o in outs), [200] * 24 + [201])
        self.assertEqual(len({json.dumps(o.json, sort_keys=True) for o in outs}), 1)
        self.assertEqual(len(self.api.call("GET", "/reservations", token=t).json["reservations"]), 1)

    def test_L051_concurrent_same_key_different_bodies(self):
        t = self.ada
        bodies = [body(table="t_1", party=1), body(table="t_2", party=1), body(table="t_3", party=1)]
        outs = self.burst([lambda i=i: self.post(t, bodies[i % 3], "conc-2") for i in range(18)])
        self.assertEqual(sum(o.status == 201 for o in outs), 1)
        for o in outs:
            self.assertIn(o.status, (200, 201, 409))
            if o.status == 409:
                self.err(o, 409, "idempotency_key_reuse")
        self.assertEqual(len(self.api.call("GET", "/reservations", token=t).json["reservations"]), 1)

    def test_L051_concurrent_distinct_keys_same_slot_one_winner(self):
        outs = self.burst([lambda i=i: self.post(self.ada if i % 2 else self.bob, body(), f"d-{i}") for i in range(16)])
        self.assertEqual(sorted(o.status for o in outs), [201] + [409] * 15)

    def test_L043_idempotency_not_on_other_endpoints(self):
        t = self.ada
        j = self.ok_book(t, f"{THU}T19:00")
        for _ in range(2):   # cancel / patch need no key
            self.assertEqual(self.api.call("PATCH", f"/reservations/{j['reference']}", {"party_size": 2}, token=t).status, 200)
        self.assertEqual(self.api.call("POST", f"/reservations/{j['reference']}/cancel", token=t).status, 200)


class Moves(Base):
    def setUp(self):
        super().setUp()
        self.t = self.ada
        self.A = self.ok_book(self.t, f"{THU}T19:00", table="t_2")
        self.B = self.ok_book(self.t, f"{THU}T19:00", table="t_3")

    def mv(self, moves, key=None, token=None, raw=None):
        return self.api.call("POST", "/reservation-moves", None if raw else {"moves": moves}, raw=raw,
                             token=token or self.t, key=key or self.newkey())

    def get(self, ref, token=None):
        return self.api.call("GET", f"/reservations/{ref}", token=token or self.t).json

    def test_L109_L110_swap(self):
        r = self.mv([{"reference": self.A["reference"], "table_id": "t_3"},
                     {"reference": self.B["reference"], "table_id": "t_2"}])
        self.assertEqual(r.status, 201, r)
        res = r.json["reservations"]
        self.assertEqual([x["reference"] for x in res], [self.A["reference"], self.B["reference"]])
        self.assertEqual([x["table_id"] for x in res], ["t_3", "t_2"])
        for x, o in zip(res, (self.A, self.B)):
            for k in ("reservation_id", "reference", "created_at", "restaurant_id", "starts_at", "ends_at", "party_size", "status"):
                self.assertEqual(x[k], o[k])
        self.assertEqual(self.get(self.A["reference"])["table_id"], "t_3")
        self.assertEqual(self.get(self.B["reference"])["table_id"], "t_2")
        self.assertEqual(set(r.json), {"reservations"})

    def test_L110_input_order_and_unchanged_items(self):
        c = self.ok_book(self.t, f"{THU}T19:00", table="t_1", party=1)
        r = self.mv([{"reference": c["reference"]}, {"reference": self.B["reference"], "party_size": 3},
                     {"reference": self.A["reference"], "starts_at_local": f"{THU}T21:00"}])
        self.assertEqual(r.status, 201, r)
        res = r.json["reservations"]
        self.assertEqual([x["reference"] for x in res], [c["reference"], self.B["reference"], self.A["reference"]])
        self.assertEqual(res[0], c)
        self.assertEqual(res[1]["party_size"], 3)
        self.assertEqual(res[1]["table_id"], "t_3")
        self.assertEqual(res[2]["starts_at_local"], f"{THU}T21:00")
        self.assertEqual(res[2]["table_id"], "t_2")
        self.assertEqual(res[2]["ends_at"], f"{THU}T22:30:00+01:00")

    def test_L110_noop_items(self):
        r = self.mv([{"reference": self.A["reference"], "table_id": "t_2", "party_size": 2,
                      "starts_at_local": f"{THU}T19:00"}, {"reference": self.B["reference"]}])
        self.assertEqual(r.status, 201, r)
        self.assertEqual(r.json["reservations"], [self.A, self.B])
        self.err(self.book(self.bob, f"{THU}T19:00", table="t_2"), 409, "table_unavailable")

    def test_L105_unknown_fields_ignored_identity_preserved(self):
        r = self.mv([{"reference": self.A["reference"], "table_id": "t_1", "party_size": 1, "junk": 5,
                      "reservation_id": "hack", "status": "cancelled", "created_at": "2000-01-01T00:00:00+00:00"}])
        self.assertEqual(r.status, 201, r)
        x = r.json["reservations"][0]
        for k in ("reservation_id", "reference", "created_at", "status", "restaurant_id"):
            self.assertEqual(x[k], self.A[k])
        self.assertEqual((x["table_id"], x["party_size"]), ("t_1", 1))

    def test_L103_shape(self):
        for b in ({"moves": []}, {"moves": "x"}, {"moves": {}}, {}, {"moves": [1]}, {"moves": [None]},
                  {"moves": [{"table_id": "t_1"}]}, {"moves": [{"reference": 5}]},
                  {"moves": [{"reference": self.A["reference"]}, {"reference": self.A["reference"]}]},
                  {"moves": [{"reference": self.A["reference"], "table_id": "t_1"},
                             {"reference": self.A["reference"], "table_id": "t_3"}]},
                  {"moves": [{"reference": f"X{i}"} for i in range(9)]},
                  {"moves": [{"reference": self.A["reference"]}] + [{"reference": f"X{i}"} for i in range(8)]}):
            r = self.api.call("POST", "/reservation-moves", b, token=self.t, key=self.newkey())
            self.assertIn(r.status, (422, 400), (b, r))
        # concrete codes: wrong-type containers are 400 or 422; the spec says invalid shape -> 422
        for b in ({"moves": []}, {}, {"moves": [{"reference": self.A["reference"]}, {"reference": self.A["reference"]}]},
                  {"moves": [{"reference": f"X{i}"} for i in range(9)]}):
            self.err(self.api.call("POST", "/reservation-moves", b, token=self.t, key=self.newkey()), 422, "validation_failed")
        self.err(self.api.call("POST", "/reservation-moves", {"moves": [{"table_id": "t_1"}]}, token=self.t,
                               key=self.newkey()), 422, "validation_failed")

    def test_L103_limit_8_and_1(self):
        # exactly 8 is accepted: seed enough bookings
        f = fixture(reservations=[seed_res(i, "u_ada", "r_other", "t_1" if i % 2 else "t_9", f"{THU}T{12 + i // 2 * 1:02d}:00",
                                           1) for i in range(1, 9)])
        # simpler: 8 bookings at distinct slots on r_other t_1 (60 minute slots)
        f = fixture(reservations=[seed_res(i, "u_ada", "r_other", "t_1", f"{THU}T{11 + i:02d}:00", 1) for i in range(1, 9)])
        self.reset(f)
        t = self.ada
        ok = self.api.call("POST", "/reservation-moves", {"moves": [{"reference": f"SEED{i:02d}"} for i in range(1, 9)]},
                           token=t, key="eight")
        self.assertEqual(ok.status, 201, ok)
        self.assertEqual(len(ok.json["reservations"]), 8)
        bad = self.api.call("POST", "/reservation-moves", {"moves": [{"reference": f"SEED{i:02d}"} for i in range(1, 9)]
                                                            + [{"reference": "SEED09"}]}, token=t, key="nine")
        self.err(bad, 422, "validation_failed")

    def test_L038_no_token_401(self):
        r = self.api.call("POST", "/reservation-moves", {"moves": [{"reference": self.A["reference"]}]}, key="k")
        self.err(r, 401, "unauthenticated")

    def test_L104_ownership_and_restaurants(self):
        o = self.ok_book(self.bob, f"{THU}T18:00", table="t_1")
        r = self.mv([{"reference": self.A["reference"], "table_id": "t_1"}, {"reference": o["reference"]}])
        self.err(r, 404, "not_found")
        self.err(self.mv([{"reference": "NOSUCH1"}]), 404, "not_found")
        self.assertEqual(self.get(self.A["reference"])["table_id"], "t_2")
        other = self.ok_book(self.t, f"{THU}T13:00", table="t_1", rest="r_other", party=1)
        r = self.mv([{"reference": self.A["reference"]}, {"reference": other["reference"]}])
        self.err(r, 422, "validation_failed")
        # a single booking at another restaurant is fine
        self.assertEqual(self.mv([{"reference": other["reference"], "table_id": "t_9"}]).status, 201)
        # table of another restaurant is a 404
        self.err(self.mv([{"reference": self.A["reference"], "table_id": "t_9"}]), 404, "not_found")

    def test_L106_cancelled_and_cutoff(self):
        self.api.call("POST", f"/reservations/{self.B['reference']}/cancel", token=self.t)
        r = self.mv([{"reference": self.A["reference"]}, {"reference": self.B["reference"]}])
        self.err(r, 409, "reservation_cancelled")
        f = fixture(reservations=[seed_res(1, "u_ada", "r_clock", "t_1", clock_minute(100), 2),
                                  seed_res(2, "u_ada", "r_clock", "t_2", clock_minute(60 * 72), 2)])
        self.reset(f)
        t = self.ada
        r = self.api.call("POST", "/reservation-moves", {"moves": [{"reference": "SEED02", "party_size": 1},
                                                                  {"reference": "SEED01", "party_size": 1}]},
                          token=t, key="c1")
        self.err(r, 409, "cutoff_passed")
        self.assertEqual(self.api.call("GET", "/reservations/SEED02", token=t).json["party_size"], 2)
        # cutoff precedes other changes for the same booking (even an invalid change)
        r = self.api.call("POST", "/reservation-moves", {"moves": [{"reference": "SEED01", "party_size": 99}]},
                          token=t, key="c2")
        self.err(r, 409, "cutoff_passed")
        r = self.api.call("POST", "/reservation-moves", {"moves": [{"reference": "SEED01", "party_size": 0}]},
                          token=t, key="c3")
        self.assertIn(r.status, (409, 422))
        self.assertEqual(r.status, 409, "cutoff precedes other changes for that booking")

    def test_L107_non_occupancy_before_occupancy(self):
        # item 0 conflicts with C (unlisted), item 1 is invalid -> invalid error wins
        self.ok_book(self.bob, f"{THU}T21:00", table="t_1", party=1)
        a, b = self.A["reference"], self.B["reference"]
        r = self.mv([{"reference": a, "table_id": "t_1", "starts_at_local": f"{THU}T21:00", "party_size": 2},
                     {"reference": b, "party_size": 99}])
        self.err(r, 422, "party_exceeds_capacity")
        r = self.mv([{"reference": a, "table_id": "t_1", "starts_at_local": f"{THU}T21:00"},
                     {"reference": b, "starts_at_local": f"{THU}T19:15"}])
        self.err(r, 422, "not_on_slot_grid")
        r = self.mv([{"reference": a, "table_id": "t_1", "starts_at_local": f"{THU}T21:00"},
                     {"reference": b, "starts_at_local": "bad"}])
        self.err(r, 422, "validation_failed")
        r = self.mv([{"reference": a, "table_id": "t_1", "starts_at_local": f"{THU}T21:00"},
                     {"reference": b, "table_id": "t_77"}])
        self.err(r, 404, "not_found")
        # and with only the conflict it is 409
        r = self.mv([{"reference": a, "table_id": "t_1", "starts_at_local": f"{THU}T21:00"}])
        self.err(r, 409, "table_unavailable")

    def test_L107_errors_in_input_order(self):
        a, b = self.A["reference"], self.B["reference"]
        r = self.mv([{"reference": a, "party_size": 99}, {"reference": b, "starts_at_local": f"{THU}T19:15"}])
        self.err(r, 422, "party_exceeds_capacity")
        r = self.mv([{"reference": b, "starts_at_local": f"{THU}T19:15"}, {"reference": a, "party_size": 99}])
        self.err(r, 422, "not_on_slot_grid")
        self.api.call("POST", f"/reservations/{b}/cancel", token=self.t)
        r = self.mv([{"reference": a, "party_size": 99}, {"reference": b}])
        self.err(r, 422, "party_exceeds_capacity")
        r = self.mv([{"reference": b}, {"reference": a, "party_size": 99}])
        self.err(r, 409, "reservation_cancelled")

    def test_L108_overlaps(self):
        a, b = self.A["reference"], self.B["reference"]
        # both listed bookings onto the same table/time
        self.err(self.mv([{"reference": a, "table_id": "t_1", "party_size": 1},
                          {"reference": b, "table_id": "t_1", "party_size": 1}]), 409, "table_unavailable")
        # overlapping results among themselves, partial overlap
        self.err(self.mv([{"reference": a, "table_id": "t_1", "party_size": 1},
                          {"reference": b, "table_id": "t_1", "party_size": 1, "starts_at_local": f"{THU}T20:00"}]),
                 409, "table_unavailable")
        # with an unlisted confirmed booking
        self.ok_book(self.bob, f"{THU}T19:30", table="t_1", party=1)
        self.err(self.mv([{"reference": a, "table_id": "t_1", "party_size": 1}]), 409, "table_unavailable")
        # adjacent results are fine
        r = self.mv([{"reference": a, "table_id": "t_1", "party_size": 1, "starts_at_local": f"{THU}T21:00"},
                     {"reference": b}])
        self.assertEqual(r.status, 201, r)
        for ref, tbl in ((a, "t_2"), (b, "t_3")):
            pass

    def test_L108_unchanged_listed_retains_occupancy(self):
        a, b = self.A["reference"], self.B["reference"]
        # move A onto B's table while B is listed but unchanged -> conflict
        self.err(self.mv([{"reference": a, "table_id": "t_3"}, {"reference": b}]), 409, "table_unavailable")
        self.err(self.mv([{"reference": b}, {"reference": a, "table_id": "t_3"}]), 409, "table_unavailable")

    def test_L109_atomic_failure_leaves_everything(self):
        a, b = self.A["reference"], self.B["reference"]
        self.ok_book(self.bob, f"{THU}T21:00", table="t_1", party=1)
        before = self.api.call("GET", "/reservations", token=self.t).json
        m = self.api.call("GET", f"/availability?restaurant_id=r_anker&date={THU}&party_size=1").json
        key = "atomic-1"
        moves = [{"reference": a, "table_id": "t_1", "starts_at_local": f"{THU}T22:00"},    # invalid hours
                 {"reference": b, "table_id": "t_1"}]
        self.err(self.mv(moves, key=key), 422, "outside_opening_hours")
        moves2 = [{"reference": a, "starts_at_local": f"{THU}T21:00"},   # fine alone
                  {"reference": b, "starts_at_local": f"{THU}T21:00", "table_id": "t_1"}]   # conflicts with bob
        self.err(self.mv(moves2, key=key), 409, "table_unavailable")
        self.assertEqual(self.api.call("GET", "/reservations", token=self.t).json, before)
        self.assertEqual(self.api.call("GET", f"/availability?restaurant_id=r_anker&date={THU}&party_size=1").json, m)
        # key unused: valid body with the same key now succeeds as first use
        r = self.mv([{"reference": a, "starts_at_local": f"{THU}T21:00"}], key=key)
        self.assertEqual(r.status, 201, r)

    def test_L109_race_two_batches_same_target(self):
        c = self.ok_book(self.ada, f"{THU}T19:00", table="t_1", party=1)
        outs = self.burst([
            lambda: self.mv([{"reference": self.A["reference"], "starts_at_local": f"{THU}T21:00", "table_id": "t_1"}],
                            key="rb-1"),
            lambda: self.mv([{"reference": self.B["reference"], "starts_at_local": f"{THU}T21:00", "table_id": "t_1"}],
                            key="rb-2")])
        self.assertEqual(sorted(o.status for o in outs), [201, 409])

    def test_L111_replay(self):
        a, b = self.A["reference"], self.B["reference"]
        moves = [{"reference": a, "table_id": "t_3"}, {"reference": b, "table_id": "t_2"}]
        r1 = self.mv(moves, key="mv-1")
        self.assertEqual(r1.status, 201)
        r2 = self.mv(moves, key="mv-1")
        self.assertEqual((r2.status, r2.json), (200, r1.json))
        self.api.call("PATCH", f"/reservations/{a}", {"starts_at_local": f"{THU}T21:00"}, token=self.t)
        self.api.call("POST", f"/reservations/{b}/cancel", token=self.t)
        r3 = self.mv(moves, key="mv-1")
        self.assertEqual((r3.status, r3.json), (200, r1.json))
        # state untouched by replay
        self.assertEqual(self.get(a)["starts_at_local"], f"{THU}T21:00")
        self.assertEqual(self.get(b)["status"], "cancelled")
        # same key, different body -> 409 even when it would be invalid
        self.err(self.mv([{"reference": a, "party_size": 99}], key="mv-1"), 409, "idempotency_key_reuse")
        self.err(self.api.call("POST", "/reservation-moves", {"moves": []}, token=self.t, key="mv-1"), 409,
                 "idempotency_key_reuse")
        # moves order matters (JSON array)
        self.err(self.mv(list(reversed(moves)), key="mv-1"), 409, "idempotency_key_reuse")
        # other user, same key: independent (404 for foreign refs)
        self.err(self.mv(moves, key="mv-1", token=self.bob), 404, "not_found")

    def test_L111_concurrent_identical_batch(self):
        moves = [{"reference": self.A["reference"], "table_id": "t_3"}, {"reference": self.B["reference"], "table_id": "t_2"}]
        outs = self.burst([lambda: self.mv(moves, key="mv-c")] * 20)
        self.assertEqual(sorted(o.status for o in outs), [200] * 19 + [201])
        self.assertEqual(len({json.dumps(o.json, sort_keys=True) for o in outs}), 1)
        self.assertEqual(self.get(self.A["reference"])["table_id"], "t_3")

    def test_L111_failed_batch_key_reusable_after_4xx(self):
        key = "mv-f"
        self.err(self.mv([{"reference": "NOSUCH1"}], key=key), 404, "not_found")
        self.err(self.mv([], key=key), 422, "validation_failed")
        r = self.mv([{"reference": self.A["reference"], "table_id": "t_1"}], key=key)
        self.assertEqual(r.status, 201, r)

    def test_L110_json_types_in_moves(self):
        a = self.A["reference"]
        for item in ({"reference": a, "party_size": "2"}, {"reference": a, "party_size": True},
                     {"reference": a, "party_size": 2.5}, {"reference": a, "party_size": 0}):
            self.err(self.mv([item]), 422, "validation_failed")
        for item in ({"reference": a, "table_id": 5}, {"reference": a, "starts_at_local": 5}):
            r = self.mv([item])
            self.assertIn(r.status, (400, 422), r)
