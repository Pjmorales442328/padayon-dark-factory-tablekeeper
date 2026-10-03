"""Version transfer and stage 2 state validation (ledger 87-102, 152, 154, 179, 183-186, 189, 194).

TestUpgrade starts the actual frozen stage-1 service, fills it with realistic state, exports it, STOPS that process, then
starts an independent stage-2 service and imports. Exports (tokens, hashes) stay in memory only.
"""
import copy
import json
import os
import subprocess
import time
import unittest

from s2common import (Api, Base2, STAGE1_DIR, STAGE2_DIR, THU, FRI, fixture2, stage1_fixture, seed_res, start_at,
                      stop_process, port_closed, wait_port_closed, common)
from test_e_transfer import walk, get_at, replace_value, record_nodes

T = f"{THU}T19:00"
ORIGINAL = {}


def new_stage2():
    return start_at(STAGE2_DIR)


class TestUpgrade(unittest.TestCase):
    err = Base2.err
    """One real migration, many observations."""

    @classmethod
    def setUpClass(cls):
        cls.src_base, cls.src_proc, cls.src_port = start_at(STAGE1_DIR)
        s = Api(cls.src_base)
        f = stage1_fixture(reservations=[seed_res(1, "u_bob", "r_anker", "t_1", f"{FRI}T18:00", 2, "BOBSEED1")])
        f["users"][0]["password"] = "abc"                                  # short seeded password, stage 1 behaviour
        assert s.call("POST", "/_test/reset", f).status == 204
        cls.tok_ada = s.call("POST", "/auth/login", {"email": "ada@example.com", "password": "abc"}).json["token"]
        cls.tok_ada2 = s.call("POST", "/auth/login", {"email": "ada@example.com", "password": "abc"}).json["token"]
        cls.tok_bob = s.call("POST", "/auth/login", {"email": "bob@example.com", "password": "battery staple"}).json["token"]
        cls.signup = s.call("POST", "/auth/signup", {"email": "new@example.com", "password": "pw-12345678", "display_name": "New"}).json
        bodies = {}

        def book(key, tid, local, party, tok):
            b = {"restaurant_id": "r_anker", "table_id": tid, "starts_at_local": local, "party_size": party}
            r = s.call("POST", "/reservations", b, token=tok, key=key)
            assert r.status == 201, r
            bodies[key] = (b, tok, r.json)
            return r.json
        cls.A = book("up-A", "t_2", T, 2, cls.tok_ada)
        cls.B = book("up-B", "t_3", T, 2, cls.tok_ada)
        cls.C = book("up-C", "t_1", f"{THU}T21:00", 1, cls.tok_ada)
        cls.D = book("up-D", "t_1", T, 2, cls.tok_bob)
        s.call("POST", f"/reservations/{cls.C['reference']}/cancel", token=cls.tok_ada)
        cls.moves_body = {"moves": [{"reference": cls.A["reference"], "table_id": "t_3"},
                                    {"reference": cls.B["reference"], "table_id": "t_2"}]}
        cls.moves_resp = s.call("POST", "/reservation-moves", cls.moves_body, token=cls.tok_ada, key="up-M")
        assert cls.moves_resp.status == 201
        cls.patched = s.call("PATCH", f"/reservations/{cls.B['reference']}", {"starts_at_local": f"{THU}T21:00"},
                             token=cls.tok_ada).json
        cls.failed = s.call("POST", "/reservations", dict(bodies["up-A"][0], table_id="nope"), token=cls.tok_bob, key="up-F")
        assert cls.failed.status == 404
        cls.bodies = bodies
        cls.list_ada = s.call("GET", "/reservations", token=cls.tok_ada).json
        cls.list_bob = s.call("GET", "/reservations", token=cls.tok_bob).json
        cls.avail_src = {d: s.call("GET", f"/availability?restaurant_id=r_anker&date={d}&party_size=1").json for d in (THU, FRI)}
        cls.export = s.call("GET", "/_test/export").json                          # private: memory only
        # the actual source is stopped BEFORE the destination exists
        stop_process(cls.src_proc)
        cls.source_stopped_before_import = wait_port_closed(cls.src_port) and cls.src_proc.poll() is not None
        cls.dst_base, cls.dst_proc, _ = new_stage2()
        cls.d = Api(cls.dst_base)
        cls.d.call("POST", "/_test/reset", fixture2(reservations=[seed_res(9, "u_ada", "r_anker", "t_2", f"{THU}T20:00", 2, "DESTONLY")]))
        cls.dest_token = cls.d.call("POST", "/auth/login", {"email": "ada@example.com", "password": "correct horse"}).json["token"]
        cls.import_resp = cls.d.call("POST", "/_test/import", cls.export)

    @classmethod
    def tearDownClass(cls):
        for p in (cls.src_proc, cls.dst_proc):
            if p.poll() is None:
                p.kill()

    def setUp(self):
        # every observation starts from the unchanged imported baseline (earlier methods mutate occupancy)
        self.assertEqual(self.d.call("POST", "/_test/import", self.export).status, 204)

    def test_L152_L194_source_stopped_then_import_accepted(self):
        self.assertTrue(self.source_stopped_before_import, "source stage-1 process must be down before the import")
        self.assertEqual(self.import_resp.status, 204, self.import_resp)
        self.assertEqual(self.import_resp.raw, b"")
        self.assertEqual(self.export["track"], "tablekeeper")
        self.assertEqual(self.export["format_version"], 1)

    def test_L152_L193_no_dependency_on_source_files_or_network(self):
        # the destination keeps serving with the source gone and holds none of its sockets
        self.assertTrue(port_closed(self.src_port))
        self.assertEqual(self.d.call("GET", "/health").json, {"status": "ok"})

    def test_L153_L186_old_tokens_and_logins_survive(self):
        d = self.d
        for t in (self.tok_ada, self.tok_ada2, self.tok_bob, self.signup["token"]):
            self.assertEqual(d.call("GET", "/reservations", token=t).status, 200)
        self.assertEqual(d.call("POST", "/auth/login", {"email": "ada@example.com", "password": "abc"}).json["user_id"], "u_ada")
        self.assertEqual(d.call("POST", "/auth/login", {"email": "bob@example.com", "password": "battery staple"}).status, 200)
        self.assertEqual(d.call("POST", "/auth/login", {"email": "new@example.com", "password": "pw-12345678"}).json["user_id"],
                         self.signup["user_id"])
        self.assertEqual(d.call("POST", "/auth/login", {"email": "ada@example.com", "password": "correct horse"}).status, 401)
        self.assertEqual(d.call("GET", "/reservations", token=self.dest_token).status, 401)      # destination data removed
        self.assertEqual(d.call("GET", "/reservations/DESTONLY", token=self.tok_ada).status, 404)

    def test_L154_L184_references_resolve_and_singletons_gain_table_ids(self):
        d = self.d
        for tok, mine in ((self.tok_ada, self.list_ada["reservations"]), (self.tok_bob, self.list_bob["reservations"])):
            for before in mine:
                r = d.call("GET", f"/reservations/{before['reference']}", token=tok)
                self.assertEqual(r.status, 200, before)
                self.assertEqual(r.json, dict(before, table_ids=[before["table_id"]]), "legacy fields kept, table_ids added")
        got = d.call("GET", "/reservations", token=self.tok_ada).json["reservations"]
        self.assertEqual(got, [dict(x, table_ids=[x["table_id"]]) for x in self.list_ada["reservations"]])
        self.assertEqual(d.call("GET", "/reservations/BOBSEED1", token=self.tok_bob).json["reservation_id"], "res_s1")
        self.assertEqual(d.call("GET", f"/reservations/{self.A['reference']}", token=self.tok_bob).status, 404)

    def test_L185_stage1_receipts_return_original_json_exactly(self):
        d = self.d
        for key, (body, tok, original) in self.bodies.items():
            r = d.call("POST", "/reservations", body, token=tok, key=key)
            self.assertEqual(r.status, 200, (key, r))
            self.assertEqual(r.json, original, key)
            self.assertNotIn("table_ids", r.json, "original legacy snapshot must not be regenerated")
        r = d.call("POST", "/reservation-moves", self.moves_body, token=self.tok_ada, key="up-M")
        self.assertEqual((r.status, r.json), (200, self.moves_resp.json))
        for x in r.json["reservations"]:
            self.assertNotIn("table_ids", x)

    def test_L094_L179_receipt_rules_still_hold_after_upgrade(self):
        d = self.d
        body, tok, _ = self.bodies["up-A"]
        self.err(d.call("POST", "/reservations", dict(body, party_size=1), token=tok, key="up-A"), 409, "idempotency_key_reuse")
        self.err(d.call("POST", "/reservations", dict(body, table_ids=["t_2"]), token=tok, key="up-A"), 409, "idempotency_key_reuse")
        self.err(d.call("POST", "/reservation-moves", {"moves": [self.moves_body["moves"][0]]}, token=self.tok_ada, key="up-M"),
                 409, "idempotency_key_reuse")
        ok = d.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_id": "t_1", "starts_at_local": f"{FRI}T20:00",
                                              "party_size": 1}, token=self.tok_bob, key="up-F")
        self.assertEqual(ok.status, 201, ok)                                   # failed key reusable
        other = d.call("POST", "/reservations", dict(body, table_id="t_1", starts_at_local=f"{FRI}T21:30", party_size=1),
                       token=self.tok_bob, key="up-A")
        self.assertEqual(other.status, 201, other)                              # same key, other user

    def test_L184_stage1_configuration_has_no_pairs_and_availability_matches(self):
        d = self.d
        for date in (THU, FRI):
            now = d.call("GET", f"/availability?restaurant_id=r_anker&date={date}&party_size=1").json
            for a, b in zip(self.avail_src[date]["slots"], now["slots"]):
                self.assertEqual(a["available_table_ids"], b["available_table_ids"])
                self.assertEqual([o["table_ids"] for o in b["available_options"]], [[x] for x in b["available_table_ids"]])
        r = d.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_ids": ["t_1", "t_2"], "starts_at_local": f"{THU}T18:00",
                                             "party_size": 3}, token=self.tok_ada, key="up-new")
        self.err(r, 422, "combination_not_allowed")
        self.assertEqual(len(d.call("GET", "/restaurants").json["restaurants"]), 6)

    def test_L093_L188_occupancy_preserved_cancelled_free(self):
        d = self.d
        cur = self.patched                                                      # B moved to t_2 at 21:00
        r = d.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_id": cur["table_id"],
                                             "starts_at_local": cur["starts_at_local"], "party_size": 1},
                   token=self.tok_bob, key="up-occ")
        self.err(r, 409, "table_unavailable")
        r = d.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_id": "t_1", "starts_at_local": f"{THU}T21:00",
                                             "party_size": 1}, token=self.tok_bob, key="up-free")
        self.assertEqual(r.status, 201, r)                                      # C was cancelled -> free

    def test_L186_new_identities_do_not_collide_after_upgrade(self):
        d = self.d
        old = {x["reference"] for x in self.list_ada["reservations"] + self.list_bob["reservations"]} | {"BOBSEED1"}
        old_ids = {x["reservation_id"] for x in self.list_ada["reservations"] + self.list_bob["reservations"]}
        new = []
        for i in range(6):
            r = d.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_id": "t_3", "starts_at_local": f"2030-03-0{i + 4}T19:00",
                                                 "party_size": 2}, token=self.tok_ada, key=f"up-n{i}")
            self.assertEqual(r.status, 201, r)
            new.append(r.json)
        self.assertFalse(old & {n["reference"] for n in new})
        self.assertFalse(old_ids & {n["reservation_id"] for n in new})
        self.assertEqual(len({n["reference"] for n in new}), 6)


class TestStage2Roundtrip(Base2):
    """Stage 2 export of pairs and pair receipts into an independent stage 2 process."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dbase, cls.dproc, _ = new_stage2()
        cls.dst = Api(cls.dbase)

    @classmethod
    def tearDownClass(cls):
        cls.dproc.kill()

    def populate(self):
        t, tb = self.ada, self.bob
        self.body = {"restaurant_id": "r_anker", "table_ids": ["t_1", "t_2"], "starts_at_local": T, "party_size": 6}
        self.pair = self.api.call("POST", "/reservations", self.body, token=t, key="rt-pair")
        self.assertEqual(self.pair.status, 201)
        self.single = self.ok_book(t, f"{THU}T21:00", table="t_3", party=2, key="rt-single")
        self.moves = {"moves": [{"reference": self.single["reference"], "table_ids": ["t_2", "t_3"], "party_size": 7}]}
        self.mresp = self.api.call("POST", "/reservation-moves", self.moves, token=t, key="rt-moves")
        self.assertEqual(self.mresp.status, 201, self.mresp)
        c = self.ok_pair(tb, f"{THU}T18:00", ["t_3"], 2)
        self.cancelled = self.api.call("POST", f"/reservations/{c['reference']}/cancel", token=tb).json
        self.t, self.tb = t, tb

    def test_L089_L183_roundtrip_pairs_and_receipts(self):
        self.populate()
        exp = self.api.call("GET", "/_test/export").json
        d = self.dst
        self.assertEqual(d.call("POST", "/_test/import", exp).status, 204)
        self.assertEqual(d.call("GET", f"/reservations/{self.pair.json['reference']}", token=self.t).json, self.pair.json)
        self.assertEqual(d.call("GET", "/reservations", token=self.t).json, self.api.call("GET", "/reservations", token=self.t).json)
        self.assertEqual(d.call("GET", "/reservations", token=self.tb).json, self.api.call("GET", "/reservations", token=self.tb).json)
        r = d.call("POST", "/reservations", self.body, token=self.t, key="rt-pair")
        self.assertEqual((r.status, r.json), (200, self.pair.json))
        r = d.call("POST", "/reservation-moves", self.moves, token=self.t, key="rt-moves")
        self.assertEqual((r.status, r.json), (200, self.mresp.json))
        self.err(d.call("POST", "/reservations", dict(self.body, table_ids=["t_2", "t_1"]), token=self.t, key="rt-pair"), 409,
                 "idempotency_key_reuse")
        # configuration and occupancy came across (pair members busy, combos still declared)
        self.assertEqual(d.call("GET", "/restaurants/r_anker").json["combinable"], [["t_1", "t_2"], ["t_2", "t_3"]])
        s = d.call("GET", f"/availability?restaurant_id=r_anker&date={THU}&party_size=1").json["slots"]
        s = {x["starts_at_local"]: x for x in s}[T]
        self.assertNotIn("t_1", s["available_table_ids"])
        self.assertNotIn("t_2", s["available_table_ids"])
        self.err(d.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_ids": ["t_1"], "starts_at_local": T,
                                                  "party_size": 1}, token=self.tb, key="rt-x"), 409, "table_unavailable")
        # the cancelled booking holds nothing
        self.assertEqual(d.call("POST", "/reservations", {"restaurant_id": "r_anker", "table_ids": ["t_3"],
                                                          "starts_at_local": f"{THU}T18:00", "party_size": 2},
                                token=self.tb, key="rt-y").status, 201)
        # replace, not merge: second import restores exactly
        self.assertEqual(d.call("POST", "/_test/import", exp).status, 204)
        self.assertEqual(len(d.call("GET", "/reservations", token=self.tb).json["reservations"]), 1)

    def test_L088_export_snapshot_detached_with_pairs(self):
        self.populate()
        exp = self.api.call("GET", "/_test/export").json
        self.ok_pair(self.t, f"{FRI}T19:00", ["t_1", "t_2"], 6)        # a genuinely free slot after the export
        self.reset()
        self.assertEqual(self.api.call("POST", "/_test/import", exp).status, 204)
        self.assertEqual(len(self.api.call("GET", "/reservations", token=self.t).json["reservations"]), 2)


class TestStage2ImportValidation(Base2):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dbase, cls.dproc, _ = new_stage2()
        cls.dst = Api(cls.dbase)

    @classmethod
    def tearDownClass(cls):
        cls.dproc.kill()

    def setUp(self):
        super().setUp()
        self.pair = self.ok_pair(self.ada, T, ["t_1", "t_2"], 6)
        self.single = self.ok_book(self.ada, f"{THU}T21:00", table="t_3", party=2)
        self.api.call("POST", "/reservation-moves", {"moves": [{"reference": self.single["reference"], "table_ids": ["t_2", "t_3"],
                                                                "party_size": 8}]}, token=self.ada, key="iv-m")
        self.exp = self.api.call("GET", "/_test/export").json
        self.restore_dest()

    def restore_dest(self):
        self.dst.call("POST", "/_test/reset", fixture2(reservations=[seed_res(9, "u_ada", "r_anker", "t_2", f"{THU}T20:00", 2, "KEEPME1")]))
        self.keep = self.dst.call("POST", "/auth/login", {"email": "ada@example.com", "password": "correct horse"}).json["token"]
        self.before = self.dst.call("GET", "/_test/export").json

    def unchanged(self, what=""):
        self.assertEqual(self.dst.call("GET", "/_test/export").json, self.before, what)
        self.assertEqual(self.dst.call("GET", "/reservations/KEEPME1", token=self.keep).status, 200, what)

    def imp(self, state):
        return self.dst.call("POST", "/_test/import", {"track": "tablekeeper", "format_version": 1, "state": state})

    def test_L183_L189_envelope_failures_422_atomic(self):
        e = self.exp
        for c in ({}, dict(e, track="pocketful"), dict(e, track=None), dict(e, format_version=2), dict(e, format_version="1"),
                  dict(e, format_version=True), {"track": "tablekeeper", "format_version": 1}, dict(e, state=[]), dict(e, state=None)):
            self.err(self.dst.call("POST", "/_test/import", c), 422, "validation_failed")
            self.unchanged(str(c)[:60])
        for raw in ("{x", "", "[]"):
            self.err(self.dst.call("POST", "/_test/import", raw=raw), 400, "malformed_request")
        self.unchanged()

    def mutate_lists(self, match, replacements, expect=422):
        st0 = self.exp["state"]
        found = [p for p, n in walk(st0) if n == match and p]
        self.assertTrue(found, f"{match} not present in the opaque state")
        for p in found:
            for rep in replacements:
                st = copy.deepcopy(st0)
                parent = get_at(st, p[:-1])
                parent[p[-1]] = rep
                r = self.imp(st)
                self.assertLess(r.status, 500, (p, rep, r))
                self.err(r, expect, "validation_failed")
                self.unchanged(f"{p} {rep}")

    def test_L183_L096_reservation_member_sets_validated(self):
        pair = list(self.pair["table_ids"])
        st0 = self.exp["state"]
        # only mutate lists that sit inside reservation-like records, i.e. not the restaurant `combinable` config
        found = [p for p, n in walk(st0) if n == pair and p and not any(k == "combinable" for k in p)]
        self.assertTrue(found, "pair booking member list not found in opaque state")
        for p in found:
            for rep in (["t_1", "t_3"], ["t_1", "t_1"], [], ["t_1", "t_2", "t_3"], ["t_1", "zzz"], ["t_1", "t_9"], "t_1", [1, 2],
                        ["t_1", None]):
                st = copy.deepcopy(st0)
                get_at(st, p[:-1])[p[-1]] = rep
                r = self.imp(st)
                self.assertLess(r.status, 500)
                self.err(r, 422, "validation_failed")
                self.unchanged(f"{p} {rep}")

    def test_L182_L183_combinable_config_validated(self):
        comb = fixture2()["restaurants"][0]["combinable"]
        self.mutate_lists(comb, ([["t_1"]], [["t_1", "t_1"]], [["t_1", "t_2", "t_3"]], [["t_1", "zzz"]], [["t_1", "t_2"], ["t_2", "t_1"]],
                                 "x", [[1, 2]], [["t_1", "t_9"]]))

    def test_L183_L188_overlapping_confirmed_pair_clone_rejected(self):
        ref, rid = self.pair["reference"], self.pair["reservation_id"]
        st = copy.deepcopy(self.exp["state"])
        for path in record_nodes(st, ref):
            if not path:
                continue
            node = get_at(st, path)
            parent = get_at(st, path[:-1])
            clone = replace_value(replace_value(json.loads(json.dumps(node)), ref, "DUPREF77"), rid, "res_dup_77")
            if isinstance(parent, list):
                parent.append(clone)
                break
            if isinstance(parent, dict):
                parent["dup-key-77"] = clone
                break
        else:
            self.skipTest("reservation anchor not visible in opaque state")
        self.err(self.imp(st), 422, "validation_failed")
        self.unchanged()

    def test_L183_fuzz_leaves_never_5xx_and_rejections_atomic(self):
        paths = [p for p, n in walk(self.exp["state"]) if p]
        step = max(1, len(paths) // 200)
        rejected = 0
        for p in paths[::step]:
            for kind in ("delete", "wrongtype"):
                st = copy.deepcopy(self.exp["state"])
                parent = get_at(st, p[:-1])
                if kind == "delete":
                    if isinstance(parent, dict):
                        del parent[p[-1]]
                    else:
                        parent.pop(p[-1])
                else:
                    cur = parent[p[-1]]
                    parent[p[-1]] = {"x": 1} if isinstance(cur, (str, int, float, bool)) else "oops"
                r = self.imp(st)
                self.assertLess(r.status, 500, (p, kind, r))
                if r.status == 204:
                    self.restore_dest()                      # the source snapshot and the path list stay fixed
                else:
                    rejected += 1
                    self.err(r, 422, "validation_failed")
                    self.unchanged(f"{p} {kind}")
        self.assertGreater(rejected, 20)
